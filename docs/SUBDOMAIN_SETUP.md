# Setting up Subdomain-Based Routing

This guide walks you through setting up subdomain-based routing using Traefik, external-dns, and cert-manager
with Let's Encrypt and Cloudflare DNS validation.

## Prerequisites

- Kubernetes cluster with Flux CD
- Cloudflare account with control over your domain (pesulabs.net)
- Cloudflare API token with permissions for DNS management

## Step 1: Create a Cloudflare API Token

1. Log in to your Cloudflare account
2. Go to your profile (click on your email in the top right)
3. Select "API Tokens"
4. Click "Create Token"
5. Choose the "Edit zone DNS" template or create a custom token with:
   - Zone > DNS > Edit
   - Zone > Zone > Read
   - Include specific zone: pesulabs.net
6. Copy the token value

## Step 2: Set up Cloudflare Token in Kubernetes

Run the setup script:

```bash
./scripts/setup-cloudflare-token.sh YOUR_CLOUDFLARE_API_TOKEN
```

This will update the kustomization files with your token.

## Step 3: Commit and Push Other Changes

```bash
# First, stage only the files you want to commit (NOT the kustomization files with tokens)
git add clusters/homelab/apps/external-dns/helmrepository.yaml
git add clusters/homelab/apps/external-dns/release.yaml
git add clusters/homelab/apps/external-dns/namespace.yaml
git add clusters/homelab/apps/cert-manager/clusterissuer.yaml
git add clusters/homelab/apps/owncloud/ingress.yaml
git add clusters/homelab/apps/owncloud/deployment.yaml

# Commit changes
git commit -m "Configure subdomain-based routing with Cloudflare DNS"

# Push to the repository
git push
```

## Step 4: Apply the Kustomization Files with Tokens

Apply the kustomization files directly:

```bash
kubectl apply -k /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/external-dns/
kubectl apply -k /Users/gonzaloiglesias/sandbox/homelab/clusters/homelab/apps/cert-manager/
```

## Step 5: Verify Everything Works

1. Check if external-dns is running:
   ```bash
   kubectl get pods -n external-dns
   ```

2. Check if DNS records are being created:
   ```bash
   kubectl logs -n external-dns $(kubectl get pods -n external-dns -o name)
   ```

3. Check if certificates are being issued:
   ```bash
   kubectl get certificates -n owncloud
   kubectl describe certificate owncloud-tls -n owncloud
   ```

4. Verify you can access your application:
   ```bash
   curl -vk https://owncloud.app.pesulabs.net
   ```

## Cleanup

After testing, revert the token changes to avoid committing sensitive data:

```bash
git checkout -- clusters/homelab/apps/external-dns/kustomization.yaml
git checkout -- clusters/homelab/apps/cert-manager/kustomization.yaml
```

## Troubleshooting

- If external-dns pods aren't running, check the logs:
  ```bash
  kubectl describe pod -n external-dns
  ```

- If certificates remain in pending state, check the challenges:
  ```bash
  kubectl get challenges -n owncloud
  kubectl describe challenge -n owncloud
  ```

- If DNS records aren't being created, check Cloudflare API permissions and DNS zone settings
