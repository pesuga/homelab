#!/usr/bin/env python3
"""
Prometheus Exporter for AMD ROCm GPU Metrics
Exposes GPU utilization, memory, temperature, and power metrics
"""

import subprocess
import re
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Configuration
EXPORTER_PORT = 9101
SCRAPE_INTERVAL = 5  # seconds


class ROCmMetrics:
    """Collect metrics from rocm-smi"""

    def __init__(self):
        self.metrics = {}

    def collect(self):
        """Collect all GPU metrics"""
        try:
            # Get GPU usage
            usage_output = subprocess.check_output(
                ["rocm-smi", "--showuse"],
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self._parse_usage(usage_output)

            # Get memory info
            mem_output = subprocess.check_output(
                ["rocm-smi", "--showmeminfo", "vram"],
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self._parse_memory(mem_output)

            # Get temperature
            temp_output = subprocess.check_output(
                ["rocm-smi", "--showtemp"],
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self._parse_temperature(temp_output)

            # Get power consumption
            power_output = subprocess.check_output(
                ["rocm-smi", "--showpower"],
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self._parse_power(power_output)

        except subprocess.CalledProcessError as e:
            print(f"Error running rocm-smi: {e}")
        except FileNotFoundError:
            print("rocm-smi not found. Is ROCm installed?")

        return self.metrics

    def _parse_usage(self, output):
        """Parse GPU usage from rocm-smi output"""
        # Look for GPU usage percentage
        # Example: "GPU use (%): 45"
        match = re.search(r"GPU use \(%\):\s+(\d+)", output)
        if match:
            self.metrics["gpu_utilization_percent"] = float(match.group(1))

    def _parse_memory(self, output):
        """Parse VRAM usage from rocm-smi output"""
        # Look for memory usage
        # Example: "VRAM Total Memory (B): 17163091968"
        # Example: "VRAM Total Used Memory (B): 1073741824"
        total_match = re.search(r"VRAM Total Memory \(B\):\s+(\d+)", output)
        used_match = re.search(r"VRAM Total Used Memory \(B\):\s+(\d+)", output)

        if total_match:
            total_bytes = float(total_match.group(1))
            self.metrics["gpu_memory_total_bytes"] = total_bytes
            self.metrics["gpu_memory_total_gb"] = total_bytes / (1024**3)

        if used_match:
            used_bytes = float(used_match.group(1))
            self.metrics["gpu_memory_used_bytes"] = used_bytes
            self.metrics["gpu_memory_used_gb"] = used_bytes / (1024**3)

        if total_match and used_match:
            total = float(total_match.group(1))
            used = float(used_match.group(1))
            self.metrics["gpu_memory_utilization_percent"] = (used / total) * 100

    def _parse_temperature(self, output):
        """Parse GPU temperature from rocm-smi output"""
        # Look for temperature
        # Example: "Temperature (Sensor edge) (C): 45.0"
        match = re.search(r"Temperature \(Sensor edge\) \(C\):\s+([\d.]+)", output)
        if match:
            self.metrics["gpu_temperature_celsius"] = float(match.group(1))

    def _parse_power(self, output):
        """Parse power consumption from rocm-smi output"""
        # Look for power usage
        # Example: "Average Graphics Package Power (W): 125.0"
        match = re.search(r"Average Graphics Package Power \(W\):\s+([\d.]+)", output)
        if match:
            self.metrics["gpu_power_watts"] = float(match.group(1))


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint"""

    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-type", "text/plain; version=0.0.4")
            self.end_headers()

            # Collect metrics
            collector = ROCmMetrics()
            metrics = collector.collect()

            # Format as Prometheus metrics
            output = self._format_prometheus(metrics)
            self.wfile.write(output.encode())

        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def _format_prometheus(self, metrics):
        """Format metrics in Prometheus exposition format"""
        output = []
        output.append("# HELP rocm_gpu_utilization_percent GPU utilization percentage")
        output.append("# TYPE rocm_gpu_utilization_percent gauge")
        if "gpu_utilization_percent" in metrics:
            output.append(f"rocm_gpu_utilization_percent {metrics['gpu_utilization_percent']}")

        output.append("# HELP rocm_gpu_memory_total_bytes Total GPU memory in bytes")
        output.append("# TYPE rocm_gpu_memory_total_bytes gauge")
        if "gpu_memory_total_bytes" in metrics:
            output.append(f"rocm_gpu_memory_total_bytes {metrics['gpu_memory_total_bytes']}")

        output.append("# HELP rocm_gpu_memory_used_bytes Used GPU memory in bytes")
        output.append("# TYPE rocm_gpu_memory_used_bytes gauge")
        if "gpu_memory_used_bytes" in metrics:
            output.append(f"rocm_gpu_memory_used_bytes {metrics['gpu_memory_used_bytes']}")

        output.append("# HELP rocm_gpu_memory_utilization_percent GPU memory utilization percentage")
        output.append("# TYPE rocm_gpu_memory_utilization_percent gauge")
        if "gpu_memory_utilization_percent" in metrics:
            output.append(f"rocm_gpu_memory_utilization_percent {metrics['gpu_memory_utilization_percent']}")

        output.append("# HELP rocm_gpu_temperature_celsius GPU temperature in Celsius")
        output.append("# TYPE rocm_gpu_temperature_celsius gauge")
        if "gpu_temperature_celsius" in metrics:
            output.append(f"rocm_gpu_temperature_celsius {metrics['gpu_temperature_celsius']}")

        output.append("# HELP rocm_gpu_power_watts GPU power consumption in watts")
        output.append("# TYPE rocm_gpu_power_watts gauge")
        if "gpu_power_watts" in metrics:
            output.append(f"rocm_gpu_power_watts {metrics['gpu_power_watts']}")

        return "\n".join(output) + "\n"

    def log_message(self, format, *args):
        """Override to reduce verbosity"""
        pass  # Silent mode


def main():
    """Start the Prometheus exporter"""
    print(f"Starting ROCm Prometheus Exporter on port {EXPORTER_PORT}")
    print(f"Metrics available at http://localhost:{EXPORTER_PORT}/metrics")
    print(f"Health check at http://localhost:{EXPORTER_PORT}/health")

    server = HTTPServer(("0.0.0.0", EXPORTER_PORT), MetricsHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down exporter...")
        server.shutdown()


if __name__ == "__main__":
    main()
