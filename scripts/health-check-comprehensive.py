#!/usr/bin/env python3
"""
Comprehensive Homelab Health Check
Checks infrastructure, Kubernetes, services, TLS certificates, and pod status
"""

import re
import sys
import subprocess
import socket
import ssl
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass

try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
except ImportError:
    print("Error: rich library not found. Install with: pip install rich")
    sys.exit(1)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
SERVICES_FILE = PROJECT_ROOT / "project-context" / "SERVICES.md"
TIMEOUT_SECONDS = 5

console = Console()

@dataclass
class ServiceCheck:
    name: str
    external_url: Optional[str]
    internal_url: Optional[str]
    namespace: str
    pod_selector: str
    expected_status: str

# Define services to check (with correct namespaces and selectors from actual pods)
SERVICES = [
    ServiceCheck("N8n", "https://n8n.fa.pesulabs.net", None, "homelab", "app=n8n", "Active"),
    ServiceCheck("Family App", "https://app.fa.pesulabs.net", None, "fa-platform", "app=family-assistant-app", "Active"),
    ServiceCheck("Family Admin", "https://admin.fa.pesulabs.net", None, "fa-platform", "app=family-assistant-admin", "Active"),
    ServiceCheck("Family API", "https://api.fa.pesulabs.net", None, "fa-platform", "app.kubernetes.io/name=family-assistant-api", "Active"),
    ServiceCheck("Authentik", "https://auth.pesulabs.net", None, "authentik", "app=authentik-server", "Active"),
    ServiceCheck("Prometheus", None, None, "homelab", "app=prometheus", "Active"),
    ServiceCheck("Loki", None, None, "homelab", "app=loki", "Active"),
    ServiceCheck("Mem0", None, None, "homelab", "app=mem0", "Active"),
    ServiceCheck("PostgreSQL", None, None, "homelab", "app=postgres", "Active"),
    ServiceCheck("Redis", None, None, "homelab", "app=redis", "Active"),
    ServiceCheck("Qdrant", None, None, "homelab", "app=qdrant", "Active"),
]

def check_infrastructure():
    """Check node connectivity and Kubernetes cluster status."""
    console.print("\n[bold cyan]═══ Infrastructure Status ═══[/bold cyan]\n")

    nodes = [
        ("Service Node (asuna)", "100.75.194.1"),
        ("Compute Node (pesubuntu)", "100.86.122.109")
    ]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Node", style="cyan")
    table.add_column("IP Address", style="dim")
    table.add_column("Status")

    all_online = True
    for name, ip in nodes:
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", ip],
                capture_output=True,
                timeout=3
            )
            if result.returncode == 0:
                table.add_row(name, ip, "[green]✅ Online[/green]")
            else:
                table.add_row(name, ip, "[red]❌ Offline[/red]")
                all_online = False
        except:
            table.add_row(name, ip, "[red]❌ Timeout[/red]")
            all_online = False

    console.print(table)

    # Check Kubernetes
    console.print("\n[bold]Kubernetes Cluster:[/bold]")
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode == 0:
            nodes_result = subprocess.run(
                ["kubectl", "get", "nodes", "--no-headers"],
                capture_output=True,
                text=True,
                timeout=5
            )
            nodes_lines = nodes_result.stdout.strip().split('\n')
            ready_count = sum(1 for line in nodes_lines if "Ready" in line and "NotReady" not in line)
            total_count = len(nodes_lines)

            console.print(f"  ✅ Cluster accessible: [green]{ready_count}/{total_count} nodes ready[/green]")
            return all_online and ready_count == total_count
        else:
            console.print("  ❌ [red]Cluster unreachable[/red]")
            return False
    except Exception as e:
        console.print(f"  ❌ [red]Error checking cluster: {e}[/red]")
        return False

def check_tls_cert(hostname: str) -> Dict[str, any]:
    """Check TLS certificate for a hostname."""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

                # Parse expiry date
                not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_until_expiry = (not_after - datetime.now()).days

                # Get issuer
                issuer = dict(x[0] for x in cert['issuer'])
                issuer_org = issuer.get('organizationName', 'Unknown')

                return {
                    'valid': True,
                    'issuer': issuer_org,
                    'days_until_expiry': days_until_expiry,
                    'expired': days_until_expiry < 0
                }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e)
        }

def check_http_endpoint(url: str, timeout: int = TIMEOUT_SECONDS) -> Dict[str, any]:
    """Check HTTP/HTTPS endpoint."""
    try:
        response = requests.get(url, timeout=timeout, verify=False, allow_redirects=True)
        return {
            'success': 200 <= response.status_code < 300,
            'status_code': response.status_code,
            'latency_ms': int(response.elapsed.total_seconds() * 1000)
        }
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Timeout', 'latency_ms': timeout * 1000}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Connection refused', 'latency_ms': 0}
    except Exception as e:
        return {'success': False, 'error': str(e), 'latency_ms': 0}

