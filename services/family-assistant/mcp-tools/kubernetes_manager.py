#!/usr/bin/env python3
"""
MCP Tool: Kubernetes Manager for Homelab Development
Enhances Claude Code with advanced Kubernetes management capabilities
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

class KubernetesManagerMCP:
    """
    Advanced Kubernetes management tool for homelab development workflow.
    Provides smart deployment monitoring, health checks, and troubleshooting.
    """

    def __init__(self):
        try:
            # Load Kubernetes configuration
            config.load_kube_config()
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            # ExtensionsV1beta1Api is deprecated and may not be available
            try:
                self.extensions_v1beta1 = client.ExtensionsV1beta1Api()
            except AttributeError:
                self.extensions_v1beta1 = None
            self.default_namespace = os.getenv("HOMELAB_NAMESPACE", "homelab")
        except Exception as e:
            print(f"Failed to initialize Kubernetes client: {e}")
            sys.exit(1)

    async def get_deployment_health(self, deployment_name: str, namespace: str = None) -> Dict[str, Any]:
        """
        Get comprehensive health status of a specific deployment
        """
        if namespace is None:
            namespace = self.default_namespace

        try:
            # Get deployment info
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=namespace
            )

            # Get replica status
            replicas = deployment.spec.replicas or 0
            ready_replicas = deployment.status.ready_replicas or 0
            available_replicas = deployment.status.available_replicas or 0

            # Get pods
            pods = self.v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app={deployment_name}"
            )

            pod_status = {}
            for pod in pods.items:
                pod_status[pod.metadata.name] = {
                    "status": pod.status.phase,
                    "ready": all(
                        condition.status == "True"
                        for condition in pod.status.conditions or []
                        if condition.type == "Ready"
                    ),
                    "restarts": sum(
                        container.restart_count or 0
                        for container in (pod.status.container_statuses or [])
                    ),
                    "age": self._calculate_age(pod.metadata.creation_timestamp),
                    "node": pod.spec.node_name
                }

            # Get recent events
            events = self.v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={deployment_name}"
            )

            recent_events = [
                {
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None
                }
                for event in events.items[:10]  # Last 10 events
            ]

            # Health assessment
            health_score = self._calculate_health_score(
                replicas, ready_replicas, available_replicas, pod_status
            )

            return {
                "deployment": deployment_name,
                "namespace": namespace,
                "health_score": health_score,
                "replicas": {
                    "desired": replicas,
                    "ready": ready_replicas,
                    "available": available_replicas,
                    "unavailable": replicas - ready_replicas
                },
                "pods": pod_status,
                "recent_events": recent_events,
                "status": self._get_health_status(health_score),
                "timestamp": datetime.utcnow().isoformat()
            }

        except ApiException as e:
            return {
                "deployment": deployment_name,
                "namespace": namespace,
                "error": str(e),
                "status": "error"
            }

    async def get_namespace_overview(self, namespace: str = None) -> Dict[str, Any]:
        """
        Get complete overview of all resources in a namespace
        """
        if namespace is None:
            namespace = self.default_namespace

        try:
            # Get all deployments
            deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)

            deployment_health = {}
            total_pods = 0
            healthy_pods = 0

            async def check_deployment(deployment):
                health = await self.get_deployment_health(
                    deployment.metadata.name, namespace
                )
                return deployment.metadata.name, health

            # Check all deployments concurrently
            tasks = [check_deployment(dep) for dep in deployments.items]
            results = await asyncio.gather(*tasks)

            for name, health in results:
                deployment_health[name] = health
                if "replicas" in health:
                    total_pods += health["replicas"]["desired"]
                    healthy_pods += health["replicas"]["ready"]

            # Get services
            services = self.v1.list_namespaced_service(namespace=namespace)
            service_info = {}

            for service in services.items:
                service_info[service.metadata.name] = {
                    "type": service.spec.type,
                    "cluster_ip": service.spec.cluster_ip,
                    "external_ips": getattr(service.spec, 'external_i_ps', []) or [],
                    "ports": [
                        {
                            "name": port.name,
                            "port": port.port,
                            "target_port": port.target_port,
                            "protocol": port.protocol
                        }
                        for port in (service.spec.ports or [])
                    ],
                    "age": self._calculate_age(service.metadata.creation_timestamp)
                }

            # Get PVCs
            pvcs = self.v1.list_namespaced_persistent_volume_claim(namespace=namespace)
            pvc_info = {}

            for pvc in pvcs.items:
                pvc_info[pvc.metadata.name] = {
                    "status": pvc.status.phase,
                    "capacity": pvc.status.capacity if pvc.status else {},
                    "access_modes": pvc.spec.access_modes or [],
                    "storage_class": pvc.spec.storage_class_name,
                    "age": self._calculate_age(pvc.metadata.creation_timestamp)
                }

            return {
                "namespace": namespace,
                "overall_health": "healthy" if healthy_pods == total_pods and total_pods > 0 else "degraded",
                "summary": {
                    "deployments": len(deployments.items),
                    "healthy_deployments": sum(1 for d in deployment_health.values() if d.get("status") == "healthy"),
                    "total_pods": total_pods,
                    "healthy_pods": healthy_pods,
                    "services": len(services.items),
                    "pvcs": len(pvcs.items)
                },
                "deployments": deployment_health,
                "services": service_info,
                "pvcs": pvc_info,
                "timestamp": datetime.utcnow().isoformat()
            }

        except ApiException as e:
            return {
                "namespace": namespace,
                "error": str(e),
                "status": "error"
            }

    async def get_pod_logs(self, pod_name: str, namespace: str = None, lines: int = 100,
                          container: str = None, follow: bool = False) -> Dict[str, Any]:
        """
        Get logs from a specific pod with intelligent error detection
        """
        if namespace is None:
            namespace = self.default_namespace

        try:
            # Get pod info first
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)

            # Determine container
            if container is None and pod.spec.containers:
                container = pod.spec.containers[0].name

            # Get logs
            logs = self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=lines,
                follow=follow
            )

            # Analyze logs for errors
            error_analysis = self._analyze_logs_for_errors(logs)

            return {
                "pod": pod_name,
                "namespace": namespace,
                "container": container,
                "logs": logs,
                "error_analysis": error_analysis,
                "timestamp": datetime.utcnow().isoformat()
            }

        except ApiException as e:
            return {
                "pod": pod_name,
                "namespace": namespace,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def restart_deployment(self, deployment_name: str, namespace: str = None,
                                strategy: str = "rolling") -> Dict[str, Any]:
        """
        Smart deployment restart with zero-downtime strategies
        """
        if namespace is None:
            namespace = self.default_namespace

        try:
            # Get current deployment state
            current_health = await self.get_deployment_health(deployment_name, namespace)

            if current_health.get("status") == "error":
                return {
                    "deployment": deployment_name,
                    "namespace": namespace,
                    "error": "Deployment not found or in error state",
                    "status": "failed"
                }

            # Perform restart based on strategy
            if strategy == "rolling":
                # Trigger rolling restart
                body = {"spec": {"template": {"metadata": {"annotations": {
                    "kubectl.kubernetes.io/restartedAt": datetime.utcnow().isoformat()
                }}}}}

                result = self.apps_v1.patch_namespaced_deployment(
                    name=deployment_name,
                    namespace=namespace,
                    body=body
                )

            elif strategy == "scale":
                # Scale down then up (for problematic deployments)
                await self._scale_deployment(deployment_name, 0, namespace)
                await asyncio.sleep(5)
                await self._scale_deployment(deployment_name,
                                            current_health["replicas"]["desired"], namespace)

            # Wait for restart to complete
            await self._wait_for_deployment_ready(deployment_name, namespace, timeout=300)

            # Get new health status
            new_health = await self.get_deployment_health(deployment_name, namespace)

            return {
                "deployment": deployment_name,
                "namespace": namespace,
                "strategy": strategy,
                "previous_health": current_health,
                "new_health": new_health,
                "restart_time": datetime.utcnow().isoformat(),
                "status": "success" if new_health.get("status") == "healthy" else "partial"
            }

        except Exception as e:
            return {
                "deployment": deployment_name,
                "namespace": namespace,
                "strategy": strategy,
                "error": str(e),
                "status": "failed",
                "restart_time": datetime.utcnow().isoformat()
            }

    async def get_resource_usage(self, namespace: str = None) -> Dict[str, Any]:
        """
        Get resource usage analysis for cost and performance optimization
        """
        if namespace is None:
            namespace = self.default_namespace

        try:
            # Get nodes info
            nodes = self.v1.list_node()
            node_resources = {}

            for node in nodes.items:
                allocatable = node.status.allocatable or {}
                node_resources[node.metadata.name] = {
                    "cpu_cores": self._parse_cpu(allocatable.get("cpu", "0")),
                    "memory_mb": self._parse_memory(allocatable.get("memory", "0Ki")),
                    "pods": int(allocatable.get("pods", "0"))
                }

            # Get pods resource requests
            pods = self.v1.list_namespaced_pod(namespace=namespace)
            pod_resources = []
            total_requests = {"cpu": 0, "memory": 0}
            total_limits = {"cpu": 0, "memory": 0}

            for pod in pods.items:
                pod_cpu_req = 0
                pod_mem_req = 0
                pod_cpu_lim = 0
                pod_mem_lim = 0

                for container in pod.spec.containers:
                    if container.resources:
                        requests = container.resources.requests or {}
                        limits = container.resources.limits or {}

                        pod_cpu_req += self._parse_cpu(requests.get("cpu", "0"))
                        pod_mem_req += self._parse_memory(requests.get("memory", "0Ki"))
                        pod_cpu_lim += self._parse_cpu(limits.get("cpu", "0"))
                        pod_mem_lim += self._parse_memory(limits.get("memory", "0Ki"))

                total_requests["cpu"] += pod_cpu_req
                total_requests["memory"] += pod_mem_req
                total_limits["cpu"] += pod_cpu_lim
                total_limits["memory"] += pod_mem_lim

                pod_resources.append({
                    "name": pod.metadata.name,
                    "node": pod.spec.node_name,
                    "requests": {"cpu": pod_cpu_req, "memory": pod_mem_req},
                    "limits": {"cpu": pod_cpu_lim, "memory": pod_mem_lim},
                    "status": pod.status.phase
                })

            # Calculate utilization percentages
            total_cluster_cpu = sum(node["cpu_cores"] for node in node_resources.values())
            total_cluster_memory = sum(node["memory_mb"] for node in node_resources.values())

            utilization = {
                "cpu_requested_percent": (total_requests["cpu"] / total_cluster_cpu * 100) if total_cluster_cpu > 0 else 0,
                "cpu_limited_percent": (total_limits["cpu"] / total_cluster_cpu * 100) if total_cluster_cpu > 0 else 0,
                "memory_requested_percent": (total_requests["memory"] / total_cluster_memory * 100) if total_cluster_memory > 0 else 0,
                "memory_limited_percent": (total_limits["memory"] / total_cluster_memory * 100) if total_cluster_memory > 0 else 0
            }

            return {
                "namespace": namespace,
                "cluster_nodes": node_resources,
                "pod_resources": pod_resources,
                "total_requests": total_requests,
                "total_limits": total_limits,
                "utilization": utilization,
                "optimization_suggestions": self._generate_optimization_suggestions(utilization),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "namespace": namespace,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def troubleshoot_service(self, service_name: str, namespace: str = None) -> Dict[str, Any]:
        """
        Comprehensive service troubleshooting
        """
        if namespace is None:
            namespace = self.default_namespace

        try:
            # Get service details
            service = self.v1.read_namespaced_service(name=service_name, namespace=namespace)

            # Get endpoints
            endpoints = self.v1.read_namespaced_endpoints(name=service_name, namespace=namespace)

            # Get pods matching service selector
            if service.spec.selector:
                selector = ",".join([f"{k}={v}" for k, v in service.spec.selector.items()])
                pods = self.v1.list_namespaced_pod(namespace=namespace, label_selector=selector)
            else:
                pods = self.v1.list_namespaced_pod(namespace=namespace)

            # Network connectivity test
            connectivity_issues = []

            # Check if endpoints exist
            if not endpoints.subsets:
                connectivity_issues.append("No endpoints found - service has no ready pods")

            # Check pod readiness
            ready_pods = 0
            for pod in pods.items:
                if pod.status.phase == "Running":
                    conditions = pod.status.conditions or []
                    if any(c.type == "Ready" and c.status == "True" for c in conditions):
                        ready_pods += 1

            if ready_pods == 0:
                connectivity_issues.append("No ready pods found for service")

            # Port accessibility
            port_issues = []
            for port in service.spec.ports or []:
                if port.node_port:
                    # Check NodePort accessibility
                    port_issues.append(f"NodePort {port.node_port} should be accessible on cluster nodes")

            # Recent events
            events = self.v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={service_name}"
            )

            service_events = [
                {
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None
                }
                for event in events.items[:5]
            ]

            return {
                "service": service_name,
                "namespace": namespace,
                "service_info": {
                    "type": service.spec.type,
                    "cluster_ip": service.spec.cluster_ip,
                    "external_ips": service.spec.external_ips or [],
                    "ports": [
                        {
                            "name": port.name,
                            "port": port.port,
                            "target_port": port.target_port,
                            "node_port": port.node_port,
                            "protocol": port.protocol
                        }
                        for port in (service.spec.ports or [])
                    ],
                    "selector": service.spec.selector
                },
                "endpoints": {
                    "subsets": [
                        {
                            "addresses": [addr.ip for addr in subset.addresses or []],
                            "ports": [
                                {"port": port.port, "protocol": port.protocol}
                                for port in (subset.ports or [])
                            ]
                        }
                        for subset in (endpoints.subsets or [])
                    ]
                },
                "pod_status": {
                    "total_pods": len(pods.items),
                    "ready_pods": ready_pods,
                    "pod_names": [pod.metadata.name for pod in pods.items]
                },
                "connectivity_issues": connectivity_issues,
                "port_issues": port_issues,
                "recent_events": service_events,
                "health_status": "healthy" if not connectivity_issues and ready_pods > 0 else "unhealthy",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "service": service_name,
                "namespace": namespace,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    # Helper methods
    def _calculate_age(self, timestamp) -> str:
        """Calculate human-readable age"""
        if not timestamp:
            return "unknown"

        age = datetime.utcnow() - timestamp.replace(tzinfo=None)
        if age.days > 0:
            return f"{age.days}d"
        elif age.seconds > 3600:
            return f"{age.seconds // 3600}h"
        elif age.seconds > 60:
            return f"{age.seconds // 60}m"
        else:
            return f"{age.seconds}s"

    def _calculate_health_score(self, desired: int, ready: int, available: int, pod_status: Dict) -> int:
        """Calculate health score (0-100)"""
        if desired == 0:
            return 100

        replica_score = (ready / desired) * 50

        # Pod health score
        healthy_pods = sum(1 for pod in pod_status.values() if pod["ready"] and pod["status"] == "Running")
        total_pods = len(pod_status)
        pod_score = (healthy_pods / total_pods * 50) if total_pods > 0 else 0

        return int(replica_score + pod_score)

    def _get_health_status(self, score: int) -> str:
        """Get status from health score"""
        if score >= 90:
            return "healthy"
        elif score >= 70:
            return "degraded"
        elif score >= 50:
            return "unhealthy"
        else:
            return "critical"

    def _analyze_logs_for_errors(self, logs: str) -> Dict[str, Any]:
        """Analyze logs for error patterns"""
        error_patterns = [
            "ERROR", "FATAL", "CRITICAL", "Exception", "Traceback",
            "failed", "timeout", "connection refused", "permission denied"
        ]

        warning_patterns = [
            "WARNING", "WARN", "deprecated", "retry", "fallback"
        ]

        lines = logs.split('\n')
        error_count = 0
        warning_count = 0
        error_lines = []

        for i, line in enumerate(lines, 1):
            line_lower = line.lower()
            for pattern in error_patterns:
                if pattern.lower() in line_lower:
                    error_count += 1
                    if len(error_lines) < 5:  # Store first 5 errors
                        error_lines.append(f"Line {i}: {line.strip()}")
                    break

            for pattern in warning_patterns:
                if pattern.lower() in line_lower and "error" not in line_lower:
                    warning_count += 1
                    break

        return {
            "total_lines": len(lines),
            "error_count": error_count,
            "warning_count": warning_count,
            "error_rate": (error_count / len(lines) * 100) if lines else 0,
            "sample_errors": error_lines
        }

    async def _scale_deployment(self, deployment_name: str, replicas: int, namespace: str):
        """Scale deployment to specified replica count"""
        body = {"spec": {"replicas": replicas}}
        self.apps_v1.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=namespace,
            body=body
        )

    async def _wait_for_deployment_ready(self, deployment_name: str, namespace: str, timeout: int = 300):
        """Wait for deployment to become ready"""
        start_time = datetime.utcnow()

        while (datetime.utcnow() - start_time).seconds < timeout:
            try:
                deployment = self.apps_v1.read_namespaced_deployment(
                    name=deployment_name, namespace=namespace
                )

                if (deployment.status.ready_replicas == deployment.spec.replicas and
                    deployment.status.ready_replicas > 0):
                    return True

                await asyncio.sleep(5)
            except Exception:
                await asyncio.sleep(5)
                continue

        return False

    def _parse_cpu(self, cpu_str: str) -> float:
        """Parse CPU string to cores"""
        if not cpu_str:
            return 0

        cpu_str = cpu_str.strip()
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000
        else:
            return float(cpu_str)

    def _parse_memory(self, mem_str: str) -> float:
        """Parse memory string to MB"""
        if not mem_str:
            return 0

        mem_str = mem_str.strip()
        multipliers = {
            'Ki': 1/1024,
            'Mi': 1,
            'Gi': 1024,
            'K': 1/1000,
            'M': 1,
            'G': 1000
        }

        for suffix, multiplier in multipliers.items():
            if mem_str.endswith(suffix):
                return float(mem_str[:-len(suffix)]) * multiplier

        return float(mem_str)

    def _generate_optimization_suggestions(self, utilization: Dict) -> List[str]:
        """Generate optimization suggestions based on utilization"""
        suggestions = []

        if utilization["cpu_requested_percent"] < 30:
            suggestions.append("CPU requests seem low - consider increasing for better performance")
        elif utilization["cpu_requested_percent"] > 90:
            suggestions.append("CPU requests are high - consider scaling or optimizing workloads")

        if utilization["memory_requested_percent"] < 30:
            suggestions.append("Memory requests seem low - consider increasing to avoid OOM kills")
        elif utilization["memory_requested_percent"] > 90:
            suggestions.append("Memory usage is high - monitor for memory pressure")

        if utilization["cpu_limited_percent"] == 0:
            suggestions.append("No CPU limits set - consider adding limits for fairness")

        if utilization["memory_limited_percent"] == 0:
            suggestions.append("No memory limits set - consider adding limits for stability")

        return suggestions

# MCP Server Interface
async def main():
    """MCP Server entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--describe":
        print(json.dumps({
            "name": "homelab-kubernetes",
            "description": "Advanced Kubernetes management for homelab development",
            "version": "1.0.0",
            "tools": [
                {
                    "name": "get_deployment_health",
                    "description": "Get comprehensive health status of a deployment",
                    "parameters": {
                        "deployment_name": {"type": "string", "required": True},
                        "namespace": {"type": "string", "required": False}
                    }
                },
                {
                    "name": "get_namespace_overview",
                    "description": "Get complete overview of all resources in namespace",
                    "parameters": {
                        "namespace": {"type": "string", "required": False}
                    }
                },
                {
                    "name": "get_pod_logs",
                    "description": "Get pod logs with error analysis",
                    "parameters": {
                        "pod_name": {"type": "string", "required": True},
                        "namespace": {"type": "string", "required": False},
                        "lines": {"type": "integer", "required": False},
                        "container": {"type": "string", "required": False}
                    }
                },
                {
                    "name": "restart_deployment",
                    "description": "Smart deployment restart with zero-downtime",
                    "parameters": {
                        "deployment_name": {"type": "string", "required": True},
                        "namespace": {"type": "string", "required": False},
                        "strategy": {"type": "string", "required": False, "enum": ["rolling", "scale"]}
                    }
                },
                {
                    "name": "get_resource_usage",
                    "description": "Get resource usage analysis for optimization",
                    "parameters": {
                        "namespace": {"type": "string", "required": False}
                    }
                },
                {
                    "name": "troubleshoot_service",
                    "description": "Comprehensive service troubleshooting",
                    "parameters": {
                        "service_name": {"type": "string", "required": True},
                        "namespace": {"type": "string", "required": False}
                    }
                }
            ]
        }))
        return

    k8s_manager = KubernetesManagerMCP()

    # Example usage for testing
    if len(sys.argv) > 2:
        command = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

        if command == "get_deployment_health":
            result = await k8s_manager.get_deployment_health(**args)
        elif command == "get_namespace_overview":
            result = await k8s_manager.get_namespace_overview(**args)
        elif command == "get_pod_logs":
            result = await k8s_manager.get_pod_logs(**args)
        elif command == "restart_deployment":
            result = await k8s_manager.restart_deployment(**args)
        elif command == "get_resource_usage":
            result = await k8s_manager.get_resource_usage(**args)
        elif command == "troubleshoot_service":
            result = await k8s_manager.troubleshoot_service(**args)
        else:
            result = {"error": f"Unknown command: {command}"}

        print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())