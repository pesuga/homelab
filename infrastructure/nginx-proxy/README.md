# Nginx Reverse Proxy for Standard Port Access

This solution provides access to Kubernetes services using standard ports (80/443) by setting up an nginx reverse proxy on the host machine.

## Why This Approach

This approach offers several advantages over other methods:

1. **No Client-Side Configuration**: Unlike port-forwarding solutions, this approach doesn't require running commands on each client device.

2. **Standard Port Access**: Services are accessible on ports 80/443, providing a more natural browsing experience.

3. **Single Point of Configuration**: The proxy only needs to be set up once on the server.

4. **Compatible with All Devices**: Works with any device that can reach your server, without additional setup.

5. **Performance**: Direct proxy on the node offers better performance than tunneling solutions.

## How It Works

```
                  ┌────────────────────────────────────┐
                  │ Kubernetes Host Node (192.168.86.141) │
┌─────────┐       │                                    │       ┌──────────────┐
│         │       │  ┌─────────┐        ┌────────────┐ │       │              │
│ Client  │───────┼─▶│  Nginx  │───────▶│ Kubernetes │─┼───────▶│  Services    │
│ Devices │       │  │ (80/443)│        │ (NodePort) │ │       │              │
└─────────┘       │  └─────────┘        └────────────┘ │       └──────────────┘
                  │                                    │
                  └────────────────────────────────────┘
```

The nginx reverse proxy running on the host machine:
1. Listens on ports 80 and 443
2. Terminates TLS using the same certificates used in-cluster
3. Forwards requests to the appropriate Kubernetes service via NodePort

## Installation

1. Copy these scripts to your Kubernetes host node
2. Make them executable: `chmod +x install-nginx-proxy.sh uninstall-nginx-proxy.sh`
3. Run the installation script as root: `sudo ./install-nginx-proxy.sh`

## Client Setup

On client devices, ensure your `/etc/hosts` file contains:
```
192.168.86.141 grafana.homelab.local prometheus.homelab.local loki.homelab.local postgres.homelab.local qdrant.homelab.local
```

## Uninstallation

If needed, run the uninstall script:
```
sudo ./uninstall-nginx-proxy.sh
```

## Integration with Tailscale

If you're using Tailscale for remote access (as mentioned in your existing subnet router setup), this solution complements it perfectly. Local devices can use the nginx proxy, while remote devices can access services through Tailscale.
