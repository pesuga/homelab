# 🏠 Homelab: Agentic Workflow Platform

> **Mission**: Build an open-source, self-hosted agentic workflow platform with local LLM inference, accessible both locally and remotely.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Active%20Development-green)]()
[![Built with Claude](https://img.shields.io/badge/Built%20with-Claude-purple)]()

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

This homelab project creates a production-ready, self-hosted platform for building and running agentic workflows with local LLM inference. Everything runs on your own hardware, ensuring complete data sovereignty and privacy.

### Key Components

- **🧠 LLM Inference**: Local model hosting with GPU acceleration (AMD RX 7800 XT)
- **🔄 Workflow Automation**: N8n for visual workflow building
- **🤖 Agent Framework**: AgentStack for advanced agent orchestration
- **☸️ Orchestration**: Kubernetes for service management
- **🔒 Secure Access**: Tailscale for zero-trust networking
- **📊 Observability**: Full metrics, logging, and alerting stack

---

## 🏗️ Architecture

### Hardware Layer

```
┌─────────────────────────────────────────────────────────────┐
│                    Network Layer                             │
│  GL-MT2500 Firewall + Tailscale Exit Node                   │
│  • Secure gateway  • VPN  • Traffic routing                 │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴──────────────────┐
        │                                       │
┌───────▼──────────┐                  ┌────────▼───────────┐
│  Compute Node    │                  │   Service Node     │
│  (WSL/Ubuntu)    │                  │   (Linux Server)   │
├──────────────────┤                  ├────────────────────┤
│ • LLM Inference  │                  │ • K8s Cluster      │
│ • Ollama/vLLM    │                  │ • N8n              │
│ • LiteLLM Router │                  │ • AgentStack       │
│ • GPU (RX 7800XT)│                  │ • PostgreSQL       │
│ • Development    │                  │ • Redis            │
│                  │                  │ • Observability    │
└──────────────────┘                  └────────────────────┘
  i5-12400F, 32GB                       i7, 16GB RAM
```

### Software Stack

```
Application Layer
├── N8n (Workflow Automation)
├── AgentStack (Agent Framework)
└── Custom Agents

Inference Layer
├── Ollama (Model Management)
├── LiteLLM (Router & Load Balancer)
└── Local LLM Models

Orchestration Layer
├── Kubernetes (K3s)
├── Docker
└── Helm Charts

Data Layer
├── PostgreSQL (Persistent Storage)
├── Redis (Caching & Queues)
└── Object Storage

Observability Layer
├── Prometheus (Metrics)
├── Grafana (Dashboards)
├── Loki (Logs)
└── AlertManager (Alerts)

Network Layer
└── Tailscale (Zero-Trust VPN)
```

---

## ✨ Features

### Core Capabilities

- ✅ **Local LLM Inference** with GPU acceleration
- ✅ **Smart Model Routing** with automatic failover
- ✅ **Visual Workflow Builder** (N8n)
- ✅ **Agent Framework** for complex automations
- ✅ **Kubernetes Orchestration** for scalability
- ✅ **Zero-Trust Networking** via Tailscale
- ✅ **Full Observability** with metrics, logs, and traces
- ✅ **CI/CD Pipeline** for automated deployments
- ✅ **Mobile Access** from anywhere securely

### Design Principles

1. **🏠 Local-First**: All compute and data stays in your network
2. **🔓 Open Source**: Built on and contributing to OSS
3. **🧩 Modular**: Services are independent and composable
4. **👁️ Observable**: Everything is logged and monitored
5. **🤖 Automated**: Manual work is automated away
6. **📚 Documented**: Comprehensive documentation
7. **🗂️ Version Controlled**: All code and config in Git
8. **🤝 Claude-Assisted**: Developed with AI pair programming

---

## 📦 Prerequisites

### Hardware Requirements

#### Compute Node (Required)
- CPU: 6+ cores (Intel i5-12400F or equivalent)
- RAM: 32GB minimum
- GPU: AMD RX 7800 XT (or equivalent with 8GB+ VRAM)
- Storage: 500GB+ NVMe SSD
- OS: Windows with WSL2 (Ubuntu) or Linux

#### Service Node (Required)
- CPU: 4+ cores (Intel i7 or equivalent)
- RAM: 16GB minimum
- Storage: 256GB+ SSD
- OS: Linux (Ubuntu 22.04 LTS recommended)

#### Network Hardware (Required)
- Router with OpenWRT support (GL-MT2500 or equivalent)
- Gigabit Ethernet connectivity
- Internet connection with static IP or DDNS

### Software Requirements

- **Docker** 24.0+
- **Kubernetes** (K3s 1.27+)
- **Git** 2.40+
- **Node.js** 18+ LTS
- **Python** 3.11+
- **Claude Code** (latest)

### Accounts Needed

- GitHub account
- Tailscale account (free tier works)
- Notion account (optional, for documentation)

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/homelab.git
cd homelab
git checkout revised-version
```

### 2. Run Setup Script

```bash
./scripts/setup.sh
```

This will:
- Verify prerequisites
- Set up environment variables
- Configure Tailscale
- Deploy base infrastructure
- Run health checks

### 3. Deploy Services

```bash
# Deploy to Compute Node (LLM Inference)
cd infrastructure/compute-node
./deploy.sh

# Deploy to Service Node (K8s cluster)
cd infrastructure/service-node
./deploy.sh
```

### 4. Access Services

Once deployed, services are available at:

- **N8n**: http://n8n.homelab.local:5678
- **Grafana**: http://grafana.homelab.local:3000
- **LiteLLM**: http://llm-router.homelab.local:8000

Via Tailscale (remote access):
- All services accessible via Tailscale DNS

---

## 📁 Project Structure

```
homelab/
├── README.md                      # This file
├── LICENSE                        # MIT License
├── .gitignore                    # Git ignore rules
├── .env.example                  # Environment template
│
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md           # System architecture
│   ├── DEPLOYMENT.md             # Deployment guide
│   ├── DEVELOPMENT.md            # Development guide
│   ├── NETWORKING.md             # Network setup
│   ├── TROUBLESHOOTING.md        # Common issues
│   └── API.md                    # API documentation
│
├── infrastructure/               # Infrastructure as Code
│   ├── kubernetes/               # K8s manifests
│   │   ├── base/                 # Base configs
│   │   ├── overlays/             # Environment overlays
│   │   └── apps/                 # Application deployments
│   ├── terraform/                # Terraform configs
│   │   ├── network/              # Network setup
│   │   └── compute/              # Compute resources
│   ├── compute-node/             # Compute node setup
│   │   ├── ollama/               # Ollama configs
│   │   ├── litellm/              # LiteLLM configs
│   │   └── scripts/              # Setup scripts
│   └── service-node/             # Service node setup
│       ├── k8s-setup/            # K8s installation
│       └── base-services/        # Core services
│
├── services/                     # Service configurations
│   ├── n8n-workflows/            # N8n workflow exports
│   │   ├── templates/            # Workflow templates
│   │   └── custom/               # Custom workflows
│   ├── agentstack-config/        # AgentStack configs
│   │   ├── agents/               # Agent definitions
│   │   └── tools/                # Agent tools
│   └── llm-router/               # LiteLLM configuration
│       ├── models.yaml           # Model definitions
│       └── routes.yaml           # Routing rules
│
├── agents/                       # Custom agent implementations
│   ├── examples/                 # Example agents
│   ├── templates/                # Agent templates
│   └── production/               # Production agents
│
├── observability/                # Monitoring configs
│   ├── grafana/                  # Dashboards
│   ├── prometheus/               # Metrics configs
│   ├── loki/                     # Log configs
│   └── alertmanager/             # Alert rules
│
├── scripts/                      # Automation scripts
│   ├── setup.sh                  # Initial setup
│   ├── deploy.sh                 # Deployment
│   ├── backup.sh                 # Backup routines
│   ├── restore.sh                # Restore routines
│   └── health-check.sh           # Health checks
│
└── tests/                        # Test suites
    ├── unit/                     # Unit tests
    ├── integration/              # Integration tests
    └── e2e/                      # End-to-end tests
```

---

## 📚 Documentation

Comprehensive documentation is available in the `/docs` directory:

- **[Architecture](docs/ARCHITECTURE.md)**: System design and components
- **[Deployment Guide](docs/DEPLOYMENT.md)**: Step-by-step deployment
- **[Development Guide](docs/DEVELOPMENT.md)**: Contributing and development
- **[Networking](docs/NETWORKING.md)**: Network configuration
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions
- **[API Documentation](docs/API.md)**: API endpoints and usage

---

## 🗓️ Roadmap

### Sprint 0: Foundation (Weeks 1-2) ✅
- [x] Repository setup
- [x] Documentation structure
- [ ] Tailscale installation
- [ ] K8s cluster setup
- [ ] Base infrastructure

### Sprint 1: LLM Infrastructure (Weeks 3-4)
- [ ] Ollama installation
- [ ] LiteLLM deployment
- [ ] Model management
- [ ] GPU configuration
- [ ] Health monitoring

### Sprint 2: Core Services (Weeks 5-6)
- [ ] N8n deployment
- [ ] AgentStack setup
- [ ] PostgreSQL cluster
- [ ] Redis deployment
- [ ] Service mesh

### Sprint 3: Observability (Weeks 7-8)
- [ ] Prometheus setup
- [ ] Grafana dashboards
- [ ] Loki logging
- [ ] Alert rules
- [ ] Runbooks

### Sprint 4: Networking (Weeks 9-10)
- [ ] Tailscale subnets
- [ ] Exit node setup
- [ ] Mobile access
- [ ] Authentication
- [ ] Access procedures

### Sprint 5: Agent Workflows (Weeks 11-12)
- [ ] First N8n workflow
- [ ] LLM integration
- [ ] AgentStack agent
- [ ] Agent templates
- [ ] Pattern documentation

### Sprint 6: CI/CD (Weeks 13-14)
- [ ] GitHub Actions
- [ ] Automated testing
- [ ] Deployment pipelines
- [ ] Backup automation
- [ ] Disaster recovery

---

## 🤝 Contributing

Contributions are welcome! This is a personal homelab project, but if you find it useful and want to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Workflow

This project uses Claude Code for AI-assisted development:

```bash
# Start Claude Code in the project directory
cd homelab
claude

# Claude has access to:
# - Project files (via filesystem MCP)
# - GitHub (via GitHub MCP)
# - Documentation (via Notion MCP)
```

---

## 📊 Project Status

**Current Phase**: Sprint 0 - Foundation  
**Progress**: 20%  
**Next Milestone**: K8s cluster deployment  
**Timeline**: 12-14 weeks to full platform

### Success Metrics

- **Performance**: LLM inference < 2s, availability > 99%
- **Development**: Idea to deployment < 1 day
- **Resources**: GPU 60-80%, CPU < 70%, Memory < 75%

---

## 🔒 Security

- All data stays local (no cloud dependencies)
- Zero-trust networking via Tailscale
- Encrypted at rest and in transit
- Regular security updates
- Audit logging enabled

See [SECURITY.md](SECURITY.md) for security policies.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Claude** by Anthropic - AI pair programming
- **N8n** - Workflow automation
- **Tailscale** - Zero-trust networking
- **Ollama** - Local LLM hosting
- All the open source projects that make this possible

---

## 📞 Support

- **Documentation**: [/docs](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/homelab/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/homelab/discussions)

---

**Built with ❤️ using Claude, running locally on your hardware.**
