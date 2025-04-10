# Homelab Infrastructure Documentation

## Local Domain Access Solution

This documentation covers the local domain access solution implemented for the homelab Kubernetes cluster.

### Components

1. **MetalLB** - Provides LoadBalancer capability for bare-metal clusters
   - Allocated IP Range: 192.168.86.200-192.168.86.210
   - Configuration: `/infrastructure/metallb/`

2. **NGINX Ingress Controller** - HTTP/HTTPS routing and traffic control
   - External IP: 192.168.86.200
   - Configuration: `/infrastructure/ingress-nginx/`

3. **Service Ingress Definitions** - Routing rules for individual services
   - Configuration: `/infrastructure/ingress/`

### Accessing Services

All services are accessible via `[service-name].homelab.local` domains pointing to 192.168.86.200.

#### Available Services

| Service    | URL                        | Internal IP     | Port |
|------------|----------------------------|-----------------|------|
| Grafana    | grafana.homelab.local      | 10.43.56.28     | 3000 |
| Prometheus | prometheus.homelab.local   | 10.43.184.103   | 9090 |
| Loki       | loki.homelab.local         | 10.43.81.86     | 3100 |
| PostgreSQL | postgres.homelab.local     | 10.43.186.130   | 5432 |
| Qdrant     | qdrant.homelab.local       | 10.43.210.80    | 6333 |

### Local DNS Setup Options

#### Option 1: Hosts File (Simplest)

Add entries to your `/etc/hosts` file:

```
192.168.86.200 grafana.homelab.local
192.168.86.200 prometheus.homelab.local
192.168.86.200 loki.homelab.local
192.168.86.200 postgres.homelab.local
192.168.86.200 qdrant.homelab.local
```

#### Option 2: Local DNS Server (Advanced)

Use the CoreDNS configuration provided in `/infrastructure/dns/coredns.yaml` for automatic DNS resolution across your network.

### Testing the Setup

Once the hosts file entries are added, you can access your services using local domain names:

1. http://grafana.homelab.local
2. http://prometheus.homelab.local
3. http://loki.homelab.local

### Maintenance

#### Adding New Services

To add a new service to the local domain access solution:

1. Create an ingress definition in `/infrastructure/ingress/`
2. Add the domain to your hosts file or DNS server
3. Apply the configuration with `kubectl apply -f /path/to/ingress-definition.yaml`

#### Troubleshooting

If you encounter issues with the access solution:

1. Verify the ingress controller is running: `kubectl get pods -n ingress-nginx`
2. Check that MetalLB is working: `kubectl get pods -n metallb-system`
3. Verify the service is accessible from within the cluster: `kubectl exec -it [any-pod] -- curl [service-ip]:[port]`
4. Check ingress rules: `kubectl get ingress -A`
