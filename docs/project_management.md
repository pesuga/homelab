# Homelab Project Management

This document serves as the central hub for tracking tasks, issues, and future enhancements for the homelab infrastructure.

## Current Tasks

### High Priority
- [ ] Fix Promtail and Loki integration
  - [ ] Troubleshoot Promtail configuration to ensure logs are being collected
  - [ ] Verify Loki is receiving logs from Promtail
  - [ ] Confirm logs are visible in Grafana
- [ ] Configure Immich for mobile device access
  - [ ] Verify networking and DNS setup for external access
  - [ ] Test connectivity from mobile app
  - [ ] Document mobile setup process
- [x] Create Glance dashboard for service monitoring
  - [x] Add uptime checks for all services
  - [x] Configure visual indicators for service status
  - [x] Set up bookmarks for quick service access
  - [x] Configure weather widget for local conditions

### Medium Priority
- [ ] Implement automated backup solutions for application data
- [ ] Fine-tune NGINX configurations for optimal performance
- [ ] Configure alerts for critical services in Grafana
- [ ] Research and implement solution for running Home Assistant add-ons in Kubernetes

### Low Priority
- [ ] Explore additional security hardening measures
- [ ] Set up a development/staging environment for testing changes
- [ ] Implement resource quotas and limits for all applications

## Completed Tasks

### Infrastructure
- [x] Set up K3s cluster
- [x] Configure Flux CD for GitOps
- [x] Implement NGINX Ingress Controller
- [x] Set up External-DNS for DDNS
- [x] Configure Cert-manager for SSL certificates
- [x] Set up subdomain routing for all applications
- [x] Configure Tailscale for secure remote access
- [x] Implement better security for home network access only

### Applications
- [x] Deploy and configure Plex Media Server
- [x] Set up Monitoring Stack (Grafana, Prometheus, Loki)
- [x] Deploy and configure Immich (photo management)
- [x] Set up Home Assistant
- [x] Deploy N8N workflow automation
- [x] Configure OwnCloud file storage
- [x] Set up Glance dashboard
- [x] Deploy Qdrant Vector Database

## Future Enhancements

### Infrastructure Improvements
- [ ] Implement multi-node cluster for high availability
- [ ] Set up network policy enforcement
- [ ] Explore GitOps workflow improvements
- [ ] Implement progressive delivery with Flagger

### New Applications to Consider
- [ ] Paperless-ngx for document management
- [ ] Frigate NVR for camera management
- [ ] Jellyfin as an alternative to Plex
- [ ] Photoprism as an alternative to Immich
- [ ] Home automation expansion (Zigbee/Z-Wave integration)

## Issues Tracking

### Open Issues
- [ ] Promtail not sending logs to Loki
- [ ] Immich mobile app connectivity issues
- [ ] DNS resolution issue for qdrant.app.pesulabs.net (workaround: using internal service IP)

### Resolved Issues
- [x] Fixed DNS resolution issues
- [x] Resolved Immich 404 error
- [x] Fixed Plex Media Server configuration
- [x] Fixed Prometheus OOMKilled errors by increasing memory limits
- [x] Improved Glance dashboard service status detection
