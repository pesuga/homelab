# Installation Guide: Homelab Development MCP Tools

This guide explains how to install and configure the MCP tools for enhancing your homelab development workflow with Claude Code.

## Overview

The MCP tools provide specialized capabilities for:
- **Kubernetes Manager**: Advanced cluster management and troubleshooting
- **Frontend Tester**: Automated testing with Playwright for dashboard/UI
- **Git Workflow**: Intelligent git operations and workflow automation
- **Infrastructure Detective**: Network diagnostics and performance analysis
- **Documentation Sync**: Automatic documentation synchronization

## Prerequisites

### System Requirements
- Python 3.8+ installed
- Claude Code with MCP support
- kubectl configured for your homelab cluster
- Docker access (for some tools)

### Python Dependencies
```bash
# Install required Python packages
pip install kubernetes asyncio aiohttp playwright psutil pygit

# Install Playwright browsers
playwright install chromium firefox webkit
```

### Git Configuration
Ensure git is configured with your user information:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Installation Steps

### 1. Clone or Verify Repository Access
Make sure you have access to the homelab repository:
```bash
cd /home/pesu/Rakuflow/systems/homelab/services/family-assistant
ls mcp-tools/
```

### 2. Make Tools Executable
```bash
chmod +x mcp-tools/*.py
```

### 3. Test Individual Tools
Test each tool to ensure they work:

```bash
# Test Kubernetes Manager
python3 mcp-tools/kubernetes_manager.py --describe

# Test Frontend Tester
python3 mcp-tools/frontend_tester.py --describe

# Test Git Workflow
python3 mcp-tools/git_workflow.py --describe

# Test Infrastructure Detective
python3 mcp-tools/infrastructure_detective.py --describe

# Test Documentation Sync
python3 mcp-tools/documentation_sync.py --describe
```

### 4. Configure Claude Code

Add the MCP tools to your Claude Code configuration. The configuration is typically located at:
- Linux/macOS: `~/.config/claude-code/config.json`
- Windows: `%APPDATA%/Claude Code/config.json`

Add the following to your Claude Code configuration:

```json
{
  "mcpServers": {
    "homelab-kubernetes": {
      "command": "python3",
      "args": ["/home/pesu/Rakuflow/systems/homelab/services/family-assistant/mcp-tools/kubernetes_manager.py"],
      "env": {
        "HOMELAB_NAMESPACE": "homelab",
        "KUBECONFIG": "/home/pesu/.kube/config"
      }
    },
    "homelab-frontend": {
      "command": "python3",
      "args": ["/home/pesu/Rakuflow/systems/homelab/services/family-assistant/mcp-tools/frontend_tester.py"],
      "env": {
        "HOMELAB_BASE_URL": "http://100.81.76.55:30800",
        "PLAYWRIGHT_BROWSERS_PATH": "/home/pesu/.playwright"
      }
    },
    "homelab-git": {
      "command": "python3",
      "args": ["/home/pesu/Rakuflow/systems/homelab/services/family-assistant/mcp-tools/git_workflow.py"],
      "env": {
        "GIT_PRE_COMMIT_TESTS": "true",
        "GIT_AUTO_PUSH": "false",
        "GIT_COMMIT_TEMPLATE": "homelab"
      }
    },
    "homelab-infra": {
      "command": "python3",
      "args": ["/home/pesu/Rakuflow/systems/homelab/services/family-assistant/mcp-tools/infrastructure_detective.py"],
      "env": {
        "SERVICE_NODE_IP": "100.81.76.55",
        "COMPUTE_NODE_IP": "100.72.98.106"
      }
    },
    "homelab-docs": {
      "command": "python3",
      "args": ["/home/pesu/Rakuflow/systems/homelab/services/family-assistant/mcp-tools/documentation_sync.py"],
      "env": {
        "DOCS_DIR": "/home/pesu/Rakuflow/systems/homelab/docs",
        "REPO_PATH": "/home/pesu/Rakuflow/systems/homelab"
      }
    }
  }
}
```

### 5. Restart Claude Code
Restart Claude Code to load the new MCP tools.

### 6. Verify Installation
Start a new Claude Code session and verify tools are available by asking:
```
What MCP tools are available for my homelab project?
```

## Tool-Specific Configuration

### Kubernetes Manager
- **KUBECONFIG**: Path to your kubeconfig file (default: `~/.kube/config`)
- **HOMELAB_NAMESPACE**: Kubernetes namespace to manage (default: `homelab`)

### Frontend Tester
- **HOMELAB_BASE_URL**: Base URL for testing (default: `http://localhost:30800`)
- **PLAYWRIGHT_BROWSERS_PATH**: Path for Playwright browser installations

