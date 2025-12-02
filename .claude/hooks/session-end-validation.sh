#!/bin/bash
# Validate all claims before session ends

cd "$PROJECT_ROOT" || exit 0

# Run comprehensive validation
echo "📊 Running end-of-session validation..." >&2
scripts/keep/health-check-all.py > /tmp/session-validation.txt 2>&1

# Save validation report
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p tmp/validation-reports
cp /tmp/session-validation.txt "tmp/validation-reports/session-end-$TIMESTAMP.txt"

echo "✅ Validation report saved to tmp/validation-reports/" >&2
cat /tmp/session-validation.txt >&2

exit 0