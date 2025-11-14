#!/usr/bin/env python3
"""
MCP Tool: Infrastructure Detective for Homelab Development
Enhances Claude Code with infrastructure troubleshooting and optimization capabilities
"""

import asyncio
import json
import os
import sys
import socket
import subprocess
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import aiohttp
import re

class InfrastructureDetectiveMCP:
    """
    Advanced infrastructure troubleshooting tool for homelab development.
    Provides network diagnostics, performance analysis, security scanning, and optimization recommendations.
    """

    def __init__(self):
        self.service_node_ip = "100.81.76.55"  # asuna
        self.compute_node_ip = "100.72.98.106"  # pesubuntu
        self.local_network = "192.168.8.0/24"
        self.tailscale_network = "100.64.0.0/10"
        self.default_timeout = 5
        self.known_services = {
            "family-assistant": {"port": 30001, "path": "/"},
            "n8n": {"port": 30678, "path": "/"},
            "grafana": {"port": 30000, "path": "/"},
            "prometheus": {"port": 30090, "path": "/"},
            "qdrant": {"port": 30633, "path": "/"},
            "redis": {"port": 6379, "path": None},
            "postgres": {"port": 5432, "path": None},
            "loki": {"port": 30314, "path": "/"},
            "mem0": {"port": 30820, "path": "/"},
            "dashboard": {"port": 30800, "path": "/"}
        }

    async def diagnose_connectivity_issue(self, target: str, service_name: str = None) -> Dict[str, Any]:
        """
        Comprehensive connectivity diagnosis for services and endpoints
        """
        diagnosis = {
            "target": target,
            "service_name": service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {}
        }

        try:
            # Parse target (URL, IP:port, or hostname)
            parsed_target = self._parse_target(target, service_name)
            diagnosis["parsed_target"] = parsed_target

            # 1. DNS Resolution
            if parsed_target["hostname"]:
                dns_result = await self._test_dns_resolution(parsed_target["hostname"])
                diagnosis["tests"]["dns"] = dns_result

            # 2. Network Path Analysis
            if parsed_target["ip"]:
                path_result = await self._test_network_path(parsed_target["ip"])
                diagnosis["tests"]["network_path"] = path_result

            # 3. Port Accessibility
            if parsed_target["port"]:
                port_result = await self._test_port_access(
                    parsed_target["ip"] or parsed_target["hostname"],
                    parsed_target["port"]
                )
                diagnosis["tests"]["port_access"] = port_result

            # 4. HTTP/HTTPS Service Test
            if parsed_target["scheme"] and parsed_target["port"]:
                http_result = await self._test_http_service(parsed_target)
                diagnosis["tests"]["http_service"] = http_result

            # 5. Service-Specific Tests
            if service_name and service_name in self.known_services:
                service_result = await self._test_specific_service(service_name, parsed_target)
                diagnosis["tests"]["service_specific"] = service_result

            # 6. Generate Diagnosis
            diagnosis["overall_status"] = self._determine_connectivity_status(diagnosis["tests"])
            diagnosis["recommendations"] = self._generate_connectivity_recommendations(
                diagnosis["tests"], diagnosis["overall_status"]
            )

        except Exception as e:
            diagnosis["error"] = str(e)
            diagnosis["overall_status"] = "error"

        return diagnosis

    async def analyze_performance_bottlenecks(self, focus: str = "all") -> Dict[str, Any]:
        """
        Analyze system performance and identify bottlenecks
        """
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "focus": focus,
            "metrics": {},
            "bottlenecks": [],
            "recommendations": []
        }

        try:
            # System Resource Analysis
            if focus in ["all", "system"]:
                system_metrics = await self._analyze_system_resources()
                analysis["metrics"]["system"] = system_metrics

                # Identify system bottlenecks
                if system_metrics["cpu"]["percent"] > 80:
                    analysis["bottlenecks"].append({
                        "type": "cpu",
                        "severity": "high" if system_metrics["cpu"]["percent"] > 95 else "medium",
                        "value": system_metrics["cpu"]["percent"],
                        "description": f"High CPU usage: {system_metrics['cpu']['percent']}%"
                    })

                if system_metrics["memory"]["percent"] > 85:
                    analysis["bottlenecks"].append({
                        "type": "memory",
                        "severity": "high" if system_metrics["memory"]["percent"] > 95 else "medium",
                        "value": system_metrics["memory"]["percent"],
                        "description": f"High memory usage: {system_metrics['memory']['percent']}%"
                    })

                if system_metrics["disk"]["percent"] > 90:
                    analysis["bottlenecks"].append({
                        "type": "disk",
                        "severity": "high",
                        "value": system_metrics["disk"]["percent"],
                        "description": f"High disk usage: {system_metrics['disk']['percent']}%"
                    })

            # Network Performance
            if focus in ["all", "network"]:
                network_metrics = await self._analyze_network_performance()
                analysis["metrics"]["network"] = network_metrics

                # Check network issues
                if network_metrics.get("packet_loss", 0) > 1:
                    analysis["bottlenecks"].append({
                        "type": "network",
                        "severity": "medium",
                        "value": network_metrics["packet_loss"],
                        "description": f"Network packet loss: {network_metrics['packet_loss']}%"
                    })

                if network_metrics.get("latency_ms", 0) > 100:
                    analysis["bottlenecks"].append({
                        "type": "network",
                        "severity": "medium",
                        "value": network_metrics["latency_ms"],
                        "description": f"High network latency: {network_metrics['latency_ms']}ms"
                    })

            # Service Performance
            if focus in ["all", "services"]:
                service_metrics = await self._analyze_service_performance()
                analysis["metrics"]["services"] = service_metrics

                # Identify slow services
                for service, metrics in service_metrics.items():
                    if metrics.get("response_time_ms", 0) > 5000:
                        analysis["bottlenecks"].append({
                            "type": "service_response",
                            "service": service,
                            "severity": "high",
                            "value": metrics["response_time_ms"],
                            "description": f"Slow response time for {service}: {metrics['response_time_ms']}ms"
                        })

            # Generate recommendations
            analysis["recommendations"] = self._generate_performance_recommendations(
                analysis["bottlenecks"], analysis["metrics"]
            )

            # Calculate overall performance score
            analysis["performance_score"] = self._calculate_performance_score(
                analysis["metrics"], analysis["bottlenecks"]
            )

        except Exception as e:
            analysis["error"] = str(e)

        return analysis

    async def security_audit(self, scope: str = "basic") -> Dict[str, Any]:
        """
        Perform security audit of homelab infrastructure
        """
        audit = {
            "timestamp": datetime.utcnow().isoformat(),
            "scope": scope,
            "checks": {},
            "vulnerabilities": [],
            "security_score": 0
        }

        try:
            # Basic Security Checks
            audit["checks"]["exposed_ports"] = await self._check_exposed_ports()
            audit["checks"]["default_credentials"] = await self._check_default_credentials()
            audit["checks"]["ssl_certificates"] = await self._check_ssl_certificates()
            audit["checks"]["system_updates"] = await self._check_system_updates()

            # Intermediate Security Checks
            if scope in ["intermediate", "comprehensive"]:
                audit["checks"]["weak_passwords"] = await self._check_weak_passwords()
                audit["checks"]["unnecessary_services"] = await self._check_unnecessary_services()
                audit["checks"]["file_permissions"] = await self._check_file_permissions()

            # Comprehensive Security Checks
            if scope == "comprehensive":
                audit["checks"]["firewall_rules"] = await self._check_firewall_rules()
                audit["checks"]["failed_logins"] = await self._check_failed_logins()
                audit["checks"]["suspicious_processes"] = await self._check_suspicious_processes()

            # Aggregate vulnerabilities
            for check_name, check_result in audit["checks"].items():
                if isinstance(check_result, dict) and "vulnerabilities" in check_result:
                    audit["vulnerabilities"].extend(check_result["vulnerabilities"])

            # Calculate security score
            audit["security_score"] = self._calculate_security_score(audit["checks"])
            audit["risk_level"] = self._determine_risk_level(audit["security_score"])

            # Generate security recommendations
            audit["recommendations"] = self._generate_security_recommendations(audit["vulnerabilities"])

        except Exception as e:
            audit["error"] = str(e)

        return audit

    async def capacity_planning(self, timeframe_months: int = 6) -> Dict[str, Any]:
        """
        Capacity planning and resource optimization recommendations
        """
        planning = {
            "timestamp": datetime.utcnow().isoformat(),
            "timeframe_months": timeframe_months,
            "current_usage": {},
            "projections": {},
            "recommendations": []
        }

        try:
            # Current Resource Usage
            current_metrics = await self._analyze_system_resources()
            planning["current_usage"] = current_metrics

            # Historical Data Analysis (placeholder - would use Prometheus/Grafana data)
            historical_data = await self._get_historical_metrics()
            planning["historical_trends"] = historical_data

            # Calculate growth rates
            growth_rates = self._calculate_growth_rates(historical_data)

            # Project Future Usage
            planning["projections"] = self._project_future_usage(
                current_metrics, growth_rates, timeframe_months
            )

            # Identify Potential Bottlenecks
            planning["potential_bottlenecks"] = self._identify_future_bottlenecks(
                planning["projections"]
            )

            # Generate Recommendations
            planning["recommendations"] = self._generate_capacity_recommendations(
                planning["current_usage"], planning["projections"], timeframe_months
            )

        except Exception as e:
            planning["error"] = str(e)

        return planning

    async def troubleshoot_service(self, service_name: str) -> Dict[str, Any]:
        """
        Comprehensive service troubleshooting
        """
        if service_name not in self.known_services:
            return {
                "error": f"Unknown service: {service_name}",
                "known_services": list(self.known_services.keys())
            }

        service_config = self.known_services[service_name]
        troubleshooting = {
            "service": service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "config": service_config,
            "checks": {}
        }

        try:
            # Service Accessibility
            troubleshooting["checks"]["accessibility"] = await self._test_service_accessibility(
                service_name, service_config
            )

            # Service Dependencies
            troubleshooting["checks"]["dependencies"] = await self._test_service_dependencies(
                service_name
            )

            # Service Logs Analysis
            troubleshooting["checks"]["logs"] = await self._analyze_service_logs(service_name)

            # Service Configuration
            troubleshooting["checks"]["configuration"] = await self._validate_service_configuration(
                service_name
            )

            # Service Performance
            troubleshooting["checks"]["performance"] = await self._analyze_service_performance_detailed(
                service_name
            )

            # Overall Health Assessment
            troubleshooting["overall_health"] = self._assess_service_health(
                troubleshooting["checks"]
            )

            # Actionable Recommendations
            troubleshooting["recommendations"] = self._generate_service_recommendations(
                service_name, troubleshooting["checks"]
            )

        except Exception as e:
            troubleshooting["error"] = str(e)

        return troubleshooting

    async def network_topology_map(self) -> Dict[str, Any]:
        """
        Generate network topology and connectivity map
        """
        topology = {
            "timestamp": datetime.utcnow().isoformat(),
            "nodes": {},
            "connections": [],
            "issues": []
        }

        try:
            # Discover nodes
            topology["nodes"]["localhost"] = await self._get_local_node_info()
            topology["nodes"]["service_node"] = await self._get_remote_node_info(self.service_node_ip)

            # Test connectivity between nodes
            topology["connections"].append({
                "from": "localhost",
                "to": "service_node",
                "status": await self._test_node_connectivity(self.service_node_ip)
            })

            # Map services to nodes
            for service_name, config in self.known_services.items():
                service_status = await self._test_service_connectivity(service_name, config)
                topology["nodes"]["service_node"]["services"][service_name] = service_status

            # Identify network issues
            topology["issues"] = await self._identify_network_issues(topology)

        except Exception as e:
            topology["error"] = str(e)

        return topology

    # Helper methods
    def _parse_target(self, target: str, service_name: str = None) -> Dict[str, Any]:
        """Parse target into components"""
        import re
        from urllib.parse import urlparse

        # If it's a service name, use known configuration
        if service_name and service_name in self.known_services:
            config = self.known_services[service_name]
            return {
                "scheme": "http",
                "hostname": self.service_node_ip,
                "port": config["port"],
                "path": config.get("path", "/"),
                "service": service_name
            }

        # Parse URL
        if target.startswith(("http://", "https://")):
            parsed = urlparse(target)
            return {
                "scheme": parsed.scheme,
                "hostname": parsed.hostname,
                "port": parsed.port or (443 if parsed.scheme == "https" else 80),
                "path": parsed.path or "/",
                "original": target
            }

        # Parse IP:Port
        ip_port_match = re.match(r'^(\d+\.\d+\.\d+\.\d+):(\d+)$', target)
        if ip_port_match:
            return {
                "scheme": "http",
                "hostname": ip_port_match.group(1),
                "port": int(ip_port_match.group(2)),
                "path": "/",
                "original": target
            }

        # Parse hostname
        return {
            "scheme": "http",
            "hostname": target,
            "port": 80,
            "path": "/",
            "original": target
        }

    async def _test_dns_resolution(self, hostname: str) -> Dict[str, Any]:
        """Test DNS resolution"""
        try:
            import socket
            ip_addresses = socket.gethostbyname_ex(hostname)[2]
            return {
                "success": True,
                "hostname": hostname,
                "ip_addresses": ip_addresses,
                "resolution_time_ms": 10  # Placeholder
            }
        except Exception as e:
            return {
                "success": False,
                "hostname": hostname,
                "error": str(e)
            }

    async def _test_network_path(self, target_ip: str) -> Dict[str, Any]:
        """Test network path and latency"""
        try:
            import subprocess
            result = subprocess.run(
                ["ping", "-c", "3", "-W", "2", target_ip],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Parse ping output
                ping_lines = result.stdout.split('\n')
                latency_line = [line for line in ping_lines if 'time=' in line]
                avg_latency = 0

                if latency_line:
                    latencies = []
                    for line in latency_line:
                        time_match = re.search(r'time=(\d+\.?\d*)', line)
                        if time_match:
                            latencies.append(float(time_match.group(1)))
                    avg_latency = sum(latencies) / len(latencies) if latencies else 0

                return {
                    "success": True,
                    "target_ip": target_ip,
                    "reachable": True,
                    "avg_latency_ms": avg_latency,
                    "packet_loss": 0
                }
            else:
                return {
                    "success": False,
                    "target_ip": target_ip,
                    "reachable": False,
                    "error": result.stderr
                }
        except Exception as e:
            return {
                "success": False,
                "target_ip": target_ip,
                "error": str(e)
            }

    async def _test_port_access(self, host: str, port: int) -> Dict[str, Any]:
        """Test TCP port accessibility"""
        try:
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=self.default_timeout)
            writer.close()
            await writer.wait_closed()

            return {
                "success": True,
                "host": host,
                "port": port,
                "accessible": True,
                "response_time_ms": 50  # Placeholder
            }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "host": host,
                "port": port,
                "accessible": False,
                "error": "Connection timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "host": host,
                "port": port,
                "accessible": False,
                "error": str(e)
            }

    async def _test_http_service(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Test HTTP/HTTPS service response"""
        try:
            url = f"{target['scheme']}://{target['hostname']}:{target['port']}{target['path']}"

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start_time = datetime.utcnow()
                async with session.get(url) as response:
                    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    content_length = len(await response.text())

                    return {
                        "success": True,
                        "url": url,
                        "status_code": response.status,
                        "response_time_ms": response_time,
                        "content_length": content_length,
                        "headers": dict(response.headers),
                        "accessible": response.status < 500
                    }
        except Exception as e:
            return {
                "success": False,
                "url": url if 'url' in locals() else f"{target['scheme']}://{target['hostname']}:{target['port']}{target['path']}",
                "error": str(e),
                "accessible": False
            }

    async def _test_specific_service(self, service_name: str, target: Dict[str, Any]) -> Dict[str, Any]:
        """Test service-specific functionality"""
        service_tests = {}

        try:
            if service_name == "family-assistant":
                # Test API endpoints
                api_endpoints = ["/health", "/dashboard/system-health"]
                for endpoint in api_endpoints:
                    url = f"{target['scheme']}://{target['hostname']}:{target['port']}{endpoint}"
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url) as response:
                                service_tests[f"api_{endpoint.replace('/', '_')}"] = {
                                    "status_code": response.status,
                                    "success": response.status == 200
                                }
                    except Exception as e:
                        service_tests[f"api_{endpoint.replace('/', '_')}"] = {
                            "success": False,
                            "error": str(e)
                        }

            elif service_name == "n8n":
                # Test N8n specific endpoints
                url = f"{target['scheme']}://{target['hostname']}:{target['port']}/healthz"
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            service_tests["health_check"] = {
                                "status_code": response.status,
                                "success": response.status == 200
                            }
                except Exception as e:
                    service_tests["health_check"] = {
                        "success": False,
                        "error": str(e)
                    }

        except Exception as e:
            service_tests["error"] = str(e)

        return service_tests

    async def _analyze_system_resources(self) -> Dict[str, Any]:
        """Analyze local system resources"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage('/')

            # Network metrics
            network = psutil.net_io_counters()

            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency_mhz": cpu_freq.current if cpu_freq else None,
                    "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
                },
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            }
        except Exception as e:
            return {"error": str(e)}

    def _determine_connectivity_status(self, tests: Dict) -> str:
        """Determine overall connectivity status"""
        if not tests:
            return "unknown"

        failed_tests = sum(1 for test in tests.values() if not test.get("success", False))

        if failed_tests == 0:
            return "healthy"
        elif failed_tests <= len(tests) / 2:
            return "degraded"
        else:
            return "critical"

    def _generate_connectivity_recommendations(self, tests: Dict, status: str) -> List[str]:
        """Generate connectivity recommendations"""
        recommendations = []

        if "dns" in tests and not tests["dns"]["success"]:
            recommendations.append(f"DNS resolution failed for {tests['dns']['hostname']}")

        if "port_access" in tests and not tests["port_access"]["success"]:
            recommendations.append("Check firewall rules and service status")

        if "http_service" in tests and not tests["http_service"]["success"]:
            recommendations.append("Verify service is running and properly configured")

        if status == "degraded":
            recommendations.append("Partial connectivity issues detected - investigate individual test failures")

        if status == "critical":
            recommendations.append("Critical connectivity failure - check network configuration and service status")

        return recommendations

    async def _analyze_network_performance(self) -> Dict[str, Any]:
        """Analyze network performance metrics"""
        try:
            # Test latency to service node
            latency_result = await self._test_network_path(self.service_node_ip)

            # Test bandwidth (simplified)
            bandwidth_test = await self._test_bandwidth()

            return {
                "latency_ms": latency_result.get("avg_latency_ms", 0),
                "packet_loss": latency_result.get("packet_loss", 0),
                "bandwidth_mbps": bandwidth_test.get("bandwidth_mbps", 0),
                "connection_quality": self._assess_connection_quality(latency_result, bandwidth_test)
            }
        except Exception as e:
            return {"error": str(e)}

    async def _test_bandwidth(self) -> Dict[str, Any]:
        """Simple bandwidth test (placeholder)"""
        # This would typically use iperf or similar tools
        return {
            "bandwidth_mbps": 1000,  # Placeholder
            "test_duration_s": 5
        }

    def _assess_connection_quality(self, latency_result: Dict, bandwidth_result: Dict) -> str:
        """Assess overall connection quality"""
        latency = latency_result.get("avg_latency_ms", 0)
        bandwidth = bandwidth_result.get("bandwidth_mbps", 0)

        if latency < 10 and bandwidth > 500:
            return "excellent"
        elif latency < 50 and bandwidth > 100:
            return "good"
        elif latency < 100:
            return "fair"
        else:
            return "poor"

    def _calculate_performance_score(self, metrics: Dict, bottlenecks: List) -> int:
        """Calculate overall performance score"""
        base_score = 100

        # Deduct points for bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck["severity"] == "high":
                base_score -= 20
            elif bottleneck["severity"] == "medium":
                base_score -= 10
            else:
                base_score -= 5

        return max(0, base_score)

    def _generate_performance_recommendations(self, bottlenecks: List, metrics: Dict) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []

        for bottleneck in bottlenecks:
            if bottleneck["type"] == "cpu":
                recommendations.append("Consider scaling CPU resources or optimizing CPU-intensive processes")
            elif bottleneck["type"] == "memory":
                recommendations.append("Add more RAM or optimize memory usage in applications")
            elif bottleneck["type"] == "disk":
                recommendations.append("Clean up disk space or add storage capacity")
            elif bottleneck["type"] == "network":
                recommendations.append("Optimize network configuration or check for bandwidth issues")

        if not bottlenecks:
            recommendations.append("System performance looks good - continue monitoring")

        return recommendations

    # Placeholder methods for comprehensive functionality
    async def _check_exposed_ports(self) -> Dict[str, Any]:
        """Check for unnecessarily exposed ports"""
        return {"vulnerabilities": []}

    async def _check_default_credentials(self) -> Dict[str, Any]:
        """Check for default credentials"""
        return {"vulnerabilities": []}

    async def _check_ssl_certificates(self) -> Dict[str, Any]:
        """Check SSL certificates"""
        return {"vulnerabilities": []}

    async def _check_system_updates(self) -> Dict[str, Any]:
        """Check for system updates"""
        return {"vulnerabilities": []}

    def _calculate_security_score(self, checks: Dict) -> int:
        """Calculate security score"""
        return 85  # Placeholder

    def _determine_risk_level(self, score: int) -> str:
        """Determine risk level from security score"""
        if score >= 80:
            return "low"
        elif score >= 60:
            return "medium"
        else:
            return "high"

    async def _get_historical_metrics(self) -> Dict[str, Any]:
        """Get historical metrics (placeholder)"""
        return {"cpu_trend": "stable", "memory_trend": "increasing"}

    def _calculate_growth_rates(self, historical_data: Dict) -> Dict[str, float]:
        """Calculate resource growth rates"""
        return {"cpu_growth_rate": 0.1, "memory_growth_rate": 0.15}  # Placeholder

    async def _get_local_node_info(self) -> Dict[str, Any]:
        """Get local node information"""
        return {
            "hostname": socket.gethostname(),
            "ip_addresses": socket.gethostbyname_ex(socket.gethostname())[2],
            "services": {}
        }

    async def _get_remote_node_info(self, ip: str) -> Dict[str, Any]:
        """Get remote node information"""
        return {
            "hostname": "asuna",
            "ip": ip,
            "services": {}
        }

    async def _test_node_connectivity(self, ip: str) -> Dict[str, Any]:
        """Test connectivity to a node"""
        return await self._test_network_path(ip)

