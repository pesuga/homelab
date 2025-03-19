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

## Tasks
[x] Fix Home Automation
[*] Fix Immich service - not working (404 error)
   - [x] Updated middleware configuration to use correct port (2283)
   - [x] Simplified ingress configuration by removing problematic middleware CRDs
   - [x] Web interface loads but login doesn't work
   - [ ] Fix login issues and determine admin credentials
   - [x] Create missing ingress.yaml file (currently defined in middleware.yaml)
   - [x] Update kustomization.yaml to remove reference to non-existent ingress.yaml
   - [ ] Fix 404 error (confirmed with curl -I https://immich.app.pesulabs.net)
[*] Fix Plex Media Server - not working (DNS resolution issue)
   - [x] Deploy Plex server on Kubernetes
   - [x] Configure storage for media library
   - [x] Set up subdomain (plex.app.pesulabs.net)
   - [x] Create kustomization.yaml file to properly deploy all Plex resources
   - [ ] Fix DNS resolution issue (curl: (6) Could not resolve host: plex.app.pesulabs.net)
   - [x] Verify ingress configuration is using the correct ingress class
   - [ ] Note: Plex pod is running but ingress has no ADDRESS assigned
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
   - [ ] Fix DNS resolution issues for monitoring tools (curl: (6) Could not resolve host)
   - [ ] Test access to monitoring tools at grafana.app.pesulabs.net and prometheus.app.pesulabs.net
   - [ ] Note: Monitoring pods are running but DNS resolution is failing
[x] Setup DDNS and enable the use of subdomains for app routing
[x] Setup a reverse proxy for the apps (NGINX Ingress)
[x] Set up a dashboard in Glance
[x] Configure Tailscale for subdomain support (see TAILSCALE_SUBDOMAIN_SETUP.md)
[x] Set up subdomain routing for applications:
   - [x] Immich
   - [x] Home Assistant
   - [x] N8N
   - [x] OwnCloud
   - [x] Glance
   - [x] Grafana (grafana.app.pesulabs.net)
   - [x] Prometheus (prometheus.app.pesulabs.net)
   - [x] Plex (plex.app.pesulabs.net)
[*] Configure Home Assistant for add-ons support
   - [ ] Research and implement solution for running add-ons in Kubernetes environment
   - [ ] Set up persistent storage for Home Assistant configuration
   - [ ] Configure trusted proxies in Home Assistant configuration.yaml
   - [ ] Set up separate deployments for commonly used add-ons (Zigbee2MQTT, etc.)
[*] Fix DNS resolution issues
   - [x] Update scripts/add-manual-dns-records.sh to include missing services:
      - [x] plex.app.pesulabs.net
      - [x] grafana.app.pesulabs.net
      - [x] prometheus.app.pesulabs.net
   - [ ] Run the updated script to add the DNS records to Cloudflare
   - [ ] Verify DNS resolution for all services
[ ] Fix login issues for Immich tomorrow

## Ongoing Improvements
[ ] Fine-tune NGINX configurations for optimal performance
[*] Set up monitoring and alerting for critical services
   - [x] Deploy monitoring stack
   - [ ] Configure alerts for critical services
[ ] Implement automated backup solutions for application data
[*] Create documentation for each service and monitoring setup
   - [x] Monitoring stack documentation
   - [x] Plex documentation
