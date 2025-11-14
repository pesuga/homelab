#!/bin/bash
# Development Environment Setup for Family Assistant
# This script sets up port forwarding to cluster services for local development

set -e

echo "🚀 Setting up Family Assistant development environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port forwarding is already running
check_port_forward() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Function to start port forward in background
start_port_forward() {
    local service=$1
    local namespace=$2
    local local_port=$3
    local remote_port=$4
    local label=$5

    echo -e "${GREEN}▶️  Forwarding $label: localhost:$local_port → $service:$remote_port${NC}"

    if check_port_forward $local_port; then
        kubectl port-forward -n $namespace svc/$service $local_port:$remote_port > /dev/null 2>&1 &
        echo $! >> /tmp/family-assistant-dev-pids.txt
        sleep 1
    fi
}

# Clean up any existing port forwards
if [ -f /tmp/family-assistant-dev-pids.txt ]; then
    echo "🧹 Cleaning up existing port forwards..."
    while read pid; do
        kill $pid 2>/dev/null || true
    done < /tmp/family-assistant-dev-pids.txt
    rm /tmp/family-assistant-dev-pids.txt
fi

# Create PID tracking file
touch /tmp/family-assistant-dev-pids.txt

echo ""
echo "📡 Setting up port forwards to cluster services..."
echo ""

# Backend API
start_port_forward "family-assistant" "homelab" 8001 8001 "Backend API"

# PostgreSQL
start_port_forward "postgres" "homelab" 5432 5432 "PostgreSQL"

# Redis
start_port_forward "redis" "homelab" 6379 6379 "Redis"

# Mem0
start_port_forward "mem0" "homelab" 8080 8080 "Mem0 AI"

# Loki (for logs)
start_port_forward "loki" "homelab" 3100 3100 "Loki Logs"

# Qdrant (vector DB)
start_port_forward "qdrant" "homelab" 6333 6333 "Qdrant HTTP"

echo ""
echo -e "${GREEN}✅ Development environment ready!${NC}"
echo ""
echo "📝 Service URLs for local development:"
echo "   Backend API:    http://localhost:8001"
echo "   PostgreSQL:     localhost:5432"
echo "   Redis:          localhost:6379"
echo "   Mem0:           http://localhost:8080"
echo "   Loki:           http://localhost:3100"
echo "   Qdrant:         http://localhost:6333"
echo ""
echo "🎯 To start frontend development:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "   Frontend will be at: http://localhost:5173"
echo "   It will proxy API calls to: http://localhost:8001"
echo ""
echo "🛑 To stop all port forwards:"
echo "   ./dev-teardown.sh"
echo ""
echo "💡 Tip: Keep this terminal open while developing"
echo "   Press Ctrl+C to stop all port forwards"
echo ""

# Wait for Ctrl+C
trap 'echo ""; echo "🛑 Stopping port forwards..."; while read pid; do kill $pid 2>/dev/null || true; done < /tmp/family-assistant-dev-pids.txt; rm /tmp/family-assistant-dev-pids.txt; echo "✅ Done"; exit 0' INT

# Keep script running
wait