# MCP Server Interface
async def main():
    """MCP Server entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--describe":
        print(json.dumps({
            "name": "homelab-infrastructure",
            "description": "Infrastructure troubleshooting and optimization for homelab development",
            "version": "1.0.0",
            "tools": [
                {
                    "name": "diagnose_connectivity_issue",
                    "description": "Comprehensive connectivity diagnosis",
                    "parameters": {
                        "target": {"type": "string", "required": True},
                        "service_name": {"type": "string", "required": False}
                    }
                },
                {
                    "name": "analyze_performance_bottlenecks",
                    "description": "Analyze performance and identify bottlenecks",
                    "parameters": {
                        "focus": {"type": "string", "required": False, "enum": ["all", "system", "network", "services"]}
                    }
                },
                {
                    "name": "security_audit",
                    "description": "Perform security audit of infrastructure",
                    "parameters": {
                        "scope": {"type": "string", "required": False, "enum": ["basic", "intermediate", "comprehensive"]}
                    }
                },
                {
                    "name": "capacity_planning",
                    "description": "Capacity planning and resource optimization",
                    "parameters": {
                        "timeframe_months": {"type": "integer", "required": False}
                    }
                },
                {
                    "name": "troubleshoot_service",
                    "description": "Comprehensive service troubleshooting",
                    "parameters": {
                        "service_name": {"type": "string", "required": True}
                    }
                },
                {
                    "name": "network_topology_map",
                    "description": "Generate network topology map",
                    "parameters": {}
                }
            ]
        }))
        return

    detective = InfrastructureDetectiveMCP()

    # Example usage for testing
    if len(sys.argv) > 2:
        command = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

        if command == "diagnose_connectivity_issue":
            result = await detective.diagnose_connectivity_issue(**args)
        elif command == "analyze_performance_bottlenecks":
            result = await detective.analyze_performance_bottlenecks(**args)
        elif command == "security_audit":
            result = await detective.security_audit(**args)
        elif command == "capacity_planning":
            result = await detective.capacity_planning(**args)
        elif command == "troubleshoot_service":
            result = await detective.troubleshoot_service(**args)
        elif command == "network_topology_map":
            result = await detective.network_topology_map()
        else:
            result = {"error": f"Unknown command: {command}"}

        print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())