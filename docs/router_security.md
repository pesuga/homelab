# Router Security Configuration

This document outlines the steps to verify and configure your router for secure homelab operation.

## Overview

To ensure your homelab services are only accessible from your local network (and optionally through Tailscale for remote access), you need to properly configure your router. This includes:

1. Disabling port forwarding for services that should not be publicly accessible
2. Configuring firewall rules to block unwanted incoming traffic
3. Documenting your network security measures

## Verification Steps

### 1. Check Port Forwarding Rules

Most routers have a "Port Forwarding" or "Virtual Server" section in their admin interface. Check for any rules that forward ports 80 or 443 (HTTP/HTTPS) to your Kubernetes cluster.

1. Log in to your router's admin interface (typically http://192.168.1.1 or similar)
2. Navigate to the port forwarding section
3. Look for any rules forwarding ports 80, 443, or other service ports to your cluster's IP (192.168.86.141)
4. Remove any port forwarding rules for services that should not be publicly accessible

### 2. Verify Firewall Settings

1. Navigate to your router's firewall settings
2. Ensure that incoming connections are blocked by default
3. Add exceptions only for services that need to be accessible from the internet

### 3. Test External Access

To verify that your services are not accessible from the internet:

1. Disconnect from your home network (use mobile data or another external network)
2. Try to access your services using their domain names:
   ```
   curl -I https://immich.app.pesulabs.net
   curl -I https://plex.app.pesulabs.net
   ```
3. These requests should fail if your services are properly secured

## Documentation Template

Use this template to document your network security configuration:

```
# Network Security Documentation

## Router Information
- Model: [Router Model]
- Firmware Version: [Firmware Version]
- Admin Interface: [URL]

## Port Forwarding Rules
| Service | External Port | Internal IP | Internal Port | Purpose |
|---------|--------------|-------------|---------------|---------|
| [Service Name] | [Port] | [IP] | [Port] | [Purpose] |

## Firewall Rules
| Rule | Source | Destination | Action | Purpose |
|------|--------|-------------|--------|---------|
| [Rule Name] | [Source] | [Destination] | [Allow/Deny] | [Purpose] |

## Remote Access Method
- [Tailscale/VPN/None]
- Configuration: [Brief description]

## Last Verified
- Date: [Date]
- By: [Name]
```

## Best Practices

1. **Regular Audits**: Review your router configuration regularly to ensure no unwanted port forwarding rules have been added
2. **Firmware Updates**: Keep your router firmware updated to patch security vulnerabilities
3. **Strong Passwords**: Use strong, unique passwords for your router admin interface
4. **Guest Network**: If your router supports it, create a separate guest network for visitors
5. **UPnP Caution**: Disable UPnP if not needed, as it can automatically create port forwarding rules
6. **DMZ Avoidance**: Avoid placing any device in the DMZ (Demilitarized Zone) as this exposes all ports

## Additional Security Measures

1. **Change Default Credentials**: Change the default username and password for your router
2. **Disable Remote Management**: Disable remote management of your router unless absolutely necessary
3. **Enable Logging**: Enable logging to track any suspicious activity
4. **MAC Filtering**: Consider enabling MAC filtering to only allow known devices on your network
