#!/bin/bash
# Startup script for Family Assistant API

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH=/home/pesu/Rakuflow/systems/homelab/services/family-assistant

# Start API
echo "🚀 Starting Family Assistant API..."
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
