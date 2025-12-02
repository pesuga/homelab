#!/bin/bash
# Auto-validate deployments after kubectl/docker/service commands

read input
COMMAND=$(echo "$input" | jq -r '.tool_input.command // empty')

# Detect deployment commands
if [[ "$COMMAND" =~ kubectl.*apply|kubectl.*rollout|docker.*run|systemctl.*restart ]]; then
  echo "🔍 Auto-validation triggered for: $COMMAND" >&2

  # Give service time to start
  sleep 5

  # Run your existing verify-claim command
  cd "$PROJECT_ROOT" || exit 0

  # Call your validation script
  ./scripts/keep/health-check-all.py

  VALIDATION_RESULT=$?

  if [ $VALIDATION_RESULT -ne 0 ]; then
    echo "" >&2
    echo "❌ VALIDATION FAILED" >&2
    echo "⚠️  Deployment command completed but service validation failed" >&2
    echo "" >&2
    echo "Please investigate and fix before claiming success." >&2
    echo "Run /verify-claim to see detailed status" >&2
    echo "" >&2

    # Re-prompt Claude to investigate
    echo "VALIDATION_FAILED" > /tmp/claude-validation-status
    exit 1  # This blocks Claude from claiming success
  else
    echo "✅ Deployment validated successfully" >&2
    echo "VALIDATION_PASSED" > /tmp/claude-validation-status
    exit 0
  fi
fi

exit 0  # Non-deployment commands pass through