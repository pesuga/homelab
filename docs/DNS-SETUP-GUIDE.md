# 🌐 DNS Setup for Tailscale Devices

## Overview

This guide explains how to make homelab domains accessible from all devices on your Tailscale network.

---

## 📋 Quick Comparison

| Method | Effort | Centralized | Auto-Updates | Best For |
|--------|--------|-------------|--------------|----------|
| **Manual /etc/hosts** | Low per device | ❌ | ❌ | Testing |
| **Tailscale MagicDNS** | Low (one-time) | ✅ | ✅ | Small tailnets |
| **Local DNS Server** | Medium (setup) | ✅ | ✅ | Learning/Control |

---

## 🎯 **Recommended: Tailscale MagicDNS with Global Nameservers**

### Setup Steps

**Important**: Tailscale MagicDNS is the simplest solution that requires ZERO per-device configuration. All DNS records are managed centrally in the Tailscale admin console.

1. **Enable MagicDNS**:
   - Go to: https://login.tailscale.com/admin/dns
   - Toggle "MagicDNS" ON
   - This enables automatic DNS for all Tailscale devices

2. **Add DNS Records** (Global Nameservers):
   - Still on the DNS page (https://login.tailscale.com/admin/dns)
   - Scroll to "Global Nameservers" section
   - Add the following DNS records:
     ```
     grafana.homelab.local     → 100.81.76.55
     prometheus.homelab.local  → 100.81.76.55
     n8n.homelab.local        → 100.81.76.55
     webui.homelab.local      → 100.81.76.55
     ```
   - **Alternative**: Use "Split DNS" to forward all `*.homelab.local` queries to a custom DNS server (requires setting up DNS server first)

3. **Test from ANY Tailscale Device**:
   ```bash
   # On any device connected to Tailscale
   nslookup grafana.homelab.local
   # Should resolve to 100.81.76.55

   # Test HTTPS access
   curl -I https://grafana.homelab.local
   # Should get HTTP/2 200 response
   ```

**That's it!** No client-side configuration needed. All devices on your Tailnet will automatically resolve homelab domains.

---

## 🔧 **Option: Deploy CoreDNS on K3s**

Deploy a DNS server in your K3s cluster to serve homelab domains.

### 1. Create CoreDNS ConfigMap

Create: `/home/pesu/Rakuflow/systems/homelab/infrastructure/kubernetes/dns/coredns-custom.yaml`

```yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns-custom
  namespace: kube-system
data:
  homelab.server: |
    homelab.local:53 {
        errors
        cache 30
        forward . 1.1.1.1 9.9.9.9
        hosts {
            100.81.76.55 grafana.homelab.local
            100.81.76.55 prometheus.homelab.local
            100.81.76.55 n8n.homelab.local
            100.81.76.55 webui.homelab.local
            fallthrough
        }
    }
```

### 2. Apply Configuration

```bash
ssh pesu@192.168.8.185 "kubectl apply -f - << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns-custom
  namespace: kube-system
data:
  homelab.server: |
    homelab.local:53 {
        errors
        cache 30
        forward . 1.1.1.1 9.9.9.9
        hosts {
            100.81.76.55 grafana.homelab.local
            100.81.76.55 prometheus.homelab.local
            100.81.76.55 n8n.homelab.local
            100.81.76.55 webui.homelab.local
            fallthrough
        }
    }
EOF
"
```

### 3. Restart CoreDNS

```bash
ssh pesu@192.168.8.185 "kubectl rollout restart deployment/coredns -n kube-system"
```

### 4. Expose CoreDNS on Tailscale

```bash
# On service node
sudo tailscale up --advertise-exit-node --accept-dns=true
```

### 5. Configure Clients

On each Tailscale device:

**Linux**:
```bash
# Add to /etc/resolv.conf (or use NetworkManager)
echo "nameserver 100.81.76.55" | sudo tee /etc/resolv.conf.d/tailscale
```

**macOS**:
```bash
# System Preferences → Network → Advanced → DNS
# Add DNS Server: 100.81.76.55
```

**Windows**:
- Network Settings → Change adapter options
- Tailscale adapter → Properties → IPv4 → DNS
- Add: 100.81.76.55

---

## 🏠 **Alternative: Pihole DNS (Advanced)**

For ad-blocking + DNS in one solution.

### 1. Deploy Pihole on Service Node

```bash
ssh pesu@192.168.8.185

# Create Pihole deployment
kubectl apply -f - << EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pihole-data
  namespace: homelab
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: local-path
  resources:
    requests:
      storage: 2Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pihole
  namespace: homelab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pihole
  template:
    metadata:
      labels:
        app: pihole
    spec:
      containers:
        - name: pihole
          image: pihole/pihole:latest
          env:
            - name: TZ
              value: "America/New_York"
            - name: WEBPASSWORD
              value: "admin123"
          ports:
            - containerPort: 80
              name: web
            - containerPort: 53
              name: dns-tcp
              protocol: TCP
            - containerPort: 53
              name: dns-udp
              protocol: UDP
          volumeMounts:
            - name: pihole-data
              mountPath: /etc/pihole
      volumes:
        - name: pihole-data
          persistentVolumeClaim:
            claimName: pihole-data
---
apiVersion: v1
kind: Service
metadata:
  name: pihole
  namespace: homelab
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30053
      name: web
    - port: 53
      targetPort: 53
      protocol: TCP
      name: dns-tcp
    - port: 53
      targetPort: 53
      protocol: UDP
      name: dns-udp
  selector:
    app: pihole
EOF
```

### 2. Configure Pihole

1. Access web UI: http://192.168.8.185:30053/admin
2. Login: admin / admin123
3. Go to: Local DNS → DNS Records
4. Add:
   ```
   grafana.homelab.local    → 100.81.76.55
   prometheus.homelab.local → 100.81.76.55
   n8n.homelab.local       → 100.81.76.55
   webui.homelab.local     → 100.81.76.55
   ```

### 3. Use Pihole as DNS

Set DNS on Tailscale devices to: `100.81.76.55` (port 53)

---

## 📱 **Quick Setup for Each Device**

### Your Devices

Based on your Tailscale network:

1. **pesubuntu** (compute) - ✅ Already configured
2. **asuna** (service) - ✅ Already configured
3. **pesu-mobile** (Android) - Needs setup
4. **pesu-stensul** (macOS) - Needs setup
5. **pesutop** (Windows) - Needs setup

### Android (pesu-mobile)

**Option 1: Hosts file** (requires root)
```bash
# Connect via Termux or adb
adb shell
su
echo "100.81.76.55 grafana.homelab.local prometheus.homelab.local n8n.homelab.local webui.homelab.local" >> /system/etc/hosts
```

**Option 2: Use IP directly**
- Just access via IP: https://100.81.76.55
- Certificate warning expected (can install Root CA)

### macOS (pesu-stensul)

```bash
# Add to hosts file
echo "100.81.76.55  grafana.homelab.local prometheus.homelab.local n8n.homelab.local webui.homelab.local" | sudo tee -a /etc/hosts

# Install Root CA
# 1. Copy ca-cert.pem from compute node
scp pesu@100.72.98.106:~/Rakuflow/systems/homelab/infrastructure/certificates/ca/ca-cert.pem ~/
# 2. Double-click to add to Keychain
# 3. Open Keychain Access → Find certificate → Trust → Always Trust
```

### Windows (pesutop)

```powershell
# Run PowerShell as Administrator

# Add to hosts file
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "100.81.76.55  grafana.homelab.local prometheus.homelab.local n8n.homelab.local webui.homelab.local"

# Install Root CA
# 1. Copy ca-cert.pem from compute node
# 2. Run: certutil -addstore -f "ROOT" ca-cert.pem
```

---

## 🔍 **Testing DNS Resolution**

On any device:

```bash
# Test DNS lookup
nslookup grafana.homelab.local

# Test HTTPS access
curl -I https://grafana.homelab.local

# Test in browser
# Open: https://grafana.homelab.local
```

---

## 📊 **Recommendation Matrix**

| Your Situation | Best Solution |
|----------------|---------------|
| 1-3 devices | Manual /etc/hosts |
| 4-10 devices | Tailscale MagicDNS |
| 10+ devices | Local DNS (Pihole/CoreDNS) |
| Want ad-blocking | Pihole |
| Want simplicity | Tailscale MagicDNS |
| Want full control | CoreDNS on K3s |
| Learning DNS | Pihole or CoreDNS |

---

## 🎯 **Recommended for You**

Given your 5 devices, I recommend:

1. **Start with**: Tailscale MagicDNS
   - Enable in web console
   - Automatic for all devices
   - Zero per-device configuration

2. **If you want more control**: Deploy Pihole
   - Adds ad-blocking
   - Local DNS server
   - Great learning experience
   - Web UI for management

3. **For now**: Manual /etc/hosts on active devices
   - Quick to test
   - Works immediately
   - Upgrade later

---

## 🚀 **Quick Start Script**

Want me to create a script that:
1. Detects which Tailscale devices are online
2. SSH to each and configure hosts file
3. Copies and installs Root CA

Let me know and I can automate this for you!

---

## 📚 **Additional Resources**

- **Tailscale MagicDNS**: https://tailscale.com/kb/1081/magicdns/
- **CoreDNS**: https://coredns.io/
- **Pihole**: https://pi-hole.net/
- **DNS over HTTPS**: https://developers.cloudflare.com/1.1.1.1/

---

**Next Steps**: Choose your DNS strategy and I'll help you implement it!
