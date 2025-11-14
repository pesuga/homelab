# Family Assistant - Local Development Guide

This guide explains how to develop the Family Assistant application locally while using services from the Kubernetes cluster.

## Quick Start

### 1. Setup Port Forwards (Terminal 1)

```bash
cd /home/pesu/Rakuflow/systems/homelab/production/family-assistant/family-assistant
chmod +x dev-setup.sh dev-teardown.sh
./dev-setup.sh
```

This will:
- Forward backend API to `localhost:8001`
- Forward PostgreSQL to `localhost:5432`
- Forward Redis to `localhost:6379`
- Forward Mem0 to `localhost:8080`
- Forward Loki to `localhost:3100`
- Forward Qdrant to `localhost:6333`

**Keep this terminal open** - it needs to stay running!

### 2. Start Frontend Dev Server (Terminal 2)

```bash
cd frontend
npm run dev
```

Access at: **http://localhost:5173**

### 3. (Optional) Start Backend Locally (Terminal 3)

If you need to modify backend code:

```bash
cd backend
source ../venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
```

Or use the cluster backend (default with port forwarding).

## Development Workflows

### Frontend-Only Development (Most Common)

1. Start port forwards: `./dev-setup.sh`
2. Start frontend: `cd frontend && npm run dev`
3. Edit React components in `frontend/src/`
4. Changes hot-reload automatically
5. API calls go to cluster backend via port forward

**No build/deploy needed!** 🎉

### Backend Development

1. Start port forwards: `./dev-setup.sh`
2. Stop the backend port forward: `pkill -f "port-forward.*family-assistant"`
3. Start local backend: `cd backend && uvicorn api.main:app --reload --port 8001`
4. Edit Python files in `api/`
5. FastAPI auto-reloads on changes

### Full Stack Development

1. Start port forwards: `./dev-setup.sh`
2. Terminal 2: Start local backend
3. Terminal 3: Start frontend dev server
4. Edit both frontend and backend simultaneously

## Environment Variables

### Frontend (.env.development)
```bash
VITE_API_BASE_URL=http://localhost:8001
VITE_ENV=development
```

### Backend (backend/.env.development)
```bash
DATABASE_URL=postgresql://homelab:homelab123@localhost:5432/homelab
REDIS_HOST=localhost
REDIS_PORT=6379
OLLAMA_API_URL=http://100.72.98.106:11434
MEM0_API_URL=http://localhost:8080
QDRANT_HOST=localhost
QDRANT_PORT=6333
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Testing

### Frontend Tests
```bash
cd frontend
npm test                    # Unit tests
npm run test:e2e           # E2E tests (requires backend)
```

### Backend Tests
```bash
cd backend
pytest tests/              # All tests
pytest tests/unit/         # Unit tests only
pytest -v --tb=short       # Verbose with short traceback
```

## Debugging

### Frontend Debugging
- Chrome DevTools: `F12` or right-click → Inspect
- React DevTools: Install browser extension
- Network tab shows API calls
- Console shows errors and logs

### Backend Debugging
- FastAPI docs: http://localhost:8001/docs
- Add `import pdb; pdb.set_trace()` for breakpoints
- View logs in terminal
- Use Grafana for cluster logs: http://100.81.76.55:30091

### Database Access
```bash
# Connect to PostgreSQL via port forward
psql postgresql://homelab:homelab123@localhost:5432/homelab

# Common queries
\dt                        # List tables
SELECT * FROM users;       # Query data
```

### Redis Access
```bash
# Connect to Redis via port forward
redis-cli -h localhost -p 6379

# Common commands
KEYS *                     # List all keys
GET key_name              # Get value
FLUSHALL                  # Clear all data (careful!)
```

## Building and Deploying

### Build Frontend Only
```bash
cd frontend
npm run build
docker build -t 100.81.76.55:30500/family-assistant-frontend:dev-test .
docker push 100.81.76.55:30500/family-assistant-frontend:dev-test
kubectl set image deployment/family-assistant-frontend -n homelab \
  frontend=100.81.76.55:30500/family-assistant-frontend:dev-test
