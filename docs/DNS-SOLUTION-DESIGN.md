# 🌐 Homelab DNS Solution Design

**Created**: 2025-11-04
**Status**: Analysis & Design Phase

---

## 🎯 Problem Statement

**Current Issues:**
- DNS hostnames (`*.pesulabs.net`) don't resolve on Tailscale devices
- Ingress resources configured but unreachable via domain names
- `/etc/hosts` hacks needed on each device (not scalable)
- Multi-device access (laptop, mobile, compute node) requires consistent solution

**Current Setup:**
- Tailscale tailnet: `giglesias.ts.net`
- Service node (asuna): `100.81.76.55`
- Compute node (pesubuntu): `100.72.98.106`
- Traefik ingress controller with hostnames like `chat.homelab.pesulabs.net`
- Cloudflare manages `pesulabs.net` domain

---

## 📊 Solution Options Comparison

### Option 1: Tailscale MagicDNS + Split DNS ⭐ **RECOMMENDED**

**How It Works:**
1. Enable Tailscale MagicDNS (handles `*.ts.net` domains automatically)
2. Set up internal DNS server (CoreDNS) on K3s cluster
3. Configure Tailscale split DNS to forward `*.pesulabs.net` queries to CoreDNS
4. CoreDNS resolves to Tailscale IPs for tailnet clients

**Architecture:**
```
Tailnet Device → Tailscale MagicDNS
                      ↓
    pesulabs.net query? → Forward to CoreDNS (100.81.76.55:53)
                      ↓
    CoreDNS → Returns Tailscale IP (100.81.76.55)
                      ↓
    Device connects via Tailscale tunnel
```

**Pros:**
- ✅ No external dependencies (all on your tailnet)
- ✅ Works automatically on all Tailscale devices
- ✅ No `/etc/hosts` modifications needed
- ✅ Secure (DNS never leaves tailnet)
- ✅ Free
- ✅ Easy to maintain

**Cons:**
- ⚠️ Requires CoreDNS deployment on K3s
- ⚠️ Initial configuration needed

**Implementation Complexity**: Medium (2-3 hours)

---

### Option 2: Cloudflare DNS + Tailscale Wildcard

**How It Works:**
1. Create wildcard CNAME in Cloudflare: `*.pesulabs.net → asuna.giglesias.ts.net`
2. Rely on Tailscale MagicDNS to resolve `asuna.giglesias.ts.net` to `100.81.76.55`
3. Devices query public DNS, get CNAME, then Tailscale resolves final IP

**Architecture:**
```
Tailnet Device → Public DNS (Cloudflare)
                      ↓
    *.pesulabs.net → CNAME → asuna.giglesias.ts.net
                      ↓
    Tailscale MagicDNS → Returns 100.81.76.55
                      ↓
    Device connects via Tailscale tunnel
```

**Pros:**
- ✅ Simple DNS configuration (one wildcard record)
- ✅ No internal DNS server needed
- ✅ Works with MagicDNS out of the box

**Cons:**
- ❌ Exposes your Tailscale hostnames publicly in DNS
- ❌ Requires Cloudflare proxy OFF (DNS-only mode)
- ⚠️ Depends on external service (Cloudflare)

**Implementation Complexity**: Low (15 minutes)

---

### Option 3: Cloudflare Tunnel + DNS

**How It Works:**
1. Run Cloudflare Tunnel (cloudflared) on service node
2. Configure tunnels for each service
3. Cloudflare DNS points domains to tunnel
4. Traffic routes through Cloudflare edge

**Architecture:**
```
Tailnet Device → Cloudflare Edge
                      ↓
    *.pesulabs.net → Cloudflare Tunnel
                      ↓
    Service Node (via tunnel)
```

**Pros:**
- ✅ Full TLS/SSL management via Cloudflare
- ✅ DDoS protection and CDN benefits
- ✅ Access from non-Tailscale devices possible

**Cons:**
- ❌ All traffic goes through Cloudflare (latency, privacy concerns)
- ❌ Not truly "local" anymore
- ❌ Requires cloudflared daemon
- ❌ More complex than needed for internal-only services

**Implementation Complexity**: High (4-6 hours)

---