def check_pod_status(namespace: str, selector: str) -> Dict[str, any]:
    """Check Kubernetes pod status."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", namespace, "-l", selector, "--no-headers"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return {'success': False, 'error': 'kubectl failed'}

        lines = result.stdout.strip().split('\n')
        if not lines or lines[0] == '':
            return {'success': False, 'error': 'No pods found', 'pods': []}

        pods = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                pod_name = parts[0]
                ready = parts[1]
                status = parts[2]
                restarts = parts[3] if len(parts) > 3 else '0'

                pods.append({
                    'name': pod_name,
                    'ready': ready,
                    'status': status,
                    'restarts': restarts,
                    'healthy': status == 'Running' and '/' in ready and ready.split('/')[0] == ready.split('/')[1]
                })

        all_healthy = all(p['healthy'] for p in pods)
        return {'success': all_healthy, 'pods': pods}

    except Exception as e:
        return {'success': False, 'error': str(e), 'pods': []}

def check_services():
    """Check all services comprehensively."""
    console.print("\n[bold cyan]═══ Service Health Checks ═══[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Service", style="cyan", width=15)
    table.add_column("External", justify="center", width=10)
    table.add_column("Internal", justify="center", width=10)
    table.add_column("Pods", justify="center", width=10)
    table.add_column("TLS Cert", justify="center", width=15)
    table.add_column("Details", width=30)

    results = []
    healthy_count = 0
    total_count = 0

    for service in SERVICES:
        if service.expected_status != "Active":
            continue

        total_count += 1

        # Check external URL
        external_status = "N/A"
        external_ok = None
        tls_status = "N/A"
        details = []

        if service.external_url:
            ext_result = check_http_endpoint(service.external_url)
            if ext_result['success']:
                external_status = f"[green]✅ {ext_result['status_code']}[/green]"
                external_ok = True
            else:
                error = ext_result.get('error', ext_result.get('status_code', 'Failed'))
                external_status = f"[red]❌ {error}[/red]"
                external_ok = False

            details.append(f"{ext_result.get('latency_ms', 0)}ms")

            # Check TLS cert
            if service.external_url.startswith('https'):
                hostname = service.external_url.split('://')[1].split('/')[0]
                cert_info = check_tls_cert(hostname)
                if cert_info['valid']:
                    days = cert_info['days_until_expiry']
                    if days < 0:
                        tls_status = f"[red]Expired[/red]"
                    elif days < 7:
                        tls_status = f"[yellow]{days}d left[/yellow]"
                    else:
                        issuer_short = cert_info['issuer'].replace("Let's Encrypt", "LE")
                        tls_status = f"[green]✅ {issuer_short}[/green]"
                else:
                    tls_status = f"[red]Invalid[/red]"

        # Internal check removed - would need to run from within cluster
        internal_status = "N/A"
        internal_ok = None

        # Check pod status
        pod_result = check_pod_status(service.namespace, service.pod_selector)
        if pod_result['success']:
            pod_count = len(pod_result['pods'])
            pod_status = f"[green]✅ {pod_count} ready[/green]"
            pod_ok = True
        else:
            if pod_result.get('pods'):
                unhealthy = [p for p in pod_result['pods'] if not p['healthy']]
                pod_status = f"[red]❌ {len(unhealthy)} issues[/red]"
                pod_details = ", ".join([f"{p['name']}: {p['status']}" for p in unhealthy[:2]])
                details.append(pod_details)
            else:
                pod_status = f"[red]❌ No pods[/red]"
            pod_ok = False

        # Determine overall health
        checks = [pod_ok]
        if external_ok is not None:
            checks.append(external_ok)
        if internal_ok is not None:
            checks.append(internal_ok)

        is_healthy = all(checks) if checks else False
        if is_healthy:
            healthy_count += 1

        table.add_row(
            service.name,
            external_status,
            internal_status,
            pod_status,
            tls_status,
            " | ".join(details) if details else "-"
        )

        results.append({
            'name': service.name,
            'healthy': is_healthy,
            'details': pod_result.get('pods', [])
        })

    console.print(table)

    # Summary
    console.print()
    health_percent = int((healthy_count / total_count) * 100) if total_count > 0 else 0
    color = "green" if health_percent >= 80 else "yellow" if health_percent >= 50 else "red"

    console.print(Panel(
        f"[{color}]Overall Health: {health_percent}%[/{color}] ({healthy_count}/{total_count} services healthy)",
        title="Summary",
        border_style=color
    ))

    return healthy_count == total_count, results

def main():
    console.print(Panel.fit(
        "[bold blue]Homelab Comprehensive Health Check[/bold blue]\n"
        "[dim]Checking infrastructure, Kubernetes, services, TLS certs, and pods[/dim]",
        border_style="blue"
    ))

    # Infrastructure checks
    infra_ok = check_infrastructure()

    # Service checks
    services_ok, results = check_services()

    # Print failed services details
    failed = [r for r in results if not r['healthy']]
    if failed:
        console.print("\n[bold red]═══ Failed Services Details ═══[/bold red]\n")
        for svc in failed:
            console.print(f"[bold red]❌ {svc['name']}[/bold red]")
            for pod in svc['details']:
                if not pod.get('healthy', False):
                    console.print(f"  • {pod['name']}: {pod['status']} (ready: {pod['ready']}, restarts: {pod['restarts']})")

    console.print()

    if not infra_ok or not services_ok:
        console.print("[bold red]HEALTH CHECK FAILED[/bold red]")
        sys.exit(1)
    else:
        console.print("[bold green]✅ ALL SYSTEMS OPERATIONAL[/bold green]")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Health check cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)
