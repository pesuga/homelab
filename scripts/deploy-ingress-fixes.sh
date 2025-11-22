#!/bin/bash
# Deployment script for ingress routing fixes
# Following Golden Rules from project_context/NETWORKING_STANDARD.md
#
# Usage: ./scripts/deploy-ingress-fixes.sh [--dry-run] [--skip-backup]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="/tmp/homelab-ingress-backup-$(date +%Y%m%d-%H%M%S)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
DRY_RUN=false
SKIP_BACKUP=false
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --skip-backup)
      SKIP_BACKUP=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--dry-run] [--skip-backup]"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Homelab Ingress Routing Fixes Deployment${NC}"
echo -e "${BLUE}  Following Golden Rules (NETWORKING_STANDARD.md)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo

if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}⚠️  DRY RUN MODE - No changes will be applied${NC}"
  echo
fi

# Function to run kubectl with dry-run support
run_kubectl() {
  if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY-RUN]${NC} kubectl $*"
  else
    kubectl "$@"
  fi
}

# Phase 1: Backup
if [ "$SKIP_BACKUP" = false ]; then
  echo -e "${BLUE}Phase 1: Creating backups...${NC}"
  mkdir -p "$BACKUP_DIR"

  echo "  → Backing up IngressRoutes..."
  kubectl get ingressroutes -A -o yaml > "$BACKUP_DIR/ingressroutes-backup.yaml"

  echo "  → Backing up services..."
  kubectl get svc -n authentik authentik-server -o yaml > "$BACKUP_DIR/authentik-server-backup.yaml" 2>/dev/null || true
  kubectl get svc -n homelab family-admin -o yaml > "$BACKUP_DIR/family-admin-backup.yaml" 2>/dev/null || true
  kubectl get svc -n homelab n8n -o yaml > "$BACKUP_DIR/n8n-backup.yaml" 2>/dev/null || true

  echo -e "${GREEN}✅ Backups created in: $BACKUP_DIR${NC}"
  echo
else
  echo -e "${YELLOW}⚠️  Skipping backups (--skip-backup flag)${NC}"
  echo
fi

# Phase 2: Update Services
echo -e "${BLUE}Phase 2: Updating service port mappings...${NC}"

echo "  → Updating authentik-server service..."
run_kubectl apply -f "$PROJECT_ROOT/infrastructure/kubernetes/services/authentik-server-service-fixed.yaml"

echo "  → Updating family-admin service..."
run_kubectl apply -f "$PROJECT_ROOT/infrastructure/kubernetes/services/family-admin-service-fixed.yaml"

echo "  → Updating n8n service..."
run_kubectl apply -f "$PROJECT_ROOT/infrastructure/kubernetes/services/n8n-service-fixed.yaml"

echo -e "${GREEN}✅ Services updated${NC}"
echo

# Wait for services to be ready
if [ "$DRY_RUN" = false ]; then
  echo "  → Waiting for services to be ready..."
  sleep 3
fi

# Verify services
echo "  → Verifying service configurations..."
run_kubectl get svc -n authentik authentik-server
run_kubectl get svc -n homelab family-admin
run_kubectl get svc -n homelab n8n
echo

# Phase 3: Update IngressRoutes
echo -e "${BLUE}Phase 3: Updating IngressRoutes...${NC}"

echo "  → Deleting old IngressRoutes..."
run_kubectl delete ingressroute admin-dashboard -n homelab --ignore-not-found=true
run_kubectl delete ingressroute family-api -n homelab --ignore-not-found=true
run_kubectl delete ingressroute n8n -n homelab --ignore-not-found=true
run_kubectl delete ingressroute authentik-ingress -n authentik --ignore-not-found=true
run_kubectl delete ingressroute family-assistant-app -n family-assistant-app --ignore-not-found=true

echo "  → Applying new IngressRoutes..."
run_kubectl apply -f "$PROJECT_ROOT/infrastructure/kubernetes/traefik/ingress-routes-fixed.yaml"

echo -e "${GREEN}✅ IngressRoutes updated${NC}"
echo

# Wait for IngressRoutes to be ready
if [ "$DRY_RUN" = false ]; then
  echo "  → Waiting for IngressRoutes to be ready..."
  sleep 5
fi

