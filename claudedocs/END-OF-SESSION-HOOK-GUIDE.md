# Claude Code End-of-Session Hook Guide

## Overview

The **End-of-Session Hook** is a custom Claude Code hook that automatically runs when Claude stops answering. It provides intelligent documentation management, file cleanup, and session continuity for your homelab project.

## Features

### 🔄 **Documentation Management**
- **"Where We Left Off" Updates**: Automatically updates the continuity section in `CLAUDE.md`
- **Session State Tracking**: Logs session activity in `docs/SESSION-STATE.md`
- **Smart Archiving**: Moves completed documentation to `claudedocs/archive/YYYY-MM-DD/`

### 🧹 **Intelligent Cleanup**
- **Temporary Files**: Removes `*.tmp`, `test-*`, `debug-*`, `temp-*` patterns
- **One-Time Scripts**: Archives or removes scripts based on usefulness
- **Documentation**: Archives non-core markdown files older than 1 hour
- **Protection**: Preserves essential files (`README.md`, `CLAUDE.md`, etc.)

### 📍 **Session Continuity**
- **Context Preservation**: Tracks working directory, branch, and git status
- **Next Steps**: Provides clear continuation instructions
- **Quick Status**: Checklist for session resume
- **Tool Awareness**: Notes active tools and services being used

## Installation

### Hook File Location
```bash
# Main hook script
~/.claude/end-of-session-hook.sh

# Test script
~/.claude/test-end-of-session-hook.sh
```

### Permissions
Both scripts are executable and ready to use:
```bash
chmod +x ~/.claude/end-of-session-hook.sh
chmod +x ~/.claude/test-end-of-session-hook.sh
```

## Usage

### Manual Testing
```bash
# Test the hook functionality
~/.claude/test-end-of-session-hook.sh

# Run hook in test mode
~/.claude/end-of-session-hook.sh --test
```

### Automatic Execution
The hook is designed to integrate with Claude Code's hook system. When Claude stops answering, it will:

1. **Update Documentation**
   - Refresh "Where We Left Off" section in `CLAUDE.md`
   - Add session entry to `docs/SESSION-STATE.md`

2. **Process Files**
   - Archive old documentation files
   - Remove temporary files and scripts
   - Preserve important project files

3. **Generate Summary**
   - Show git status and uncommitted changes
   - Provide continuity instructions
   - Display cleanup results

## File Processing Rules

### Files Removed (🗑️)
- `*.tmp`, `*.log` files
- `test-*`, `temp-*`, `debug-*`, `check-*`, `verify-*` files
- One-time scripts with temporary names

### Files Archived (📁)
- Documentation files not in `docs/` directory (older than 1 hour)
- Potentially useful scripts (not in established script directories)
- Session-specific markdown files

### Files Preserved (✅)
- Core documentation: `README.md`, `CLAUDE.md`, `SESSION-STATE.md`
- Files in `docs/` directory
- Infrastructure scripts: `infrastructure/compute-node/scripts/`
- Established project scripts: `scripts/`

## Directory Structure

```
claudedocs/
├── archive/                    # Session documentation archive
│   └── 2025-11-15/            # Date-stamped archives
│       ├── scripts/           # Archived scripts
│       └── *.md              # Archived documentation
├── END-OF-SESSION-HOOK-GUIDE.md
└── [existing project docs]
```

## "Where We Left Off" Section

The hook maintains a section in `CLAUDE.md` with:

- **Last Session**: Date and main activity
- **Working Directory**: Current project path
- **Current Branch**: Git branch information
- **Active Tasks**: What was being worked on
- **Tools & Services**: Active development tools
- **Session Summary**: Documentation and cleanup results
- **Continuation Instructions**: Next session checklist
- **Quick Status**: Immediate action items

## Configuration

### Customization Options
Edit `~/.claude/end-of-session-hook.sh` to modify:

- **TEMP_FILE_PATTERNS**: Files to remove
- **SCRIPT_PATTERNS**: Script processing rules
- **DOC_PATTERNS**: Documentation archiving
- **PROJECT_DIR**: Target project directory
- **Archive timing**: File age thresholds

### Environment-Specific Settings
```bash
# Project directory
PROJECT_DIR="/home/pesu/Rakuflow/systems/homelab"

# Archive location
CLAUDE_DOCS="$PROJECT_DIR/claudedocs"
ARCHIVE_DIR="$CLAUDE_DOCS/archive"
```

## Troubleshooting

### Common Issues

**Hook not running:**
- Ensure file is executable: `chmod +x ~/.claude/end-of-session-hook.sh`
- Check Claude Code hook configuration

**Files not being cleaned:**
- Verify file patterns match your naming conventions
- Check file modification times (files < 1 hour old are preserved)

**Documentation not updating:**
- Ensure `CLAUDE.md` is writable
- Check backup file creation permissions

### Debug Mode
Run with detailed output:
```bash
bash -x ~/.claude/end-of-session-hook.sh --test
```

### Manual Cleanup
If needed, manually process files:
```bash
# Remove temporary files
rm -f test-* temp-* debug-*.sh *.tmp

# Archive old documentation
mkdir -p claudedocs/archive/$(date +%Y-%m-%d)
mv *.md claudedocs/archive/$(date +%Y-%m-%d)/ 2>/dev/null || true
```

## Integration with Workflow

### Before Ending Session
1. **Commit important changes**: `git add . && git commit -m "Session progress"`
2. **Run final health checks**: `./scripts/health-check-all.sh`
3. **Note any blockers**: Update current sprint objectives

### After Hook Runs
1. **Review "Where We Left Off"**: Check updated section in `CLAUDE.md`
2. **Verify git status**: Commit any remaining important changes
3. **Check archive**: Review moved files in `claudedocs/archive/`

### Best Practices
- **Commit frequently**: Don't let uncommitted files accumulate
- **Use descriptive filenames**: Avoid generic names like `temp.md`
- **Update documentation**: Keep `CLAUDE.md` current during sessions
- **Review archives**: Periodically clean up old archives

## Development

### Hook Structure
```bash
main()                    # Entry point
├── get_session_info()   # Collect session data
├── update_where_we_left_off()  # Update CLAUDE.md
├── update_session_state()      # Update SESSION-STATE.md
├── process_files()             # File cleanup/archiving
└── generate_summary()          # Status output
```

### Testing
Use the test script to verify functionality:
```bash
~/.claude/test-end-of-session-hook.sh
```

This creates test files, runs the hook, and shows results.

## Future Enhancements

Potential improvements:
- **Git integration**: Auto-commit of session documentation
- **Service status**: Check and log homelab service health
- **Resource monitoring**: Track system resource usage
- **Sprint tracking**: Integration with project sprint management
- **Team notifications**: Alert team members of session completion

## Support

For issues or enhancement requests:
1. Check this guide for troubleshooting steps
2. Review hook logs for error messages
3. Test with the provided test script
4. Verify file permissions and directory structure

---

**Last Updated**: 2025-11-15
**Version**: 1.0
**Status**: Production Ready ✅