### Option 4: External-DNS + Cloudflare API

**How It Works:**
1. Deploy External-DNS in K8s cluster
2. External-DNS watches Ingress resources
3. Automatically creates/updates Cloudflare DNS records
4. DNS records point to Tailscale IPs

**Architecture:**
```
K8s Ingress Created
       ↓
External-DNS detects change
       ↓
Cloudflare API call → Creates A record
       ↓
*.pesulabs.net → 100.81.76.55 (Tailscale IP)
```

**Pros:**
- ✅ Fully automated DNS management
- ✅ Ingress changes auto-update DNS
- ✅ GitOps friendly

**Cons:**
- ⚠️ Exposes internal IPs in public DNS
- ⚠️ Requires Cloudflare API token
- ⚠️ More moving parts

**Implementation Complexity**: Medium (2-3 hours)

---

## 🏆 Recommended Solution: Tailscale MagicDNS + CoreDNS Split DNS

### Why This Solution?

1. **Privacy**: DNS queries never leave your tailnet
2. **Simplicity**: One-time setup, works everywhere
3. **Security**: Only Tailscale devices can resolve domains
4. **Cost**: $0 (uses existing infrastructure)
5. **Reliability**: No external dependencies
6. **Scalability**: Works for unlimited devices/services

### Implementation Plan

#### Phase 1: Deploy CoreDNS on K3s

**CoreDNS Deployment:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns-custom
  namespace: homelab
data:
  Corefile: |
    pesulabs.net:53 {
      log
      errors

      # All pesulabs.net services resolve to service node Tailscale IP
      template IN A pesulabs.net {
        match "^(.+)\\.pesulabs\\.net\\.$"
        answer "{{ .Name }} 60 IN A 100.81.76.55"
        fallthrough
      }

      # Serve zone file for specific overrides if needed
      file /etc/coredns/pesulabs.net.zone pesulabs.net

      # Forward anything we don't know to upstream
      forward . 1.1.1.1 8.8.8.8
    }

    # Catch-all for other queries
    .:53 {
      forward . 1.1.1.1 8.8.8.8
    }

---
apiVersion: v1
kind: Service
metadata:
  name: coredns-custom
  namespace: homelab
spec:
  selector:
    app: coredns-custom
  ports:
    - port: 53
      targetPort: 53
      protocol: UDP
      name: dns-udp
    - port: 53
      targetPort: 53
      protocol: TCP
      name: dns-tcp
  type: ClusterIP
  clusterIP: 10.43.0.53  # Fixed IP for easy reference

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coredns-custom
  namespace: homelab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: coredns-custom
  template:
    metadata:
      labels:
        app: coredns-custom
    spec:
      containers:
      - name: coredns
        image: coredns/coredns:1.11.1
        args: [ "-conf", "/etc/coredns/Corefile" ]
        volumeMounts:
        - name: config
          mountPath: /etc/coredns
        ports:
        - containerPort: 53
          protocol: UDP
          name: dns-udp
        - containerPort: 53
          protocol: TCP
          name: dns-tcp
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
      volumes:
      - name: config
        configMap:
          name: coredns-custom
```

#### Phase 2: Expose CoreDNS via NodePort

**NodePort Service for External Access:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: coredns-custom-external
  namespace: homelab
spec:
  selector:
    app: coredns-custom
  ports:
    - port: 53
      targetPort: 53
      nodePort: 30053
      protocol: UDP
      name: dns-udp
    - port: 53
      targetPort: 53
      nodePort: 30053
      protocol: TCP
      name: dns-tcp
  type: NodePort
```

#### Phase 3: Configure Tailscale Split DNS

**Via Tailscale Admin Console:**
1. Go to https://login.tailscale.com/admin/dns
2. Add nameserver:
   - Type: Custom
   - Address: `100.81.76.55:30053` (service node Tailscale IP + NodePort)
   - Restrict to search domain: `pesulabs.net`
3. Enable "Override local DNS"

**Result:**
- Queries for `*.pesulabs.net` → Forwarded to CoreDNS
- Queries for everything else → Normal DNS resolution
- All Tailscale devices automatically use this configuration

#### Phase 4: Test DNS Resolution

