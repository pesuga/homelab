# This document contains a list of wishes for the home lab.

## Apps or services I wish to install

[ ] Plex Media Server
[ ] Graphana, prometheus and Loki
[x] NGINX Ingress Controller (implementation in progress)
[x] External-DNS for DDNS (implementation in progress)

## Tasks
[ ] Fix Home Automation
[x] Setup DDNS and enable the use of subdomains for app routing (implementation in progress)
[ ] Setup a reverse proxy for the apps (implementation in progress with NGINX Ingress)
[ ] Set up a dashboard in Glance
[ ] Configure Tailscale for subdomain support (see TAILSCALE_SUBDOMAIN_SETUP.md)
[ ] Migrate existing applications from path-based to subdomain-based routing

## Ideas
[ ] Implement cert-manager for automatic SSL certificate management
[ ] Configure monitoring and alerting for critical services