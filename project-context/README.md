# Homelab Project

**Project Type**: Personal Infrastructure & Service Platform
**Architecture**: Two-node Kubernetes homelab with GPU compute
**Primary Goal**: Self-hosted AI services, automation, and family applications

---

## Quick Reference

- **Main Services**: Dashboard, N8n, Family Assistant, Ollama
- **Infrastructure**: K3s on service node (asuna) + compute node with AMD RX 7800 XT
- **Networking**: Tailscale mesh, Traefik ingress with Let's Encrypt
- **Monitoring**: Prometheus, Grafana, Loki

---

## Project Structure

```
homelab/
├── infrastructure/        # Infrastructure as code
│   ├── kubernetes/       # K8s manifests and Kustomize
│   └── docker/           # Docker Compose configs
├── services/             # Application services
│   ├── family-api/       # Family Assistant backend (Python/FastAPI)
│   ├── dashboard/        # Homelab dashboard (React)
│   └── n8n/              # Workflow automation
├── project-context/      # THIS DIRECTORY - Project documentation
│   ├── README.md         # This file - project overview
│   ├── SESSION-STATE.md  # Current session tracking
│   ├── ARCHITECTURE.md   # System architecture
│   ├── SERVICES.md       # Service inventory
│   └── KNOWLEDGE.md      # Reusable patterns
├── .claude/              # Claude Code configuration
│   ├── skills/           # Reusable knowledge bases
│   ├── commands/         # Slash commands
│   ├── hooks/            # Automation hooks
│   └── config/           # Configuration files
├── scripts/              # Permanent utility scripts
└── tmp/                  # Ephemeral content (gitignored)
```

---

## Documentation Files

### SESSION-STATE.md
Tracks what happened during each development session:
- Commands executed
- Files modified
- Outcomes and decisions
- Blockers encountered

### ARCHITECTURE.md
System design and architecture decisions:
- Infrastructure layout
- Service dependencies
- Network topology
- Design patterns

### SERVICES.md
Current service inventory:
- Service status
- Version information
- Endpoints
- Health check details

### KNOWLEDGE.md
Reusable patterns and learnings:
- Common troubleshooting procedures
- Configuration patterns
- Best practices
- Lessons learned

---

## Key Technologies

### Infrastructure
- **Kubernetes**: K3s lightweight distribution
- **Container Runtime**: containerd
- **Ingress**: Traefik with automatic HTTPS
- **Service Mesh**: Tailscale for secure networking
- **Storage**: Local path provisioner

### Services
- **Family API**: Python 3.12, FastAPI, PostgreSQL
- **Dashboard**: React 18, TypeScript, Vite
- **N8n**: Workflow automation platform
- **Ollama**: Local LLM inference with AMD GPU

### Monitoring & Observability
- **Metrics**: Prometheus
- **Visualization**: Grafana
- **Logs**: Loki
- **Tracing**: OpenTelemetry (planned)

---

## Development Workflow

### Starting a Session
1. Check `SESSION-STATE.md` for current state
2. Review any blockers or next steps
3. Use validation commands to verify service health

### During Development
1. Update `SESSION-STATE.md` as you work
2. Run validation after deployments
3. Document important decisions in `ARCHITECTURE.md`
4. Capture reusable patterns in `KNOWLEDGE.md`

### Ending a Session
1. Run `/validate-session` to verify claims
2. Update service inventory if changes were made
3. Archive ephemeral documentation
4. Update "Where We Left Off" in CLAUDE.md

---

## Common Commands

```bash
# Health checks
/homelab-health                    # Comprehensive system status
/verify-claim claim:"..."          # Verify specific claim

# Validation
/validate-session                   # End-of-session validation

# Documentation
/update-docs                        # Update project documentation
/update-config                      # Update config files from discovery

# Kubernetes operations (run directly, no ssh needed)
kubectl get pods -A                 # All pods
kubectl logs -f <pod>              # Follow logs
kubectl describe pod <pod>         # Pod details
```

---

## Service URLs

- **Dashboard**: https://dash.pesulabs.net
- **N8n**: https://n8n.homelab.pesulabs.net
- **Family Assistant**: https://family-assistant.homelab.pesulabs.net
- **Ollama (Native)**: http://100.72.98.106:11434
- **Prometheus**: https://prometheus.homelab.pesulabs.net
- **Grafana**: https://grafana.homelab.pesulabs.net

---

## Important Notes

### Network Access
- Always use Tailscale IPs for inter-node communication
- Service node (asuna): 100.81.76.55
- Compute node: 100.72.98.106

### Validation Requirements
- Never claim "all services working" without running `/verify-claim`
- Always run validation after deployments
- Use validation hooks to catch failures early

### Documentation Standards
- Update SESSION-STATE.md for all significant changes
- Record architecture decisions when making design choices
- Capture reusable patterns immediately when discovered
- Keep service inventory current

---

## Getting Help

- Check `KNOWLEDGE.md` for common patterns
- Review `ARCHITECTURE.md` for system design context
- Use `.claude/skills/homelab-troubleshooting/main.md` for diagnostic procedures
- See `CLAUDE.md` for Claude Code specific instructions

---

**Last Updated**: 2025-11-26
**Maintained By**: Claude Code with homelab-documentation-manager skill
