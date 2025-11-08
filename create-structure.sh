#!/bin/bash

# Homelab Directory Structure Creation Script
# This script creates the complete directory structure for the homelab project

set -e

echo "🏗️  Creating Homelab Directory Structure..."
echo ""

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to create directory and print status
create_dir() {
    mkdir -p "$1"
    echo -e "${GREEN}✓${NC} Created: ${BLUE}$1${NC}"
}

# Root level files (will be created separately)
echo "📁 Creating root structure..."

# Documentation
create_dir "docs"
create_dir "docs/diagrams"
create_dir "docs/runbooks"
create_dir "docs/api"

# Infrastructure
echo ""
echo "📁 Creating infrastructure structure..."
create_dir "infrastructure/kubernetes/base"
create_dir "infrastructure/kubernetes/overlays/development"
create_dir "infrastructure/kubernetes/overlays/production"
create_dir "infrastructure/kubernetes/apps/n8n"
create_dir "infrastructure/kubernetes/apps/agentstack"
create_dir "infrastructure/kubernetes/apps/postgres"
create_dir "infrastructure/kubernetes/apps/redis"
create_dir "infrastructure/kubernetes/apps/monitoring"

create_dir "infrastructure/terraform/network"
create_dir "infrastructure/terraform/compute"
create_dir "infrastructure/terraform/modules"

create_dir "infrastructure/compute-node/ollama"
create_dir "infrastructure/compute-node/litellm"
create_dir "infrastructure/compute-node/scripts"
create_dir "infrastructure/compute-node/systemd"

create_dir "infrastructure/service-node/k8s-setup"
create_dir "infrastructure/service-node/base-services"
create_dir "infrastructure/service-node/scripts"

# Services
echo ""
echo "📁 Creating services structure..."
create_dir "services/n8n-workflows/templates"
create_dir "services/n8n-workflows/custom"
create_dir "services/n8n-workflows/examples"

create_dir "services/agentstack-config/agents"
create_dir "services/agentstack-config/tools"
create_dir "services/agentstack-config/prompts"

create_dir "services/llm-router/config"
create_dir "services/llm-router/models"

# Agents
echo ""
echo "📁 Creating agents structure..."
create_dir "agents/examples"
create_dir "agents/templates"
create_dir "agents/production"
create_dir "agents/lib"
create_dir "agents/tests"

# Observability
echo ""
echo "📁 Creating observability structure..."
create_dir "observability/grafana/dashboards"
create_dir "observability/grafana/provisioning"

create_dir "observability/prometheus/rules"
create_dir "observability/prometheus/config"

create_dir "observability/loki/config"

create_dir "observability/alertmanager/config"
create_dir "observability/alertmanager/templates"

# Scripts
echo ""
echo "📁 Creating scripts structure..."
create_dir "scripts/deployment"
create_dir "scripts/backup"
create_dir "scripts/maintenance"
create_dir "scripts/monitoring"
create_dir "scripts/utils"

# Tests
echo ""
echo "📁 Creating tests structure..."
create_dir "tests/unit"
create_dir "tests/integration"
create_dir "tests/e2e"
create_dir "tests/fixtures"

# CI/CD
echo ""
echo "📁 Creating CI/CD structure..."
create_dir ".github/workflows"
create_dir ".github/ISSUE_TEMPLATE"
create_dir ".github/PULL_REQUEST_TEMPLATE"

# Config
echo ""
echo "📁 Creating config structure..."
create_dir "config/development"
create_dir "config/production"

# Create placeholder README files
echo ""
echo "📝 Creating placeholder README files..."

create_readme() {
    local dir=$1
    local title=$2
    if [ ! -f "$dir/README.md" ]; then
        cat > "$dir/README.md" << EOF
# $title

Documentation for this directory.

## Contents

<!-- List the purpose and contents of this directory -->

## Usage

<!-- Add usage instructions -->

## References

<!-- Add links to related documentation -->
EOF
        echo -e "${GREEN}✓${NC} Created README: ${BLUE}$dir/README.md${NC}"
    fi
}

create_readme "docs" "Documentation"
create_readme "infrastructure" "Infrastructure"
create_readme "infrastructure/kubernetes" "Kubernetes Configuration"
create_readme "infrastructure/terraform" "Terraform Configuration"
create_readme "infrastructure/compute-node" "Compute Node Setup"
create_readme "infrastructure/service-node" "Service Node Setup"
create_readme "services" "Services"
create_readme "services/n8n-workflows" "N8n Workflows"
create_readme "services/agentstack-config" "AgentStack Configuration"
create_readme "agents" "Custom Agents"
create_readme "observability" "Observability Stack"
create_readme "scripts" "Automation Scripts"
create_readme "tests" "Test Suite"

# Create sample configuration files
echo ""
echo "📝 Creating sample configuration files..."

# Sample Kubernetes namespace
cat > infrastructure/kubernetes/base/namespace.yaml << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: homelab
  labels:
    name: homelab
    environment: production
EOF
echo -e "${GREEN}✓${NC} Created: ${BLUE}infrastructure/kubernetes/base/namespace.yaml${NC}"

# Sample N8n workflow
cat > services/n8n-workflows/examples/hello-world.json << 'EOF'
{
  "name": "Hello World Example",
  "nodes": [
    {
      "parameters": {},
      "name": "Start",
      "type": "n8n-nodes-base.start",
      "typeVersion": 1,
      "position": [250, 300]
    }
  ],
  "connections": {}
}
EOF
echo -e "${GREEN}✓${NC} Created: ${BLUE}services/n8n-workflows/examples/hello-world.json${NC}"

# Sample LiteLLM config
cat > services/llm-router/config/config.yaml << 'EOF'
model_list:
  - model_name: llama3
    litellm_params:
      model: ollama/llama3.2
      api_base: http://192.168.1.10:11434
      
  - model_name: mistral
    litellm_params:
      model: ollama/mistral
      api_base: http://192.168.1.10:11434

router_settings:
  routing_strategy: simple-shuffle
  num_retries: 2
  timeout: 300
EOF
echo -e "${GREEN}✓${NC} Created: ${BLUE}services/llm-router/config/config.yaml${NC}"

# Sample setup script
cat > scripts/setup.sh << 'EOF'
#!/bin/bash

# Homelab Setup Script
# Run this script to set up the homelab environment

set -e

echo "🚀 Starting Homelab Setup..."

# Check prerequisites
echo "Checking prerequisites..."

# Add your setup logic here

echo "✅ Setup complete!"
EOF
chmod +x scripts/setup.sh
echo -e "${GREEN}✓${NC} Created: ${BLUE}scripts/setup.sh${NC}"

# Sample GitHub workflow
cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [ main, revised-version ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: echo "Tests will run here"
        
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run linting
        run: echo "Linting will run here"
EOF
echo -e "${GREEN}✓${NC} Created: ${BLUE}.github/workflows/ci.yml${NC}"

echo ""
echo "✨ Directory structure created successfully!"
echo ""
echo "📊 Summary:"
echo "  - Created complete directory structure"
echo "  - Added placeholder README files"
echo "  - Created sample configuration files"
echo ""
echo "📝 Next steps:"
echo "  1. Copy .env.example to .env and configure"
echo "  2. Review and customize configuration files"
echo "  3. Run scripts/setup.sh to begin deployment"
echo ""
echo "🎉 Happy building!"
