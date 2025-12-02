#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
#     "rich",
# ]
# ///

import re
import sys
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
SERVICES_FILE = PROJECT_ROOT / "project-context" / "SERVICES.md"
TIMEOUT_SECONDS = 5

console = Console()

class ServiceEndpoint(NamedTuple):
    name: str
    url: str

class Service(NamedTuple):
    name: str
    endpoints: List[ServiceEndpoint]
    health_check: Optional[str]
    status_marker: str

def parse_services_md(file_path: Path) -> List[Service]:
    """Parses SERVICES.md to extract service details."""
    if not file_path.exists():
        console.print(f"[bold red]Error:[/bold red] Could not find {file_path}")
        sys.exit(1)

    content = file_path.read_text()
    services = []
    
    # Split by level 3 headers (### Service Name)
    # But first, truncate content at "Recent Service Changes" or "Planned Service Changes"
    for stop_marker in ["## Recent Service Changes", "## Planned Service Changes", "## Service Status Summary"]:
        if stop_marker in content:
            content = content.split(stop_marker)[0]

    sections = re.split(r'^###\s+(.+)$', content, flags=re.MULTILINE)
    
    # Skip preamble (index 0)
    for i in range(1, len(sections), 2):
        service_name = sections[i].strip()
        service_body = sections[i+1]
        
        # Extract Status
        status_match = re.search(r'\*\*Status\*\*:\s*(.+)', service_body)
        status_marker = status_match.group(1).strip() if status_match else "?"

        # Extract Endpoints section
        endpoints = []
        health_check = None
        
        endpoints_section_match = re.search(r'\*\*Endpoints\*\*:(.+?)(?=\n\n|\n\*\*|\Z)', service_body, re.DOTALL)
        if endpoints_section_match:
            endpoints_text = endpoints_section_match.group(1)
            
            # Find all list items: - **Name**: URL
            for line in endpoints_text.strip().split('\n'):
                line = line.strip()
                if not line.startswith('-'):
                    continue
                
                # Parse: - **Name**: URL (maybe with extra text)
                match = re.match(r'-\s*\*\*(.+?)\*\*:\s*(\S+)', line)
                if match:
                    name = match.group(1).strip()
                    url = match.group(2).strip()
                    
                    if name.lower() == "health check" or name.lower() == "health":
                        health_check = url
                    else:
                        endpoints.append(ServiceEndpoint(name, url))

        # If explicit Health Check line exists outside endpoints
        if not health_check:
            for ep in endpoints:
                if ep.name.lower() in ["health", "health check"]:
                    health_check = ep.url
                    break
        
        # If still no health check, use the first HTTP endpoint
        if not health_check and endpoints:
            for ep in endpoints:
                if ep.url.startswith("http"):
                    health_check = ep.url
                    break

        services.append(Service(service_name, endpoints, health_check, status_marker))

    return services

def check_url(url: str) -> tuple[bool, str, str]:
    """Checks a URL and returns (success, status_code/msg, response_time)."""
    if not url.startswith("http"):
        return False, "Invalid URL", "0ms"
    
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS, verify=False)
        is_ok = 200 <= response.status_code < 300
        color = "green" if is_ok else "yellow" if response.status_code in [401, 403, 429] else "red"
        return is_ok, f"[{color}]{response.status_code}[/{color}]", f"{response.elapsed.total_seconds()*1000:.0f}ms"
    except requests.exceptions.Timeout:
        return False, "[red]Timeout[/red]", f">{TIMEOUT_SECONDS}s"
    except requests.exceptions.ConnectionError:
        return False, "[red]Conn Refused[/red]", "0ms"
    except Exception as e:
        return False, f"[red]Error[/red]", "0ms"

def check_k8s():
    """Checks Kubernetes cluster status."""
    console.print("[bold]Checking Kubernetes Cluster...[/bold]")
    try:
        subprocess.run(["kubectl", "cluster-info"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Get node status
        nodes = subprocess.check_output(["kubectl", "get", "nodes", "--no-headers"], text=True).strip().split('\n')
        ready_nodes = sum(1 for line in nodes if "Ready" in line)
        total_nodes = len(nodes)
        
        console.print(f"  ✅ Cluster Accessible: [green]{ready_nodes}/{total_nodes} Nodes Ready[/green]")
        return True
    except subprocess.CalledProcessError:
        console.print("  ❌ [red]Cluster Unreachable[/red]")
        return False
    except FileNotFoundError:
        console.print("  ⚠️  [yellow]kubectl not found[/yellow]")
        return False

def check_ping(ip: str, name: str):
    """Pings a node IP."""
    try:
        subprocess.run(["ping", "-c", "1", "-W", "2", ip], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    console.print(Panel.fit("[bold blue]Homelab Dynamic Health Check[/bold blue]", border_style="blue"))
    
    # 1. Infrastructure Checks
    console.print("\n[bold]Infrastructure Status[/bold]")
    
    # Current Tailscale IPs for the infrastructure
    nodes = [
        ("Service Node (asuna)", "100.75.194.1"),
        ("Compute Node (pesubuntu)", "100.86.122.109")
    ]
    
    infra_table = Table(show_header=False, box=None)
    infra_table.add_column("Node")
    infra_table.add_column("Status")
    
    for name, ip in nodes:
        if check_ping(ip, name):
            infra_table.add_row(f"{name} ({ip})", "[green]Online[/green]")
        else:
            infra_table.add_row(f"{name} ({ip})", "[red]Offline[/red]")
            
    console.print(infra_table)
    console.print()
    
    check_k8s()
    console.print()

    # 2. Service Checks
    console.print(f"[bold]Scanning Services from {SERVICES_FILE.name}...[/bold]")
    services = parse_services_md(SERVICES_FILE)
    
    table = Table(title="Service Health Status")
    table.add_column("Service", style="cyan")
    table.add_column("Doc Status", style="dim")
    table.add_column("Health Check Endpoint")
    table.add_column("Live Status")
    table.add_column("Latency", justify="right")

    success_count = 0
    total_checked = 0
    active_failures = 0

    for svc in services:
        if not svc.health_check:
            table.add_row(svc.name, svc.status_marker, "[dim]No endpoint[/dim]", "[yellow]Skipped[/yellow]", "")
            continue

        total_checked += 1
        is_ok, status_msg, latency = check_url(svc.health_check)
        
        if is_ok:
            success_count += 1
            live_status = f"✅ {status_msg}"
        else:
            live_status = f"❌ {status_msg}"
            # Only count as failure if service is marked as Active
            if "Active" in svc.status_marker:
                active_failures += 1
            
        # Truncate long URLs for display
        display_url = svc.health_check
        if len(display_url) > 40:
            display_url = display_url[:37] + "..."
            
        table.add_row(svc.name, svc.status_marker, display_url, live_status, latency)

    console.print(table)
    
    # Summary
    console.print()
    if total_checked > 0:
        health_percent = int((success_count / total_checked) * 100)
        color = "green" if health_percent >= 80 else "yellow" if health_percent >= 50 else "red"
        console.print(Panel(f"Overall Health: [{color}]{health_percent}%[/] ({success_count}/{total_checked} Services Healthy)", expand=False))
        
        if active_failures > 0:
            console.print(f"[bold red]FAILED:[/bold red] {active_failures} active services are down.")
            sys.exit(1)
                
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Check cancelled by user[/yellow]")
        sys.exit(130)