### Git Workflow
- **GIT_PRE_COMMIT_TESTS**: Enable pre-commit tests (default: `true`)
- **GIT_AUTO_PUSH**: Automatically push after commits (default: `false`)
- **GIT_REQUIRE_ISSUE_LINK**: Require issue references in commits (default: `false`)

### Infrastructure Detective
- **SERVICE_NODE_IP**: IP address of service node (default: `100.81.76.55`)
- **COMPUTE_NODE_IP**: IP address of compute node (default: `100.72.98.106`)

### Documentation Sync
- **DOCS_DIR**: Documentation directory path
- **REPO_PATH**: Repository root path

## Usage Examples

### Kubernetes Management
```
Check the health of all deployments in the homelab namespace
```

```
Show me resource usage across all services
```

```
Restart the Family Assistant deployment with zero downtime
```

### Frontend Testing
```
Run comprehensive tests on the homelab dashboard
```

```
Test the dashboard on mobile devices with different viewports
```

```
Validate the cappuccino moka dark theme implementation
```

### Git Workflow
```
Commit my changes with a smart message and run tests first
```

```
Create a feature branch for dashboard improvements
```

```
Help me prepare a pull request for the new monitoring features
```

### Infrastructure Troubleshooting
```
Diagnose why I can't access the Family Assistant API
```

```
Analyze performance bottlenecks in the homelab stack
```

```
Check for security vulnerabilities in my current setup
```

### Documentation
```
Update service documentation to match actual running services
```

```
Generate API documentation for the Family Assistant
```

```
Validate that architecture docs match the actual infrastructure
```

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   ```bash
   chmod +x mcp-tools/*.py
   ```

2. **Python Module Not Found**
   ```bash
   pip install -r requirements.txt
   ```

3. **Kubernetes Connection Issues**
   ```bash
   kubectl cluster-info
   export KUBECONFIG=/path/to/your/kubeconfig
   ```

4. **Playwright Browser Issues**
   ```bash
   playwright install chromium
   ```

5. **MCP Tools Not Loading**
   - Verify Claude Code configuration syntax
   - Restart Claude Code completely
   - Check tool paths are correct

### Debug Mode

Run tools in debug mode to troubleshoot issues:

```bash
# Test Kubernetes connection
python3 mcp-tools/kubernetes_manager.py get_namespace_overview '{"namespace": "homelab"}'

# Test frontend accessibility
python3 mcp-tools/frontend_tester.py test_dashboard_health '{"base_url": "http://100.81.76.55:30800"}'

# Test git operations
python3 mcp-tools/git_workflow.py get_repo_status '{}'
```

## Performance Optimization

### Resource Usage
- The tools are designed to be lightweight
- Kubernetes queries are cached when possible
- Playwright tests run in headless mode by default

### Network Efficiency
- All network operations have timeouts
- Concurrent operations are used when beneficial
- Connection pooling for repeated requests

## Security Considerations

### Safe Operations
- All destructive operations require confirmation
- Read-only access by default
- Namespace isolation prevents accidental cross-namespace changes
- Audit logging for all operations

### Credentials
- Tools use existing kubectl configuration
- No hardcoded credentials
- Environment variables for sensitive configuration

## Customization and Extension

### Adding New Tools
1. Create new Python file in `mcp-tools/`
2. Implement the MCP interface with `--describe` support
3. Add to Claude Code configuration
4. Update this documentation

### Modifying Existing Tools
Each tool is modular and can be customized:
- Update environment variables for different configurations
- Add new functionality by extending existing classes
- Modify timeouts and retry logic as needed

## Updates and Maintenance

### Updating Tools
```bash
cd /home/pesu/Rakuflow/systems/homelab/services/family-assistant/mcp-tools
git pull  # If tools are version controlled
```

### Updating Dependencies
```bash
pip install --upgrade kubernetes playwright aiohttp psutil
```

### Backup Configuration
Backup your Claude Code configuration:
```bash
cp ~/.config/claude-code/config.json ~/.config/claude-code/config.json.backup
```

## Support and Contributing

### Getting Help
- Check the tool documentation: `python3 mcp-tools/[tool-name].py --describe`
- Review debug output from tool runs
- Verify all prerequisites are met

### Contributing
To contribute improvements:
1. Test changes thoroughly
2. Update documentation
3. Ensure backward compatibility
4. Follow existing code patterns

---

**Note**: These tools are designed specifically for the homelab project architecture. Adjust IP addresses, namespaces, and configurations as needed for your specific setup.