"""
Service Validation Framework

Validates actual service status against claims made in session documentation.
Supports multiple validation methods including HTTP checks, Kubernetes status,
and custom test script execution.
"""

import asyncio
import socket
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import httpx
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pydantic import BaseModel, Field

from loguru import logger
from rich.console import Console
from rich.table import Table

from .session_parser import ServiceClaim, ParsedSession


class ValidationStatus(Enum):
    """Status of service validation."""
    VALID = "✅ VALID"
    INVALID = "❌ INVALID"
    WARNING = "⚠️ WARNING"
    UNKNOWN = "❓ UNKNOWN"
    SKIPPED = "⏭️ SKIPPED"


class ValidationResult(BaseModel):
    """Result of validating a single service."""

    service_name: str = Field(description="Name of service being validated")
    claimed_status: str = Field(description="Status claimed in session")
    actual_status: ValidationStatus = Field(description="Actual validation status")
    claimed_url: Optional[str] = Field(None, description="URL claimed in session")
    actual_url: Optional[str] = Field(None, description="Actual working URL found")
    validation_method: str = Field(description="How validation was performed")
    details: List[str] = Field(default_factory=list, description="Validation details")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Warnings")
    timestamp: datetime = Field(default_factory=datetime.now, description="When validated")
    response_time_ms: Optional[float] = Field(None, description="HTTP response time in ms")


