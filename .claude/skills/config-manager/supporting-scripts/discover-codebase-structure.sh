#!/bin/bash
# Auto-discover codebase structure and languages

OUTPUT="tmp/analysis/discovered-structure.yaml"
mkdir -p tmp/analysis

echo "🔍 Discovering codebase structure..." >&2
echo "# Auto-discovered structure - $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$OUTPUT"

# Detect languages
echo "languages:" >> "$OUTPUT"

PYTHON_COUNT=$(find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -not -path "./tmp/*" | wc -l)
if [ "$PYTHON_COUNT" -gt 0 ]; then
  echo "  - name: python" >> "$OUTPUT"
  echo "    files: $PYTHON_COUNT" >> "$OUTPUT"
  echo "    primary_paths:" >> "$OUTPUT"
  find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -not -path "./tmp/*" -type f | head -5 | while read -r file; do
    DIR=$(dirname "$file")
    echo "      - $DIR" >> "$OUTPUT"
  done
fi

JS_COUNT=$(find . \( -name "*.js" -o -name "*.jsx" \) -not -path "./node_modules/*" -not -path "./tmp/*" | wc -l)
if [ "$JS_COUNT" -gt 0 ]; then
  echo "  - name: javascript" >> "$OUTPUT"
  echo "    files: $JS_COUNT" >> "$OUTPUT"
fi

TS_COUNT=$(find . \( -name "*.ts" -o -name "*.tsx" \) -not -path "./node_modules/*" -not -path "./tmp/*" | wc -l)
if [ "$TS_COUNT" -gt 0 ]; then
  echo "  - name: typescript" >> "$OUTPUT"
  echo "    files: $TS_COUNT" >> "$OUTPUT"
fi

# Detect project structure
echo "" >> "$OUTPUT"
echo "project_paths:" >> "$OUTPUT"

# Find service directories
if [ -d "services" ]; then
  echo "  services:" >> "$OUTPUT"
  find services -maxdepth 1 -type d -not -path "services" | while read -r service_dir; do
    echo "    - $(basename "$service_dir")" >> "$OUTPUT"
  done
fi

# Find infrastructure directories
if [ -d "infrastructure" ]; then
  echo "  infrastructure:" >> "$OUTPUT"
  find infrastructure -maxdepth 1 -type d -not -path "infrastructure" | while read -r infra_dir; do
    echo "    - $(basename "$infra_dir")" >> "$OUTPUT"
  done
fi

# Detect exclude paths
echo "" >> "$OUTPUT"
echo "exclude_paths:" >> "$OUTPUT"
for exclude in "node_modules/" "venv/" ".venv/" "__pycache__/" ".git/" "tmp/"; do
  if [ -d "$exclude" ] || [ -d "./$exclude" ]; then
    echo "  - $exclude" >> "$OUTPUT"
  fi
done

echo "✅ Structure discovery complete: $OUTPUT" >&2
cat "$OUTPUT" >&2
