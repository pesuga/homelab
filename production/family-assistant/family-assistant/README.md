# Family Assistant - AI-Powered Family Platform

A comprehensive family management platform with AI assistance, built on Kubernetes with local LLM inference.

## 🚀 Quick Start

### Development Mode (Recommended)

```bash
# Terminal 1: Start port forwards to cluster services
./dev-setup.sh

# Terminal 2: Start frontend dev server
cd frontend
npm run dev
```

Access at: **http://localhost:5173**

**That's it!** No build, no deploy, just edit and reload. 🎉

### Production Access

- **HTTPS**: https://family.homelab.pesulabs.net
- **HTTP NodePort**: http://100.81.76.55:30300

## 📚 Documentation

- **[DEV_GUIDE.md](DEV_GUIDE.md)** - Complete development guide with workflows, debugging, and tips
- **[INSTALL.md](INSTALL.md)** - Production deployment and configuration
- **[TELEGRAM_SETUP_GUIDE.md](TELEGRAM_SETUP_GUIDE.md)** - Telegram bot setup

## 🏗️ Architecture

```
Frontend (React + TypeScript + Vite)
    ↓ API Calls
Backend (FastAPI + Python)
    ↓ Services
├─ PostgreSQL (User data, profiles)
├─ Redis (Cache, sessions)
├─ Mem0 (AI memory)
├─ Qdrant (Vector storage)
└─ Ollama (Local LLM via Tailscale)
```

## 🛠️ Development Workflows

### Frontend Only (Most Common)
```bash
./dev-setup.sh              # Start port forwards
cd frontend && npm run dev  # Start dev server
# Edit src/ files - changes hot-reload automatically
```

### Backend Development
```bash
./dev-setup.sh                                    # Start port forwards
pkill -f "port-forward.*family-assistant"        # Stop backend forward
cd backend && uvicorn api.main:app --reload --port 8001
# Edit api/ files - FastAPI auto-reloads
```

### Quick Deploy
```bash
./scripts/quick-deploy.sh frontend   # Deploy frontend only
./scripts/quick-deploy.sh backend    # Deploy backend only
./scripts/quick-deploy.sh full       # Deploy both
```

## 🎯 Key Features

- **AI Chat Assistant**: Powered by local Ollama (Qwen 2.5 Coder 14B)
- **Family Member Management**: Profiles, permissions, roles
- **Smart Memory**: Mem0 for contextual conversations
- **Real-time Updates**: WebSocket connections
- **System Dashboard**: Monitor all services
- **Telegram Bot**: Multimodal chat interface

## 🔧 VS Code Integration

Press `F1` and search for:
- `Tasks: Run Task` → See all available tasks
- `Debug: Select and Start Debugging` → Debug frontend or backend

## 🧪 Testing

```bash
# Frontend
cd frontend
npm test              # Unit tests
npm run test:e2e     # E2E tests

# Backend
pytest tests/        # All tests
pytest -v --tb=short # Verbose with short traceback
```

## 📊 Observability

- **Grafana (Logs)**: http://100.81.76.55:30091 (admin/admin123)
- **Prometheus (Metrics)**: http://100.81.76.55:30090
- **Loki (Log Aggregation)**: http://100.81.76.55:30314

## 🗂️ Project Structure

```
family-assistant/
├── frontend/               # React application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── contexts/      # React contexts
│   │   ├── hooks/         # Custom hooks
│   │   └── utils/         # Utilities
│   ├── e2e/              # E2E tests
│   └── nginx.conf        # Production nginx config
├── api/                  # FastAPI backend
│   ├── main.py          # Main application
│   ├── routes/          # API routes
│   └── models/          # Data models
├── config/              # Configuration
├── tests/               # Backend tests
├── scripts/             # Deployment scripts
└── .vscode/            # VS Code configuration
```

## 🚦 Common Tasks

| Task | Command |
|------|---------|
| Start development | `./dev-setup.sh` |
| Stop port forwards | `./dev-teardown.sh` or `Ctrl+C` |
| Frontend dev server | `cd frontend && npm run dev` |
| Backend dev server | `uvicorn api.main:app --reload --port 8001` |
| Deploy frontend | `./scripts/quick-deploy.sh frontend` |
| Deploy backend | `./scripts/quick-deploy.sh backend` |
| View logs (Grafana) | http://100.81.76.55:30091 |
| Frontend logs (K8s) | `kubectl logs -n homelab -l app=family-assistant-frontend -f` |
| Backend logs (K8s) | `kubectl logs -n homelab -l app=family-assistant -f` |

## 🐛 Troubleshooting

See [DEV_GUIDE.md](DEV_GUIDE.md#common-issues) for detailed troubleshooting.

**Quick fixes:**
```bash
# Port forwards not working
./dev-teardown.sh && ./dev-setup.sh

# Frontend not loading
cd frontend && rm -rf node_modules package-lock.json && npm install

# Backend errors
kubectl logs -n homelab -l app=family-assistant --tail=50
```

## 🤝 Contributing

1. Create feature branch
2. Develop locally with `./dev-setup.sh`
3. Test changes
4. Deploy with `./scripts/quick-deploy.sh`
5. Create pull request

## 📝 License

Private project for personal use.
