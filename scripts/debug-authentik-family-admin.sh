#!/bin/bash

echo "=========================================="
echo "Authentik Family Admin Diagnostics"
echo "=========================================="
echo

echo "1. Checking Authentik Middleware..."
kubectl get middleware authentik -n authentik -o yaml | grep -A 10 "spec:"
echo

echo "2. Checking IngressRoute..."
kubectl get ingressroute family-admin -n homelab -o yaml | grep -A 20 "spec:"
echo

echo "3. Testing ForwardAuth Endpoint..."
kubectl run test-debug --image=curlimages/curl --restart=Never --rm -i -- \
  curl -v http://authentik-server.authentik.svc.cluster.local:9000/outpost.goauthentik.io/auth/traefik \
  2>&1 | grep -E "(HTTP|Location|X-)"
echo

echo "4. Checking Authentik Outpost Logs..."
kubectl logs -n authentik authentik-server-75b86c5997-2hwb7 --tail=20 | \
  grep -E "(outpost|proxy|forward|auth)" | tail -10
echo

echo "5. Testing Family Admin Access..."
curl -I https://admin.fa.pesulabs.net 2>&1 | grep -E "(HTTP|Location|X-authentik)"
echo

echo "=========================================="
echo "CRITICAL AUTHENTIK CONFIGURATION CHECKLIST:"
echo "=========================================="
echo
echo "In Authentik Admin UI, verify:"
echo
echo "1. Provider Configuration:"
echo "   - Go to: Applications → Providers → [Your Provider]"
echo "   - Type: Proxy Provider"
echo "   - Mode: 'Forward auth (single application)' ✓"
echo "   - External host: https://admin.fa.pesulabs.net"
echo "   - Authorization flow: default-provider-authorization-implicit-consent"
echo
echo "2. Application Configuration:"
echo "   - Go to: Applications → Applications → Family Admin"
echo "   - Slug: family-admin"
echo "   - Provider: [linked to provider from step 1]"
echo
echo "3. Outpost Assignment:"
echo "   - Go to: Applications → Outposts → authentik Embedded Outpost"
echo "   - Applications field MUST include 'Family Admin'"
echo "   - Type: Proxy"
echo
echo "If all above are correct and still getting 404:"
echo "  - The embedded outpost may not support ForwardAuth"
echo "  - You may need to deploy a separate proxy outpost"
echo
echo "=========================================="