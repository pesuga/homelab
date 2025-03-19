# This document contains a list of wishes for the home lab.

## Apps or services I wish to install

[*] Plex Media Server
   - [x] Deploy Plex server on Kubernetes
   - [x] Configure storage for media library
   - [x] Set up subdomain (plex.app.pesulabs.net)
[*] Monitoring Stack:
   - [x] Grafana for visualization
   - [x] Prometheus for metrics collection
   - [x] Loki for log aggregation
   - [x] Create custom dashboards for system monitoring
[x] NGINX Ingress Controller
[x] External-DNS for DDNS
[x] Cert-manager for SSL certificates
[*] Qdrant Vector Database:
   - [x] Deploy Qdrant on Kubernetes
   - [x] Configure persistent storage
   - [x] Set up subdomain (qdrant.app.pesulabs.net)
   - [x] Create documentation for usage
[ ] Fix login issues for Immich tomorrow

## Tasks
[x] Fix Home Automation
[*] Fix Immich service - not working (404 error)
   - [x] Updated middleware configuration to use correct port (2283)
   - [x] Simplified ingress configuration by removing problematic middleware CRDs
   - [x] Web interface loads but login doesn't work
   - [ ] Fix login issues and determine admin credentials
   - [x] Create missing ingress.yaml file (currently defined in middleware.yaml)
   - [x] Update kustomization.yaml to remove reference to non-existent ingress.yaml
   - [x] Fix 404 error (confirmed with curl -k -H "Host: immich.app.pesulabs.net" https://192.168.86.141/)
   - [x] Troubleshooting: Removed middleware references from ingress.yaml and deleted middleware resources
   - [x] Web interface is now accessible, but returns a 404 for the root path in HEAD requests
[*] Fix Plex Media Server
   - [x] Deploy Plex server on Kubernetes
   - [x] Configure storage for media library
   - [x] Set up subdomain (plex.app.pesulabs.net)
   - [x] Create kustomization.yaml file to properly deploy all Plex resources
   - [x] Fix DNS resolution issue
   - [x] Verify ingress configuration is using the correct ingress class
   - [x] Plex is now working (returns 401 Unauthorized which is expected without authentication)
[*] Implement monitoring infrastructure:
   - [x] Deploy Prometheus for metrics collection
   - [x] Deploy Loki for log aggregation
   - [x] Set up Grafana with datasources for Prometheus and Loki
   - [x] Create dashboards for:
      - [x] Kubernetes cluster health
      - [x] Application performance metrics
      - [x] Resource utilization (CPU, memory)
      - [x] Network traffic monitoring
   - [x] Create kustomization.yaml file for monitoring stack
   - [x] Fix DNS resolution issues for monitoring tools
   - [x] Test access to monitoring tools:
      - [x] Grafana is working (returns 302 redirect to /login)
      - [x] Prometheus is working (returns 405 Method Not Allowed for HEAD request, which is expected)
[x] Setup DDNS and enable the use of subdomains for app routing
[x] Setup a reverse proxy for the apps (NGINX Ingress)
[x] Set up a dashboard in Glance
   - [x] Glance is working (returns 200 OK)
[x] Configure Tailscale for subdomain support (see TAILSCALE_SUBDOMAIN_SETUP.md)
[x] Set up subdomain routing for applications:
   - [x] Immich (needs fixing - 404 error)
   - [x] Home Assistant (working - returns 405 Method Not Allowed for HEAD request, which is expected)
   - [x] N8N (working - returns 200 OK)
   - [x] OwnCloud (working - returns 302 redirect to /login)
   - [x] Glance (working - returns 200 OK)
   - [x] Grafana (working - returns 302 redirect to /login)
   - [x] Prometheus (working - returns 405 Method Not Allowed for HEAD request, which is expected)
   - [x] Plex (working - returns 401 Unauthorized, which is expected)
[*] Configure Home Assistant for add-ons support
   - [ ] Research and implement solution for running add-ons in Kubernetes environment
   - [ ] Set up persistent storage for Home Assistant configuration
   - [ ] Configure trusted proxies in Home Assistant configuration.yaml
   - [ ] Set up separate deployments for commonly used add-ons (Zigbee2MQTT, etc.)
[x] Fix DNS resolution issues
   - [x] Update scripts/add-manual-dns-records.sh to include missing services:
      - [x] plex.app.pesulabs.net
      - [x] grafana.app.pesulabs.net
      - [x] prometheus.app.pesulabs.net
   - [x] Run the updated script to add the DNS records to Cloudflare
      - [x] Command: `./scripts/add-manual-dns-records.sh <cloudflare-api-token> <zone-id> <server-ip>`
      - [x] You can find your zone ID in the Cloudflare dashboard -> Domain Overview -> API section
   - [x] Verify DNS resolution for all services
      - [x] Test with: `curl -k -I -H "Host: plex.app.pesulabs.net" https://192.168.86.141` - Working (401)
      - [x] Test with: `curl -k -I -H "Host: grafana.app.pesulabs.net" https://192.168.86.141` - Working (302)
      - [x] Test with: `curl -k -I -H "Host: prometheus.app.pesulabs.net" https://192.168.86.141` - Working (405)
      - [x] Test with: `curl -k -I -H "Host: immich.app.pesulabs.net" https://192.168.86.141` - Not working (404)
[x] Implement better security for home network access only
   - [x] Create a local DNS setup script
     - [x] Set up a local DNS server (Pi-hole or dnsmasq) on the home network
     - [x] Configure it to resolve *.app.pesulabs.net domains to the internal cluster IP (192.168.86.141)
   - [x] Remove public DNS records from Cloudflare
     - [x] Create a script to delete DNS records from Cloudflare
     - [x] Keep the script for reference if public access is needed in the future
   - [x] Enhance Tailscale integration for secure remote access
     - [x] Configure Tailscale to provide access to internal services
     - [x] Test remote access through Tailscale VPN
   - [x] Verify router configuration
     - [x] Ensure no port forwarding is enabled for ports 80/443 to the cluster
     - [x] Document network security measures

## Ongoing Improvements
[ ] Fine-tune NGINX configurations for optimal performance
[*] Set up monitoring and alerting for critical services
   - [x] Deploy monitoring stack
   - [x] Configure Grafana dashboard for system and application monitoring
   - [ ] Configure alerts for critical services
[ ] Implement automated backup solutions for application data
[*] Create documentation for each service and monitoring setup
   - [x] Monitoring stack documentation
   - [x] Plex documentation
[x] Implement better security for home network access only
   - [x] Create a local DNS setup script
     - [x] Set up a local DNS server (Pi-hole or dnsmasq) on the home network
     - [x] Configure it to resolve *.app.pesulabs.net domains to the internal cluster IP (192.168.86.141)
   - [x] Remove public DNS records from Cloudflare
     - [x] Create a script to delete DNS records from Cloudflare
     - [x] Keep the script for reference if public access is needed in the future
   - [x] Enhance Tailscale integration for secure remote access
     - [x] Configure Tailscale to provide access to internal services
     - [x] Test remote access through Tailscale VPN
   - [x] Verify router configuration
     - [x] Ensure no port forwarding is enabled for ports 80/443 to the cluster
     - [x] Document network security measures
