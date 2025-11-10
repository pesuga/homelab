"""
Homelab Management MCP Tools

Specialized MCP (Model Context Protocol) tools designed for homelab infrastructure management.
These tools provide AI assistants with safe, controlled access to manage Kubernetes services,
monitor infrastructure, and perform homelab-specific operations.
"""

import asyncio
import subprocess
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HomelabMCPManager:
    """MCP Manager for homelab operations with safety controls."""

    def __init__(self):
        self.kubectl_base = ["kubectl"]
        self.ssh_base = ["ssh"]
        self.allowed_namespaces = ["homelab", "default", "kube-system", "monitoring"]
        self.safe_operations = [
            "get", "describe", "logs", "top", "status", "config",
            "rollout", "scale", "restart", "exec", "cp", "apply"
        ]

    async def get_service_status(self, namespace: str = "homelab") -> Dict[str, Any]:
        """
        Get status of all services in a namespace.

        Args:
            namespace: Kubernetes namespace to query

        Returns:
            Dictionary containing service status information
        """
        if namespace not in self.allowed_namespaces:
            raise ValueError(f"Namespace '{namespace}' not allowed")

        try:
            # Get services
            result = await self._run_kubectl([
                "get", "services", "-n", namespace, "-o", "json"
            ])
            services_data = json.loads(result.stdout)

            # Get pods
            pods_result = await self._run_kubectl([
                "get", "pods", "-n", namespace, "-o", "json"
            ])
            pods_data = json.loads(pods_result.stdout)

            # Process and combine data
            status_info = {
                "namespace": namespace,
                "timestamp": datetime.now().isoformat(),
                "services": [],
                "pods": [],
                "summary": {}
            }

            # Process services
            for service in services_data.get("items", []):
                service_info = {
                    "name": service["metadata"]["name"],
                    "type": service["spec"].get("type", "ClusterIP"),
                    "cluster_ip": service["spec"].get("clusterIP"),
                    "ports": service["spec"].get("ports", []),
                    "selector": service["spec"].get("selector", {}),
                    "creation_timestamp": service["metadata"]["creationTimestamp"]
                }
                status_info["services"].append(service_info)

            # Process pods
            for pod in pods_data.get("items", []):
                pod_info = {
                    "name": pod["metadata"]["name"],
                    "namespace": pod["metadata"]["namespace"],
                    "status": pod["status"].get("phase", "Unknown"),
                    "node": pod["spec"].get("nodeName"),
                    "creation_timestamp": pod["metadata"]["creationTimestamp"],
                    "labels": pod["metadata"].get("labels", {}),
                    "conditions": pod["status"].get("conditions", []),
                    "containers": []
                }

                # Add container information
                for container in pod.get("spec", {}).get("containers", []):
                    container_info = {
                        "name": container["name"],
                        "image": container["image"],
                        "ports": container.get("ports", []),
                        "resources": container.get("resources", {}),
                    }
                    pod_info["containers"].append(container_info)

                status_info["pods"].append(pod_info)

            # Generate summary
            status_info["summary"] = {
                "total_services": len(status_info["services"]),
                "total_pods": len(status_info["pods"]),
                "running_pods": len([p for p in status_info["pods"] if p["status"] == "Running"]),
                "pending_pods": len([p for p in status_info["pods"] if p["status"] == "Pending"]),
                "failed_pods": len([p for p in status_info["pods"] if p["status"] in ["Failed", "Error"]])
            }

            return status_info

        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {"error": str(e), "namespace": namespace}

    async def get_resource_usage(self, namespace: str = "homelab") -> Dict[str, Any]:
        """
        Get resource usage statistics for namespace.

        Args:
            namespace: Kubernetes namespace to analyze

        Returns:
            Dictionary containing resource usage information
        """
        if namespace not in self.allowed_namespaces:
            raise ValueError(f"Namespace '{namespace}' not allowed")

        try:
            # Get resource quotas
            quota_result = await self._run_kubectl([
                "describe", "quota", "-n", namespace
            ])

            # Get top pods resource usage
            top_result = await self._run_kubectl([
                "top", "pods", "-n", namespace", "--sort-by=cpu"
            ])

            # Get node information
            node_result = await self._run_kubectl([
                "top", "nodes"
            ])

            return {
                "namespace": namespace,
                "timestamp": datetime.now().isoformat(),
                "resource_quotas": quota_result.stdout,
                "pod_usage": top_result.stdout,
                "node_usage": node_result.stdout,
                "summary": self._parse_resource_usage(quota_result.stdout, top_result.stdout)
            }

        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {"error": str(e), "namespace": namespace}

    async def get_pod_logs(self, pod_name: str, namespace: str = "homelab",
                          lines: int = 100, container: str = None) -> Dict[str, Any]:
        """
        Get logs from a specific pod.

        Args:
            pod_name: Name of the pod
            namespace: Kubernetes namespace
            lines: Number of recent lines to retrieve
            container: Specific container name (optional)

        Returns:
            Dictionary containing pod logs
        """
        if namespace not in self.allowed_namespaces:
            raise ValueError(f"Namespace '{namespace}' not allowed")

        try:
            cmd = ["logs", pod_name, "-n", namespace, "--tail", str(lines)]
            if container:
                cmd.extend(["-c", container])

            result = await self._run_kubectl(cmd)

            return {
                "pod_name": pod_name,
                "namespace": namespace,
                "container": container,
                "lines": lines,
                "timestamp": datetime.now().isoformat(),
                "logs": result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            logger.error(f"Error getting pod logs: {e}")
            return {"error": str(e), "pod_name": pod_name}

    async def scale_deployment(self, deployment_name: str, replicas: int,
                            namespace: str = "homelab") -> Dict[str, Any]:
        """
        Scale a deployment to specified replica count.

        Args:
            deployment_name: Name of the deployment
            replicas: Target replica count
            namespace: Kubernetes namespace

        Returns:
            Dictionary containing scale operation result
        """
        if namespace not in self.allowed_namespaces:
            raise ValueError(f"Namespace '{namespace}' not allowed")

        if replicas < 0 or replicas > 20:
            raise ValueError("Replica count must be between 0 and 20")

        try:
            # First, get current replica count for rollback info
            current_result = await self._run_kubectl([
                "get", "deployment", deployment_name, "-n", namespace, "-o", "jsonpath={.spec.replicas}"
            ])
            current_replicas = int(current_result.stdout.strip() or "0")

            # Perform scaling
            scale_result = await self._run_kubectl([
                "scale", "deployment", deployment_name, f"--replicas={replicas}", "-n", namespace
            ])

            # Wait for scaling to complete (with timeout)
            rollout_result = await self._run_kubectl([
                "rollout", "status", f"deployment/{deployment_name}", "-n", namespace,
                "--timeout=60s"
            ])

            return {
                "deployment_name": deployment_name,
                "namespace": namespace,
                "previous_replicas": current_replicas,
                "new_replicas": replicas,
                "timestamp": datetime.now().isoformat(),
                "scale_command": scale_result.stdout,
                "rollout_status": rollout_result.stdout,
                "success": rollout_result.returncode == 0
            }

        except Exception as e:
            logger.error(f"Error scaling deployment: {e}")
            return {"error": str(e), "deployment_name": deployment_name}

    async def restart_deployment(self, deployment_name: str, namespace: str = "homelab") -> Dict[str, Any]:
        """
        Restart a deployment by triggering a rollout restart.

        Args:
            deployment_name: Name of the deployment
            namespace: Kubernetes namespace

        Returns:
            Dictionary containing restart operation result
        """
        if namespace not in self.allowed_namespaces:
            raise ValueError(f"Namespace '{namespace}' not allowed")

        try:
            # Trigger rollout restart
            result = await self._run_kubectl([
                "rollout", "restart", f"deployment/{deployment_name}", "-n", namespace"
            ])

            # Wait for restart to complete
            status_result = await self._run_kubectl([
                "rollout", "status", f"deployment/{deployment_name}", "-n", namespace",
                "--timeout=120s"
            ])

            return {
                "deployment_name": deployment_name,
                "namespace": namespace,
                "timestamp": datetime.now().isoformat(),
                "restart_command": result.stdout,
                "rollout_status": status_result.stdout,
                "success": status_result.returncode == 0
            }

        except Exception as e:
            logger.error(f"Error restarting deployment: {e}")
            return {"error": str(e), "deployment_name": deployment_name}

    async def execute_in_pod(self, pod_name: str, command: List[str], namespace: str = "homelab",
                           container: str = None) -> Dict[str, Any]:
        """
        Execute a command in a pod container.

        Args:
            pod_name: Name of the pod
            command: Command to execute
            namespace: Kubernetes namespace
            container: Container name (optional)

        Returns:
            Dictionary containing execution result
        """
        if namespace not in self.allowed_namespaces:
            raise ValueError(f"Namespace '{namespace}' not allowed")

        # Safety check for dangerous commands
        dangerous_commands = [
            "rm", "dd", "mkfs", "fdisk", "passwd", "su", "sudo",
            "chmod", "chown", "kill", "pkill", "systemctl"
        ]

        if any(dangerous_cmd in " ".join(command) for dangerous_cmd in dangerous_commands):
            raise ValueError("Dangerous commands not allowed for safety")

        try:
            cmd = ["exec", pod_name, "--"]
            if container:
                cmd.extend(["-c", container])
            cmd.extend(["--",] + command)
            cmd.extend(["-n", namespace])

            result = await self._run_kubectl(cmd)

            return {
                "pod_name": pod_name,
                "namespace": namespace,
                "container": container,
                "command": " ".join(command),
                "timestamp": datetime.now().isoformat(),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0
            }

        except Exception as e:
            logger.error(f"Error executing command in pod: {e}")
            return {"error": str(e), "pod_name": pod_name, "command": " ".join(command)}

    async def get_events(self, namespace: str = "homelabel", kind: str = None,
                        since: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Kubernetes events for monitoring and debugging.

        Args:
            namespace: Kubernetes namespace
            kind: Filter by resource kind (optional)
            since: Get events since this timestamp (optional)

        Returns:
            Dictionary containing Kubernetes events
        """
        if namespace not in self.allowed_namespaces:
            raise ValueError(f"Namespace '{namespace}' not allowed")

        try:
            cmd = ["get", "events", "-n", namespace, "--sort-by=.metadata.creationTimestamp"]

            if kind:
                cmd.extend(["--field-selector", f"involvedObject.kind={kind}"])
            if since:
                cmd.extend(["--field-selector", f"creationTimestamp>={since}"])

            result = await self._run_kubectl(cmd)

            # Parse events into structured format
            events = []
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header line
                if line.strip():
                    # Basic event parsing - would need more sophisticated parsing for production
                    events.append({
                        "raw": line,
                        "timestamp": datetime.now().isoformat()
                    })

            return {
                "namespace": namespace,
                "kind_filter": kind,
                "since_filter": since,
                "timestamp": datetime.now().isoformat(),
                "events": events[-50:],  # Return last 50 events
                "total_events": len(events)
            }

        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return {"error": str(e), "namespace": namespace}

    async def get_cluster_info(self) -> Dict[str, Any]:
        """
        Get basic cluster information and status.

        Returns:
            Dictionary containing cluster information
        """
        try:
            # Get cluster info
            cluster_info_result = await self._run_kubectl(["cluster-info"])

            # Get nodes
            nodes_result = await self._run_kubectl([
                "get", "nodes", "-o", "json"
            ])
            nodes_data = json.loads(nodes_result.stdout)

            # Get version
            version_result = await self._run_kubectl(["version", "--short"])

            # Process node information
            nodes = []
            for node in nodes_data.get("items", []):
                node_info = {
                    "name": node["metadata"]["name"],
                    "status": node["status"].get("conditions", []),
                    "creation_timestamp": node["metadata"]["creationTimestamp"],
                    "labels": node["metadata"].get("labels", {}),
                    "annotations": node["metadata"].get("annotations", {}),
                    "addresses": node["status"].get("addresses", []),
                    "capacity": node["status"].get("capacity", {}),
                    "allocatable": node["status"].get("allocatable", {})
                }
                nodes.append(node_info)

            return {
                "timestamp": datetime.now().isoformat(),
                "cluster_info": cluster_info_result.stdout,
                "kubernetes_version": version_result.stdout.strip(),
                "total_nodes": len(nodes),
                "nodes": nodes,
                "cluster_status": "healthy" if len(nodes) > 0 else "unknown"
            }

        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return {"error": str(e)}

    async def _run_kubectl(self, cmd: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """
        Execute kubectl command with proper error handling.
        """
        try:
            full_cmd = self.kubectl_base + cmd
            result = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=timeout
            )
            stdout, stderr = await result.communicate()

            return subprocess.CompletedProcess(
                args=full_cmd,
                returncode=result.returncode,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else ""
            )

        except asyncio.TimeoutError:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            raise
        except Exception as e:
            logger.error(f"Error executing kubectl command: {e}")
            raise

    def _parse_resource_usage(self, quota_output: str, top_output: str) -> Dict[str, Any]:
        """Parse resource usage from kubectl outputs."""
        # This is a simplified parser - would need more sophisticated parsing for production
        return {
            "quota_info": quota_output,
            "top_info": top_output,
            "cpu_pressure": "normal",
            "memory_pressure": "normal",
            "storage_pressure": "normal"
        }


# MCP Tool registration and interface
class HomelabMCPTools:
    """Collection of MCP tools for homelab management."""

    def __init__(self):
        self.manager = HomelabMCPManager()

    def get_tools(self) -> Dict[str, Any]:
        """Return all available MCP tools."""
        return {
            "get_service_status": {
                "description": "Get comprehensive status of all services in a namespace",
                "parameters": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace (default: homelab)",
                        "default": "homelab"
                    }
                }
            },
            "get_resource_usage": {
                "description": "Get resource usage statistics for monitoring",
                "parameters": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace (default: homelab)",
                        "default": "homelab"
                    }
                }
            },
            "get_pod_logs": {
                "description": "Retrieve logs from a specific pod",
                "parameters": {
                    "pod_name": {
                        "type": "string",
                        "description": "Name of the pod"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace (default: homelelab)",
                        "default": "homelab"
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Number of recent lines to retrieve",
                        "default": 100
                    },
                    "container": {
                        "type": "string",
                        "description": "Container name within pod (optional)"
                    }
                }
            },
            "scale_deployment": {
                "description": "Scale a deployment to specified replica count",
                "parameters": {
                    "deployment_name": {
                        "type": "string",
                        "description": "Name of the deployment to scale"
                    },
                    "replicas": {
                        "type": "integer",
                        "description": "Target replica count (0-20)"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace (default: homelab)",
                        "default": "homelab"
                    }
                }
            },
            "restart_deployment": {
                "description": "Restart a deployment with zero downtime",
                "parameters": {
                    "deployment_name": {
                        "type": "string",
                        "description": "Name of the deployment to restart"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace (default: homelab)",
                        "default": "homelab"
                    }
                }
            },
            "execute_in_pod": {
                "description": "Execute command safely within a pod container",
                "parameters": {
                    "pod_name": {
                        "type": "string",
                        "description": "Name of the pod"
                    },
                    "command": {
                        "type": "array",
                        "description": "Command to execute"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace (default: homelab)",
                        "default": "homelab"
                    },
                    "container": {
                        "type": "string",
                        "description": "Container name within pod (optional)"
                    }
                }
            },
            "get_events": {
                "description": "Get Kubernetes events for monitoring",
                "parameters": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace (default: homelelab)",
                        "default": "homelab"
                    },
                    "kind": {
                        "type": "string",
                        "description": "Filter by resource kind (optional)"
                    },
                    "since": {
                        "type": "string",
                        "description": "Get events since timestamp (optional)"
                    }
                }
            },
            "get_cluster_info": {
                "description": "Get cluster-wide information and status",
                "parameters": {}
            }
        }


# Example usage
if __name__ == "__main__":
    # Create MCP tools instance
    mcp_tools = HomelabMCPTools()

    # Example: Get service status
    async def main():
        manager = HomelabMCPManager()

        # Get all services in homelab namespace
        status = await manager.get_service_status("homelab")
        print("Service Status:", json.dumps(status, indent=2))

        # Get resource usage
        usage = await manager.get_resource_usage("homelab")
        print("Resource Usage:", json.dumps(usage, indent=2))

        # Get cluster info
        cluster = await manager.get_cluster_info()
        print("Cluster Info:", json.dumps(cluster, indent=2))

    asyncio.run(main())