# Verify IngressRoutes
echo "  → Verifying IngressRoute configurations..."
run_kubectl get ingressroutes -A
echo

# Phase 4: Cleanup
echo -e "${BLUE}Phase 4: Cleaning up obsolete resources...${NC}"

echo "  → Deleting old Ingress resources..."
run_kubectl delete ingress family-assistant -n family-assistant --ignore-not-found=true 2>/dev/null || true
run_kubectl delete ingress family-assistant-app -n family-assistant-app --ignore-not-found=true 2>/dev/null || true
run_kubectl delete ingress family-assistant-admin -n family-assistant-admin --ignore-not-found=true 2>/dev/null || true

echo "  → Verifying no old Ingress resources remain..."
OLD_INGRESS=$(kubectl get ingress -A 2>/dev/null | grep -v "No resources" | wc -l || echo "0")
if [ "$OLD_INGRESS" -gt 1 ]; then
  echo -e "${YELLOW}⚠️  Warning: Some old Ingress resources still exist:${NC}"
  kubectl get ingress -A
else
  echo -e "${GREEN}✅ No old Ingress resources found${NC}"
fi
echo

# Phase 5: Validation
if [ "$DRY_RUN" = false ]; then
  echo -e "${BLUE}Phase 5: Validation...${NC}"

  echo "  → Checking service endpoints..."
  kubectl get endpoints -n authentik authentik-server
  kubectl get endpoints -n homelab family-admin
  kubectl get endpoints -n homelab family-assistant
  kubectl get endpoints -n homelab n8n
  kubectl get endpoints -n family-assistant-app family-assistant 2>/dev/null || echo "    (family-assistant-app endpoints not found - may be expected)"
  echo

  echo "  → Testing external HTTPS access..."
  ENDPOINTS=(
    "https://auth.pesulabs.net"
    "https://app.fa.pesulabs.net"
    "https://admin.fa.pesulabs.net"
    "https://api.fa.pesulabs.net"
    "https://n8n.fa.pesulabs.net"
  )

  for endpoint in "${ENDPOINTS[@]}"; do
    echo -n "    Testing $endpoint... "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k --max-time 10 "$endpoint" || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
      echo -e "${GREEN}✅ $HTTP_CODE${NC}"
    else
      echo -e "${RED}❌ $HTTP_CODE${NC}"
    fi
  done
  echo

  echo "  → Checking for Traefik errors..."
  TRAEFIK_ERRORS=$(kubectl logs -n homelab deployment/traefik --tail=50 2>/dev/null | grep -i error | wc -l || echo "0")
  if [ "$TRAEFIK_ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✅ No Traefik errors found${NC}"
  else
    echo -e "${YELLOW}⚠️  Found $TRAEFIK_ERRORS error(s) in Traefik logs${NC}"
    echo "    Check with: kubectl logs -n homelab deployment/traefik --tail=100 | grep -i error"
  fi
  echo
fi

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo
echo "Summary of changes:"
echo "  • Updated 3 service port mappings (authentik, family-admin, n8n)"
echo "  • Applied 5 compliant IngressRoutes"
echo "  • Removed obsolete Ingress resources"
echo
if [ "$SKIP_BACKUP" = false ]; then
  echo "Backups saved to: $BACKUP_DIR"
  echo
  echo "To rollback, run:"
  echo "  kubectl apply -f $BACKUP_DIR/authentik-server-backup.yaml"
  echo "  kubectl apply -f $BACKUP_DIR/family-admin-backup.yaml"
  echo "  kubectl apply -f $BACKUP_DIR/n8n-backup.yaml"
  echo "  kubectl apply -f $BACKUP_DIR/ingressroutes-backup.yaml"
  echo
fi

echo "Next steps:"
echo "  1. Verify all services are accessible via HTTPS"
echo "  2. Check application logs for any errors"
echo "  3. Test user workflows (login, API access, etc.)"
echo "  4. Monitor Traefik logs: kubectl logs -n homelab deployment/traefik -f"
echo
echo "Documentation:"
echo "  • Audit Report: INGRESS_ROUTING_AUDIT_REPORT.md"
echo "  • Fixes Summary: INGRESS_ROUTING_FIXES_SUMMARY.md"
echo "  • Golden Rules: project_context/NETWORKING_STANDARD.md"
echo
