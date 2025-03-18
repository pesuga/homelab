# Subdomain Routing Fix Plan - Updated

## Current Status and Attempted Solutions

We've been working on resolving several issues with subdomain-based routing. Here's a detailed analysis of what we've tried and found:

## 1. External-DNS Issue

**Problem:**
The external-dns HelmRelease is failing with the persistent error:
```
HelmChart 'flux-system/external-dns-external-dns' is not ready: chart pull error: failed to download chart for remote reference: Get "oci://registry-1.docker.io/bitnamicharts/external-dns:8.7.7": unsupported protocol scheme "oci"
```

**Solutions Attempted:**

1. **Added DNS-01 instead of DNS01**: Fixed the ClusterIssuer configuration by changing `dns-01` to `dns01`.
   - Result: This fixed the ClusterIssuer issue, and certificates are now being issued correctly.

2. **Updated the HelmRelease API version**: Changed from `v2beta1` to `v2`.
   - Result: No change in the error.

3. **Created a dedicated HelmRepository**:
   - Created a new `bitnami-external-dns` HelmRepository specifically for external-dns.
   - Updated the HelmRelease to point to this new repository.
   - Result: The repository was created correctly with `Ready: True` status, but the HelmRelease still fails.

4. **Upgraded HelmRelease to v2**:
   - Result: No improvement.

## Root Cause Analysis

After researching similar issues online, we've identified that the problem is likely related to how Flux is trying to use OCI (Open Container Initiative) repositories. The error message indicates Flux is trying to use the `oci://` protocol to download the chart, which suggests:

1. **Flux Configuration**: The Flux controllers might be configured to use OCI repositories by default, which isn't supported by the current setup.

2. **Bitnami Chart Repository Change**: Bitnami may have changed their repository format, and Flux is trying to use the new format while missing required configurations.

3. **Version Mismatch**: There may be a mismatch between Flux's version and its ability to handle certain chart repository types.

## New Fix Plan

1. **Disable OCI Support or Configure it Properly**:
   - Update the Flux HelmController configuration to either:
     - Disable OCI support entirely, or
     - Properly configure OCI support if it's required

2. **Use Direct Helm Installation as Workaround**:
   - If Flux continues to have issues, we can:
     - Create a Kubernetes Job that uses `helm install` directly
     - This bypasses Flux's HelmRelease controller completely

3. **Try Alternative Chart Repository**:
   - Use a different chart repository that's known to work with current Flux version
   - Options include the Kubernetes SIGs ExternalDNS chart

4. **Check Flux Version Compatibility**:
   - Review Flux's compatibility matrix to ensure we're using compatible versions of all components

5. **Verify Cloudflare API Token**:
   - Although unrelated to the OCI error, ensure the Cloudflare API token is configured correctly
   - This will be necessary once external-dns is working

## Manual DNS Workaround

As a temporary solution while we fix external-dns:

1. Manually add DNS records in Cloudflare for each service:
   - `owncloud.app.pesulabs.net` → Your server's IP
   - `n8n.app.pesulabs.net` → Your server's IP
   - `home-assistant.app.pesulabs.net` → Your server's IP
   - `glance.app.pesulabs.net` → Your server's IP

2. Test services by directly accessing their subdomains once DNS records are in place

3. Continue working on the external-dns fix in parallel

## Next Steps

1. Try implementing the new fix plan starting with the OCI configuration
2. If that fails, implement the manual DNS workaround
3. Continue to research the specific error and newer Flux compatibility issues
