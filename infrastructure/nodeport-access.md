# Accessing Homelab Services via NodePort

## Step 1: Host File Configuration
Add these entries to your `/etc/hosts` file:
```
192.168.86.141 grafana.homelab.local prometheus.homelab.local loki.homelab.local postgres.homelab.local qdrant.homelab.local
```

## Step 2: Service Access URLs
Use these URLs to access your services:

| Service    | HTTP URL                                    | HTTPS URL                                     |
|------------|---------------------------------------------|-----------------------------------------------|
| Grafana    | http://grafana.homelab.local:32737          | https://grafana.homelab.local:32720           |
| Prometheus | http://prometheus.homelab.local:32737       | https://prometheus.homelab.local:32720        |
| Loki       | http://loki.homelab.local:32737             | https://loki.homelab.local:32720              |
| PostgreSQL | http://postgres.homelab.local:32737         | https://postgres.homelab.local:32720          |
| Qdrant     | http://qdrant.homelab.local:32737           | https://qdrant.homelab.local:32720            |

## Step 3: Certificate Trust (One-time setup)
Import the generated CA certificate to trust the TLS connections:
```
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /tmp/homelab-certs/homelab-ca.crt
```

## Notes
- HTTP URLs will redirect to HTTPS automatically
- The NodePorts might change if the ingress-nginx-controller pod restarts
  - If you can't access services, run: `kubectl get svc ingress-nginx-controller -n ingress-nginx` to check current ports
