#!/bin/bash
# Run discovery and generate comparison report

echo "🔍 Running configuration discovery check..." >&2

# Run discovery
bash .claude/skills/config-manager/supporting-scripts/discover-services.sh
bash .claude/skills/config-manager/supporting-scripts/discover-codebase-structure.sh

REPORT="tmp/analysis/config-drift-report-$(date +%Y%m%d-%H%M%S).md"

cat > "$REPORT" << EOF
# Configuration Drift Report

**Generated**: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Summary

This report compares discovered project state vs current configuration files.

---

## Services

### Discovered Services
\`\`\`yaml
EOF

cat tmp/analysis/discovered-services.yaml >> "$REPORT"

cat >> "$REPORT" << 'EOF'
```

### Current Config
```yaml
EOF

grep -A 50 "critical_services:" .claude/config/validation-rules.yaml >> "$REPORT" 2>/dev/null || echo "No current config found" >> "$REPORT"

cat >> "$REPORT" << 'EOF'
```

---

## Codebase Structure

### Discovered Languages
```yaml
EOF

grep -A 20 "languages:" tmp/analysis/discovered-structure.yaml >> "$REPORT"

cat >> "$REPORT" << 'EOF'
```

### Current Config
```yaml
EOF

grep -A 10 "languages:" .claude/config/code-hygiene.yaml >> "$REPORT" 2>/dev/null || echo "No current config found" >> "$REPORT"

cat >> "$REPORT" << 'EOF'
```

---

## Recommendations

1. Review discovered services for new additions
2. Check for URL changes in existing services
3. Verify language detection is accurate
4. Update configs with merge script if changes are acceptable

## Next Steps

```bash
# Merge services
bash .claude/skills/config-manager/supporting-scripts/merge-config.sh \
  .claude/config/validation-rules.yaml \
  tmp/analysis/discovered-services.yaml

# Merge structure
bash .claude/skills/config-manager/supporting-scripts/merge-config.sh \
  .claude/config/code-hygiene.yaml \
  tmp/analysis/discovered-structure.yaml

# Review changes
git diff .claude/config/
```
EOF

echo "✅ Configuration drift report generated: $REPORT" >&2
cat "$REPORT"
