# MCP Development Tools for Homelab Project

This directory contains MCP tools specifically designed to enhance the development workflow for the homelab project. These tools integrate with Claude Code to provide better Kubernetes management, frontend testing, git operations, and development automation.

## Available MCP Tools

### 1. Kubernetes Manager MCP
**File**: `kubernetes_manager.py`
**Purpose**: Advanced Kubernetes cluster management for homelab development
**Features**:
- Smart deployment monitoring and health checks
- Log aggregation and error detection
- Resource usage analysis and optimization
- Backup and recovery operations
- Multi-namespace management
- Rollout status tracking with intelligent alerts

**Usage Examples**:
```bash
# Monitor Family Assistant deployment with health checks
"Check the Family Assistant deployment status and show me any errors"

# Analyze resource usage across all homelab services
"Show me resource usage trends for the homelab namespace"

# Smart restart with zero downtime
"Restart the N8n deployment without causing downtime"

# Get logs from multiple services at once
"Show me recent logs from all database services"
```

### 2. Frontend Testing MCP
**File**: `frontend_tester.py`
**Purpose**: Automated frontend testing for dashboard and Family Assistant UI
**Features**:
- Visual regression testing with Playwright
- Performance benchmarking
- Accessibility testing (WCAG 2.1 AA)
- Cross-browser compatibility checks
- Mobile responsiveness testing
- Dark theme validation
- Real-time monitoring integration

**Usage Examples**:
```bash
# Test dashboard functionality
"Run comprehensive tests on the homelab dashboard"

# Check mobile responsiveness
"Test how the dashboard looks on mobile devices"

# Validate dark theme
"Check if the cappuccino moka theme is working properly"

# Performance benchmarking
"Analyze dashboard performance and identify bottlenecks"
```

### 3. Git Workflow MCP
**File**: `git_workflow.py`
**Purpose**: Intelligent git operations and workflow automation
**Features**:
- Smart commit message generation
- Branch management for features
- Automated testing before commits
- PR/merge request assistance
- Release management
- Conflict resolution helpers

**Usage Examples**:
```bash
# Smart commits with testing
"Commit my changes with a good message and run tests first"

# Branch management
"Create a feature branch for the dashboard enhancements"

# PR preparation
"Help me prepare a pull request for the new monitoring features"
```

### 4. Infrastructure Detective MCP
**File**: `infrastructure_detective.py`
**Purpose**: Troubleshooting and optimization for homelab infrastructure
**Features**:
- Network connectivity diagnostics
- Performance bottleneck identification
- Security vulnerability scanning
- Configuration validation
- Capacity planning recommendations
- Automated health checks

**Usage Examples**:
```bash
# Diagnose connectivity issues
"Why can't I access the Family Assistant API?"

# Performance analysis
"Identify performance bottlenecks in the homelab stack"

# Security scanning
"Check for security vulnerabilities in my current setup"
```

### 5. Documentation Sync MCP
**File**: `documentation_sync.py`
**Purpose**: Keep project documentation in sync with reality
**Features**:
- Auto-update architecture diagrams
- Service discovery and documentation
- API endpoint documentation generation
- Configuration documentation
- Health check documentation updates

**Usage Examples**:
```bash
# Update service documentation
"Update the documentation with current service statuses"

# Generate API docs
"Generate API documentation for the Family Assistant"

# Architecture validation
"Check if the architecture documentation matches reality"
```

## Installation and Setup

### 1. Add MCP Tools to Claude Code

Add these tools to your Claude Code instance by updating the MCP configuration:

```json
{
  "mcpServers": {
    "homelab-kubernetes": {
      "command": "python3",
      "args": ["/home/pesu/Rakuflow/systems/homelab/services/family-assistant/mcp-tools/kubernetes_manager.py"],
      "env": {
        "KUBECONFIG": "/home/pesu/.kube/config"
      }
    },
    "homelab-frontend": {
      "command": "python3",
      "args": ["/home/pesu/Rakuflow/systems/homelab/services/family-assistant/mcp-tools/frontend_tester.py"],
      "env": {
        "PLAYWRIGHT_BROWSERS_PATH": "/home/pesu/.playwright"
      }
    },
    "homelab-git": {
      "command": "python3",
      "args": ["/home/pesu/Rakuflow/systems/homelab/services/family-assistant/mcp-tools/git_workflow.py"]
    },
    "homelab-infra": {
      "command": "python3",
      "args": ["/home/pesu/Rakuflow/systems/homelab/services/family-assistant/mcp-tools/infrastructure_detective.py"]
    },
    "homelab-docs": {
      "command": "python3",
      "args": ["/home/pesu/Rakuflow/systems/homelab/services/family-assistant/mcp-tools/documentation_sync.py"]
    }
  }
}
```

### 2. Install Dependencies

```bash
# Install required Python packages
pip install kubernetes asyncio aiohttp playwright pygit

# Install Playwright browsers
playwright install chromium firefox webkit
```

### 3. Configure Access Rights

Ensure the tools have necessary permissions:
- Kubernetes access via `kubectl`
- Git repository access
- Network access for service checks
- File system access for documentation

## Development Workflow Integration

### Daily Development Routine

1. **Morning Health Check**:
   ```bash
   "Good morning! Please run a complete homelab health check and show me the status dashboard."
   ```

2. **Before Making Changes**:
   ```bash
   "Run frontend tests and check if all services are healthy before I start development."
   ```

3. **During Development**:
   ```bash
   "Monitor the Family Assistant logs while I test this new feature."
   ```

4. **Before Committing**:
   ```bash
   "Run full test suite and prepare a commit message for my changes."
   ```

5. **After Deployment**:
   ```bash
   "Verify the deployment was successful and update documentation."
   ```

### Troubleshooting Workflow

1. **Service Not Responding**:
   ```bash
   "The Family Assistant is down. Help me diagnose and fix the issue."
   ```

2. **Performance Issues**:
   ```bash
   "The dashboard is slow. Analyze performance and suggest optimizations."
   ```

3. **Deployment Failures**:
   ```bash
   "The deployment failed. Show me logs and help me fix the problem."
   ```

## Customization and Extension

Each MCP tool can be customized for your specific environment:

- **Namespace Configuration**: Update default namespaces for your setup
- **Service Endpoints**: Add your specific service URLs and ports
- **Alerting Preferences**: Configure how you want to receive alerts
- **Testing Parameters**: Adjust testing thresholds and expectations

## Safety and Security

All tools include built-in safety measures:
- Read-only operations by default
- Confirmation prompts for destructive actions
- Namespace isolation to prevent accidental changes
- Audit logging for all operations
- Rate limiting to prevent API abuse

## Integration with Existing Tools

These MCP tools integrate seamlessly with:
- Your existing kubectl configuration
- Git workflows and branches
- Tailscale networking
- Prometheus/Grafana monitoring
- Existing CI/CD pipelines

## Troubleshooting MCP Tools

If MCP tools aren't working:
1. Check Python dependencies are installed
2. Verify Kubernetes configuration
3. Ensure proper file permissions
4. Check Claude Code MCP configuration
5. Review tool logs for errors

## Contributing

To extend these tools:
1. Add new functions to the appropriate MCP class
2. Update the tool documentation
3. Test with your homelab setup
4. Contribute back improvements