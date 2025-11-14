#!/bin/bash
# Teardown script for development environment

echo "🛑 Stopping Family Assistant development environment..."

if [ -f /tmp/family-assistant-dev-pids.txt ]; then
    while read pid; do
        if kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null && echo "   Stopped port forward (PID: $pid)"
        fi
    done < /tmp/family-assistant-dev-pids.txt
    rm /tmp/family-assistant-dev-pids.txt
    echo "✅ All port forwards stopped"
else
    echo "ℹ️  No active port forwards found"
fi