```bash
# From any Tailscale device
nslookup chat.homelab.pesulabs.net
# Should return: 100.81.76.55

# Test in browser
curl http://chat.homelab.pesulabs.net
# Should connect via Tailscale to LobeChat

# Mobile test
# Open browser on phone (connected to Tailscale)
# Navigate to: http://chat.homelab.pesulabs.net
# Should load LobeChat
```

---

## 📋 Alternative Quick Win: Simplified CoreDNS

**For immediate testing, simple wildcard resolution:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns-custom
  namespace: homelab
data:
  Corefile: |
    pesulabs.net:53 {
      log
      errors

      # Wildcard: everything under pesulabs.net → service node
      template IN A pesulabs.net {
        answer "{{ .Name }} 60 IN A 100.81.76.55"
      }
    }

    .:53 {
      forward . 1.1.1.1
    }
```

**Deploy:**
```bash
kubectl apply -f coredns-deployment.yaml
```

**Configure Tailscale:**
- Nameserver: `100.81.76.55:30053`
- Search domain: `pesulabs.net`

**Done!** All `*.pesulabs.net` queries resolve to your service node.

---

## 🔧 Maintenance & Operations

### Adding New Services

**With CoreDNS Template (Recommended):**
- No action needed! All `*.pesulabs.net` domains auto-resolve to `100.81.76.55`
- Just create Ingress with desired hostname
- Traefik routes based on Host header

**With Zone File (For Specific Overrides):**
```bash
# Edit zone file if you need specific IP overrides
kubectl edit configmap coredns-custom -n homelab

# Add to pesulabs.net.zone section:
# custom-service  IN  A  100.72.98.106  ; Points to compute node instead
```

### Troubleshooting

**DNS not resolving:**
```bash
# Check CoreDNS pod
kubectl logs -n homelab -l app=coredns-custom

# Test from within cluster
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup chat.pesulabs.net 10.43.0.53

# Check Tailscale DNS config
tailscale status
# Verify MagicDNS is enabled in web console
```

**Slow DNS queries:**
```bash
# Check CoreDNS resource usage
kubectl top pod -n homelab -l app=coredns-custom

# Increase replicas if needed
kubectl scale deployment coredns-custom -n homelab --replicas=2
```

---

## 🚀 Migration Path

### Week 1: Setup & Test
- ✅ Deploy CoreDNS to K3s
- ✅ Configure Tailscale split DNS
- ✅ Test from compute node and laptop
- ✅ Validate mobile access

### Week 2: Production Rollout
- ✅ Update documentation with new URLs
- ✅ Remove `/etc/hosts` hacks from all devices
- ✅ Monitor DNS query logs for issues
- ✅ Create monitoring alerts

### Week 3: Optimization
- ✅ Fine-tune CoreDNS caching
- ✅ Add specific domain overrides if needed
- ✅ Document service DNS patterns

---

## 📈 Benefits Summary

**Before:**
- ❌ Manual `/etc/hosts` on every device
- ❌ Breaks when IPs change
- ❌ Doesn't work on mobile
- ❌ No automation

**After:**
- ✅ Automatic DNS on all Tailscale devices
- ✅ Works on desktop, laptop, mobile
- ✅ IPs managed centrally
- ✅ New services auto-work
- ✅ GitOps compatible

---

## 🎓 Learning Resources

- [Tailscale MagicDNS Docs](https://tailscale.com/kb/1081/magicdns)
- [Tailscale Split DNS Guide](https://tailscale.com/kb/1054/dns)
- [CoreDNS Documentation](https://coredns.io/manual/toc/)
- [K3s CoreDNS Customization](https://docs.k3s.io/networking#coredns)

---

## 💡 Next Steps

1. **Decide on solution**: Tailscale MagicDNS + CoreDNS (recommended)
2. **Deploy CoreDNS**: Apply Kubernetes manifests
3. **Configure Tailscale**: Add split DNS nameserver
4. **Test thoroughly**: All devices, all services
5. **Document**: Update service endpoint documentation
6. **Monitor**: Watch DNS query logs for patterns

---

**Status**: Ready for implementation
**Estimated Time**: 2-3 hours for complete setup
**Risk Level**: Low (easily reversible)
