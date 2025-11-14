# Homelab Repository Structure

This document outlines the restructured repository organization for better maintainability and scalability.

## 📁 Directory Structure

```
homelab/
├── production/           # ✅ Production-ready services ONLY
│   ├── core/            # Essential services (N8n, PostgreSQL, Redis)
│   ├── monitoring/      # Prometheus, Loki, dashboards
│   ├── ai-stack/        # Ollama, Qdrant, Mem0, Whisper
│   └── family-assistant/ # Enhanced family platform
├── experimental/        # 🧪 Development and testing
│   ├── mcp-tools/       # MCP development tools
│   ├── new-services/    # Experimental deployments
│   └── beta-features/   # Feature development
├── archive/             # 📦 Deprecated services
│   ├── deprecated/      # Flowise, Grafana, Open WebUI
│   ├── prototypes/      # Early experiments
│   └── old-configs/     # Historical configurations
├── infrastructure/      # ⚙️ Infrastructure as Code
│   ├── certificates/    # SSL certificates and CA
│   ├── compute-node/    # Compute node specific configs
│   ├── flux/            # GitOps configurations
│   ├── kubernetes/      # Remaining K8s manifests
│   └── service-node/    # Service node specific configs
├── scripts/             # 🛠️ Utility scripts
├── docs/                # 📚 Documentation
├── workflows/           # 🔄 N8n workflow templates
└── tests/               # 🧪 Test suites
```

## 🏗️ Production Services

### Core Services (`production/core/`)
Essential services that run the homelab infrastructure:
- **N8n**: Workflow automation and orchestration
- **Databases**: PostgreSQL, Redis, Qdrant
- **Foundational services**: DNS, certificates

### Monitoring Stack (`production/monitoring/`)
Observability and monitoring infrastructure:
- **Prometheus**: Metrics collection and alerting
- **Loki**: Log aggregation and analysis
- **Homelab Dashboard**: System monitoring interface
- **Grafana Dashboards**: (archived) replaced by homelab-dashboard

### AI Stack (`production/ai-stack/`)
Artificial Intelligence and Machine Learning services:
- **Ollama**: Local LLM inference with GPU acceleration
- **Qdrant**: Vector database for semantic search
- **Mem0**: AI memory and context management
- **Whisper**: Speech-to-text processing

### Family Assistant (`production/family-assistant/`)
Family-oriented intelligent assistant platform:
- **Backend**: FastAPI with AI integrations
- **Frontend**: React-based user interface
- **Agents**: Specialized AI agents for family tasks
- **Tools**: Integration with external services

## 🧪 Experimental Services

### MCP Tools (`experimental/mcp-tools/`)
Model Context Protocol development tools and integrations.

### New Services (`experimental/new-services/`)
Experimental services being tested for production readiness.

### Beta Features (`experimental/beta-features/`)
Features in development for existing production services.

## 📦 Archived Services

### Deprecated (`archive/deprecated/`)
Services that have been decommissioned:
- **Flowise**: Replaced by N8n workflows
- **Grafana**: Consolidated into homelab-dashboard
- **Monitorium**: Replaced by Prometheus+Loki stack

### Prototypes (`archive/prototypes/`)
Early experiments and proof-of-concepts:
- **Tana.ai integrations**: Various AI service experiments
- **Sandbox projects**: Testing and development environments

## 📋 Service Migration Status

| Service | Source | Destination | Status | Notes |
|---------|--------|-------------|--------|-------|
| N8n workflows | `services/n8n-workflows` | `production/core/` | ✅ Complete | Core orchestration |
| Homelab Dashboard | `services/homelab-dashboard` | `production/monitoring/` | ✅ Complete | Consolidated monitoring |
| Family Assistant | `services/family-assistant` | `production/family-assistant/` | ✅ Complete | Enhanced platform |
| AI Services | `infrastructure/kubernetes/ai-services` | `production/ai-stack/` | ✅ Complete | All AI-related services |
| MCP Tools | `services/family-assistant/mcp-tools` | `experimental/mcp-tools/` | ✅ Complete | Development tools |
| Flowise | `trash/flowise` | `archive/deprecated/` | ✅ Complete | Replaced by N8n |

## 🔧 Maintenance Guidelines

### Adding New Services
1. **Experimental Phase**: Place in `experimental/` directory
2. **Production Ready**: Move to appropriate `production/` subdirectory
3. **Decommission**: Move to `archive/` with documentation

### Service Lifecycle
- **Prototype** → **Experimental** → **Production** → **Archive**
- Each phase should have clear success criteria
- Automated testing required before production promotion

### Documentation Requirements
- **Production Services**: Full documentation, deployment guides, monitoring
- **Experimental Services**: Basic setup instructions, testing procedures
- **Archived Services**: Deprecation reason, migration notes, retention timeline

## 🚀 Deployment Workflow

1. **Development**: Work in `experimental/` directory
2. **Testing**: Use separate namespace/environment for testing
3. **Validation**: Automated tests, manual verification
4. **Production**: Move to `production/` with proper manifests
5. **Monitoring**: Set up alerts and health checks
6. **Documentation**: Update all relevant documentation

This restructured organization provides:
- ✅ Clear separation of production vs experimental code
- ✅ Better resource management and service discovery
- ✅ Improved developer experience and onboarding
- ✅ Scalable architecture for future enhancements
- ✅ Proper lifecycle management for services