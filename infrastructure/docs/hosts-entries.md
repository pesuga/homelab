# Local Domain Setup for Homelab Services

Add these entries to your `/etc/hosts` file on each device where you want to access your services:

```
# Kubernetes Homelab Services
192.168.86.200 grafana.homelab.local
192.168.86.200 prometheus.homelab.local
192.168.86.200 loki.homelab.local
192.168.86.200 postgres.homelab.local
192.168.86.200 qdrant.homelab.local
192.168.86.200 homer.homelab.local
# Add more services as needed
```

On macOS/Linux, you can add these entries with:

```bash
sudo nano /etc/hosts
```

On Windows, edit `C:\Windows\System32\drivers\etc\hosts` as Administrator.