```

### Build Backend Only
```bash
docker build -t 100.81.76.55:30500/family-assistant:dev-test .
docker push 100.81.76.55:30500/family-assistant:dev-test
kubectl set image deployment/family-assistant -n homelab \
  family-assistant=100.81.76.55:30500/family-assistant:dev-test
```

### Quick Deploy Script
```bash
./scripts/quick-deploy.sh frontend  # Deploy frontend only
./scripts/quick-deploy.sh backend   # Deploy backend only
./scripts/quick-deploy.sh full      # Deploy both
```

## Cleanup

### Stop Port Forwards
```bash
./dev-teardown.sh
```

Or press `Ctrl+C` in the dev-setup terminal.

### Kill All Node/Python Processes (Nuclear Option)
```bash
pkill -f "vite"           # Kill Vite dev server
pkill -f "uvicorn"        # Kill FastAPI
pkill -f "port-forward"   # Kill all port forwards
```

## Tips and Tricks

### Hot Reload Not Working?
- Frontend: Check if `npm run dev` is running
- Backend: Ensure `--reload` flag is used with uvicorn
- Try restarting the dev server

### Port Already in Use?
```bash
# Find what's using the port
lsof -i :5173     # Frontend port
lsof -i :8001     # Backend port

# Kill the process
kill -9 <PID>
```

### API Calls Failing?
- Verify port forwards are running: `ps aux | grep port-forward`
- Check backend is accessible: `curl http://localhost:8001/health`
- Check browser console for errors
- Verify CORS settings if getting CORS errors

### Database Migrations
```bash
cd backend
alembic upgrade head      # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│ Your Local Machine                                   │
│                                                      │
│  ┌─────────────┐         ┌──────────────┐          │
│  │   Browser   │────────▶│ Vite Dev     │          │
│  │ :5173       │         │ Server       │          │
│  └─────────────┘         └──────┬───────┘          │
│                                  │                   │
│                                  │ API Calls         │
│                                  ▼                   │
│                          ┌──────────────┐           │
│                          │ Backend      │           │
│                          │ localhost:   │           │
│                          │ 8001         │           │
│                          └──────┬───────┘           │
│                                  │                   │
└──────────────────────────────────┼──────────────────┘
                                   │
                    Port Forwards  │
                                   │
┌──────────────────────────────────┼──────────────────┐
│ Kubernetes Cluster (100.81.76.55)│                  │
│                                   ▼                  │
│  ┌────────────┐  ┌──────────┐  ┌────────┐          │
│  │ PostgreSQL │  │  Redis   │  │  Mem0  │          │
│  │   :5432    │  │  :6379   │  │  :8080 │          │
│  └────────────┘  └──────────┘  └────────┘          │
│                                                      │
│  ┌────────────┐  ┌──────────┐                       │
│  │   Loki     │  │  Qdrant  │                       │
│  │   :3100    │  │  :6333   │                       │
│  └────────────┘  └──────────┘                       │
└─────────────────────────────────────────────────────┘
```

## Common Issues

### "Connection refused" errors
- Ensure port forwards are running: `./dev-setup.sh`
- Check if services are healthy: `kubectl get pods -n homelab`

### Frontend can't reach backend
- Verify `VITE_API_BASE_URL` in `.env.development`
- Check browser console for CORS errors
- Ensure backend CORS settings allow localhost:5173

### Database connection errors
- Verify PostgreSQL port forward is running
- Check credentials in backend `.env.development`
- Test connection: `psql postgresql://homelab:homelab123@localhost:5432/homelab`

### Changes not appearing
- Frontend: Check for build errors in terminal
- Backend: Verify `--reload` flag is set
- Clear browser cache: `Ctrl+Shift+R`

## Resources

- Frontend Docs: `frontend/README.md`
- Backend API: http://localhost:8001/docs (when running)
- Grafana Logs: http://100.81.76.55:30091
- Cluster Dashboard: https://dash.homelab.pesulabs.net