class ServiceValidator:
    """Validates services against their claimed status."""

    def __init__(self, project_root: Path, timeout: int = 10):
        self.project_root = Path(project_root)
        self.timeout = timeout
        self.console = Console()

        # Initialize Kubernetes client if available
        self.k8s_available = self._init_kubernetes()

        # Service node and compute node IPs
        self.service_node_ip = "100.81.76.55"
        self.compute_node_ip = "100.72.98.106"

        # Known service configurations
        self.service_configs = self._load_service_configs()

        # Health check scripts
        self.health_check_scripts = self._find_health_check_scripts()

    def _init_kubernetes(self) -> bool:
        """Initialize Kubernetes client."""
        try:
            config.load_kube_config()
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()

            # Test connection
            self.v1.get_api_resources()
            logger.info("Kubernetes client initialized successfully")
            return True
        except Exception as e:
            logger.warning(f"Kubernetes client not available: {e}")
            self.v1 = None
            self.apps_v1 = None
            return False

    def _load_service_configs(self) -> Dict[str, Dict]:
        """Load known service configurations."""
        return {
            # Service Node Services
            "n8n": {
                "expected_ports": [30678],
                "health_paths": ["/healthz"],
                "namespace": "homelab",
                "node": "service_node"
            },
            "prometheus": {
                "expected_ports": [30090],
                "health_paths": ["/-/healthy"],
                "namespace": "homelab",
                "node": "service_node"
            },
            "loki": {
                "expected_ports": [30314],
                "health_paths": ["/ready"],
                "namespace": "homelab",
                "node": "service_node"
            },
            "qdrant": {
                "expected_ports": [30633],
                "health_paths": ["/collections"],
                "namespace": "homelab",
                "node": "service_node"
            },
            "docker registry": {
                "expected_ports": [30500],
                "health_paths": ["/v2/"],
                "namespace": "homelab",
                "node": "service_node"
            },
            "homelab dashboard": {
                "expected_ports": [30800],
                "health_paths": ["/"],
                "namespace": "homelab",
                "node": "service_node"
            },
            "mem0": {
                "expected_ports": [30880],
                "health_paths": ["/docs"],
                "namespace": "homelab",
                "node": "service_node"
            },
            "lobechat": {
                "expected_ports": [30910],
                "health_paths": ["/"],
                "namespace": "homelab",
                "node": "service_node"
            },
            "whisper": {
                "expected_ports": [30900],
                "health_paths": ["/"],
                "namespace": "homelab",
                "node": "service_node"
            },
            "family assistant": {
                "expected_ports": [30080],
                "health_paths": ["/health", "/"],
                "namespace": "homelab",
                "node": "service_node"
            },

            # Compute Node Services
            "ollama": {
                "expected_ports": [11434, 30277],  # native and k8s
                "health_paths": ["/api/version"],
                "namespace": "ollama",  # for k8s deployment
                "node": "compute_node"
            },

            # Database Services (internal only)
            "postgresql": {
                "service_name": "postgres",
                "port": 5432,
                "namespace": "homelab",
                "node": "service_node",
                "internal_only": True
            },
            "redis": {
                "service_name": "redis",
                "port": 6379,
                "namespace": "homelab",
                "node": "service_node",
                "internal_only": True
            }
        }

    def _find_health_check_scripts(self) -> Dict[str, Path]:
        """Find available health check scripts."""
        scripts = {}
        scripts_dir = self.project_root / "scripts"

        if scripts_dir.exists():
            for script_path in scripts_dir.glob("health-check*.sh"):
                scripts[script_path.stem] = script_path
            for script_path in scripts_dir.glob("service-check*.sh"):
                scripts[script_path.stem] = script_path

        logger.info(f"Found health check scripts: {list(scripts.keys())}")
        return scripts

    async def validate_session(self, session: ParsedSession) -> List[ValidationResult]:
        """Validate all service claims from a session."""
        logger.info(f"Starting validation for session with {len(session.service_claims)} claims")

        # Combine explicit claims with endpoint services
        all_services = session.service_claims.copy()

        # Add services from endpoints that aren't already claimed
        for service_name, url in session.endpoints.items():
            if not any(s.name.lower() == service_name.lower() for s in all_services):
                all_services.append(ServiceClaim(
                    name=service_name,
                    status="✅",
                    description=f"Service should be accessible at {url}",
                    url=url
                ))

        # Validate all services concurrently
        tasks = [self.validate_service(claim) for claim in all_services]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and convert to results
        validation_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Validation error: {result}")
                continue
            if isinstance(result, ValidationResult):
                validation_results.append(result)

        return validation_results

    async def validate_service(self, claim: ServiceClaim) -> ValidationResult:
        """Validate a single service claim."""
        logger.info(f"Validating service: {claim.name}")

        result = ValidationResult(
            service_name=claim.name,
            claimed_status=claim.status,
            claimed_url=claim.url
        )

        try:
            # Determine validation strategy based on service type
            service_key = claim.name.lower()
            config = self._get_service_config(service_key)

            if config and config.get("internal_only"):
                # Internal services (databases) - validate via Kubernetes
                result = await self._validate_internal_service(claim, config, result)
            elif self.k8s_available and config:
                # Kubernetes-deployed services - validate via multiple methods
                result = await self._validate_kubernetes_service(claim, config, result)
            else:
                # External services - validate via HTTP/network checks
                result = await self._validate_external_service(claim, result)

            # Run health check scripts if available
            if "health-check-all" in self.health_check_scripts:
                script_result = await self._run_health_check_script(claim)
                if script_result:
                    result.details.append(f"Health check script: {script_result}")

        except Exception as e:
            logger.error(f"Error validating {claim.name}: {e}")
            result.actual_status = ValidationStatus.UNKNOWN
            result.errors.append(str(e))

        return result

    async def _validate_external_service(self, claim: ServiceClaim, result: ValidationResult) -> ValidationResult:
        """Validate external service via HTTP/network checks."""
        urls_to_test = []

        # Use claimed URL if available
        if claim.url:
            urls_to_test.append(claim.url)

        # Add known URLs based on service configuration
        config = self._get_service_config(claim.name.lower())
        if config:
            base_ip = self.service_node_ip if config["node"] == "service_node" else self.compute_node_ip
            for port in config["expected_ports"]:
                urls_to_test.append(f"http://{base_ip}:{port}")

        # Test URLs
        working_url = None
        for url in urls_to_test:
            validation_result = await self._test_http_endpoint(url)
            if validation_result[0]:  # Success
                working_url = url
                result.actual_status = ValidationStatus.VALID
                result.response_time_ms = validation_result[1]
                break
            elif validation_result[0] is False:  # Failed but reachable
                result.warnings.append(f"URL {url} responded but with issues")

        # Set actual URL if found
        if working_url:
            result.actual_url = working_url
            result.validation_method = "HTTP endpoint test"
        else:
            result.actual_status = ValidationStatus.INVALID
            result.validation_method = "HTTP endpoint test (all failed)"
            result.errors.append(f"No working URLs found among: {urls_to_test}")

        return result

    async def _validate_kubernetes_service(self, claim: ServiceClaim, config: Dict, result: ValidationResult) -> ValidationResult:
        """Validate Kubernetes-deployed service."""
        namespace = config.get("namespace", "homelab")
        service_name = config.get("service_name", claim.name.lower().replace(" ", "-"))

        # Check if service exists in Kubernetes
        try:
            service = self.v1.read_namespaced_service(name=service_name, namespace=namespace)
            result.details.append(f"K8s service found: {service_name} in {namespace}")
        except ApiException as e:
            if e.status == 404:
                result.errors.append(f"K8s service not found: {service_name} in {namespace}")
                result.actual_status = ValidationStatus.INVALID
                return result
            else:
                raise

        # Check pods
        pods = self.v1.list_namespaced_pod(namespace=namespace, label_selector=f"app={service_name}")
        if not pods.items:
            result.errors.append(f"No pods found for service: {service_name}")
            result.actual_status = ValidationStatus.INVALID
            return result

        # Check pod status
        running_pods = [pod for pod in pods.items if pod.status.phase == "Running"]
        if not running_pods:
            result.errors.append(f"No running pods for service: {service_name}")
            result.actual_status = ValidationStatus.INVALID
            return result

        result.details.append(f"Found {len(running_pods)}/{len(pods.items)} running pods")

        # Check service endpoints
        try:
            endpoints = self.v1.read_namespaced_endpoints(name=service_name, namespace=namespace)
            if not endpoints.subsets:
                result.warnings.append(f"No endpoints ready for service: {service_name}")
            else:
                ready_addresses = sum(len(subset.addresses or []) for subset in endpoints.subsets)
                result.details.append(f"Service has {ready_addresses} ready endpoints")
        except ApiException as e:
            result.warnings.append(f"Could not read endpoints: {e}")

        # Test HTTP endpoint
        result = await self._validate_external_service(claim, result)

        # Update validation method
        if result.validation_method == "HTTP endpoint test":
            result.validation_method = "Kubernetes + HTTP validation"

        return result

    async def _validate_internal_service(self, claim: ServiceClaim, config: Dict, result: ValidationResult) -> ValidationResult:
        """Validate internal service (database, etc.) via Kubernetes."""
        namespace = config.get("namespace", "homelab")
        service_name = config.get("service_name", claim.name.lower().replace(" ", "-"))

        # Check if service exists
        try:
            service = self.v1.read_namespaced_service(name=service_name, namespace=namespace)
            result.details.append(f"Internal service found: {service_name}")
        except ApiException as e:
            if e.status == 404:
                result.errors.append(f"Internal service not found: {service_name}")
                result.actual_status = ValidationStatus.INVALID
                return result
            else:
                raise

        # Check if pods are running
        pods = self.v1.list_namespaced_pod(namespace=namespace, label_selector=f"app={service_name}")
        if not pods.items:
            result.errors.append(f"No pods found for internal service: {service_name}")
            result.actual_status = ValidationStatus.INVALID
            return result

        running_pods = [pod for pod in pods.items if pod.status.phase == "Running"]
        if running_pods:
            result.actual_status = ValidationStatus.VALID
            result.validation_method = "Kubernetes internal service check"
            result.details.append(f"Internal service running: {len(running_pods)} pods")
        else:
            result.actual_status = ValidationStatus.INVALID
            result.validation_method = "Kubernetes internal service check"
            result.errors.append("No running pods for internal service")

        return result

    async def _test_http_endpoint(self, url: str) -> Tuple[Optional[bool], Optional[float]]:
        """Test an HTTP endpoint and return (success, response_time_ms)."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                start_time = datetime.now()
                response = await client.get(url)
                response_time = (datetime.now() - start_time).total_seconds() * 1000

                # Consider 2xx and 3xx as success (3xx for redirects)
                if 200 <= response.status_code < 400:
                    return True, response_time
                else:
                    return False, response_time

        except httpx.TimeoutException:
            logger.warning(f"Timeout testing {url}")
            return None, None
        except httpx.ConnectError:
            logger.warning(f"Connection error testing {url}")
            return None, None
        except Exception as e:
            logger.warning(f"Error testing {url}: {e}")
            return None, None

    async def _run_health_check_script(self, claim: ServiceClaim) -> Optional[str]:
        """Run a health check script and return its output."""
        if "health-check-all" not in self.health_check_scripts:
            return None

        script_path = self.health_check_scripts["health-check-all"]
        try:
            result = await asyncio.create_subprocess_exec(
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                # Look for service in output
                output = stdout.decode()
                if claim.name.lower() in output.lower():
                    return "Service found in health check output"
            else:
                logger.warning(f"Health check script failed: {stderr.decode()}")

        except Exception as e:
            logger.warning(f"Error running health check script: {e}")

        return None

    def _get_service_config(self, service_name: str) -> Optional[Dict]:
        """Get configuration for a service by name."""
        # Direct match
        if service_name in self.service_configs:
            return self.service_configs[service_name]

        # Partial match
        for key, config in self.service_configs.items():
            if key in service_name or service_name in key:
                return config

        return None

    def print_validation_results(self, results: List[ValidationResult]) -> None:
        """Print validation results in a formatted table."""
        table = Table(title="Service Validation Results")
        table.add_column("Service", style="cyan")
        table.add_column("Claimed", style="yellow")
        table.add_column("Actual", style="green")
        table.add_column("Method", style="blue")
        table.add_column("Details", style="white")

        valid_count = 0
        invalid_count = 0
        warning_count = 0

        for result in results:
            status_style = {
                ValidationStatus.VALID: "green",
                ValidationStatus.INVALID: "red",
                ValidationStatus.WARNING: "yellow",
                ValidationStatus.UNKNOWN: "dim",
                ValidationStatus.SKIPPED: "dim"
            }.get(result.actual_status, "white")

            details_text = " | ".join(result.details[:2])  # Limit details
            if len(result.details) > 2:
                details_text += "..."

            table.add_row(
                result.service_name,
                result.claimed_status,
                f"[{status_style}]{result.actual_status.value}[/{status_style}]",
                result.validation_method,
                details_text
            )

            # Count status types
            if result.actual_status == ValidationStatus.VALID:
                valid_count += 1
            elif result.actual_status == ValidationStatus.INVALID:
                invalid_count += 1
            elif result.actual_status == ValidationStatus.WARNING:
                warning_count += 1

        self.console.print(table)

        # Print summary
        total = len(results)
        if total > 0:
            valid_percent = (valid_count / total) * 100
            print(f"\n📊 Summary: {valid_count}/{total} valid ({valid_percent:.1f}%)")

            if invalid_count > 0:
                print(f"❌ Invalid services: {invalid_count}")
            if warning_count > 0:
                print(f"⚠️ Warnings: {warning_count}")

    def generate_validation_report(self, results: List[ValidationResult]) -> str:
        """Generate a detailed validation report."""
        report_lines = [
            "# 🔍 Session Validation Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
        ]

        total = len(results)
        if total > 0:
            valid_count = sum(1 for r in results if r.actual_status == ValidationStatus.VALID)
            invalid_count = sum(1 for r in results if r.actual_status == ValidationStatus.INVALID)
            warning_count = sum(1 for r in results if r.actual_status == ValidationStatus.WARNING)

            report_lines.extend([
                f"- Total services validated: {total}",
                f"- ✅ Valid: {valid_count} ({valid_count/total*100:.1f}%)",
                f"- ❌ Invalid: {invalid_count} ({invalid_count/total*100:.1f}%)",
                f"- ⚠️ Warnings: {warning_count} ({warning_count/total*100:.1f}%)",
                ""
            ])

        # Detailed results
        report_lines.append("## Detailed Results")
        report_lines.append("")

        for result in results:
            report_lines.extend([
                f"### {result.service_name}",
                f"- **Claimed Status**: {result.claimed_status}",
                f"- **Actual Status**: {result.actual_status.value}",
                f"- **Validation Method**: {result.validation_method}",
            ])

            if result.claimed_url:
                report_lines.append(f"- **Claimed URL**: {result.claimed_url}")
            if result.actual_url:
                report_lines.append(f"- **Actual URL**: {result.actual_url}")
            if result.response_time_ms:
                report_lines.append(f"- **Response Time**: {result.response_time_ms:.0f}ms")

            if result.details:
                report_lines.append("- **Details**:")
                for detail in result.details:
                    report_lines.append(f"  - {detail}")

            if result.warnings:
                report_lines.append("- **Warnings**:")
                for warning in result.warnings:
                    report_lines.append(f"  - {warning}")

            if result.errors:
                report_lines.append("- **Errors**:")
                for error in result.errors:
                    report_lines.append(f"  - {error}")

            report_lines.append("")

        return "\n".join(report_lines)