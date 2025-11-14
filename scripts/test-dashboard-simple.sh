#!/bin/bash
# Family Assistant Dashboard Testing Script
# Tests dashboard functionality using curl and basic tools

set -e

DASHBOARD_URL="http://100.81.76.55:30801/dashboard"
OUTPUT_DIR="/home/pesu/Rakuflow/systems/homelab/scripts/dashboard-test-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "==================================="
echo "Family Assistant Dashboard Test"
echo "==================================="
echo "URL: $DASHBOARD_URL"
echo "Timestamp: $TIMESTAMP"
echo ""

# Test 1: HTTP Response
echo "Test 1: HTTP Response Check"
echo "-----------------------------------"
HTTP_CODE=$(curl -s -o "$OUTPUT_DIR/response_${TIMESTAMP}.html" -w "%{http_code}" "$DASHBOARD_URL")
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "$DASHBOARD_URL")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Page Load Status: SUCCESS (HTTP $HTTP_CODE)"
else
    echo "❌ Page Load Status: FAILED (HTTP $HTTP_CODE)"
fi
echo "📊 Response Time: ${RESPONSE_TIME}s"
echo ""

# Test 2: Content Analysis
echo "Test 2: Content Analysis"
echo "-----------------------------------"
CONTENT_FILE="$OUTPUT_DIR/response_${TIMESTAMP}.html"

if [ -f "$CONTENT_FILE" ]; then
    CONTENT_SIZE=$(wc -c < "$CONTENT_FILE")
    echo "📄 Content Size: $CONTENT_SIZE bytes"

    # Check for key elements
    echo ""
    echo "Visual Elements Found:"

    if grep -qi "title" "$CONTENT_FILE"; then
        echo "  ✅ Title element detected"
    else
        echo "  ⚠️  Title element not found"
    fi

    if grep -qi "cpu\|memory\|disk" "$CONTENT_FILE"; then
        echo "  ✅ System metrics detected"
    else
        echo "  ⚠️  System metrics not found"
    fi

    if grep -qi "service\|status" "$CONTENT_FILE"; then
        echo "  ✅ Service status detected"
    else
        echo "  ⚠️  Service status not found"
    fi

    if grep -qi "websocket\|ws://" "$CONTENT_FILE"; then
        echo "  ✅ WebSocket connection detected"
    else
        echo "  ⚠️  WebSocket connection not found"
    fi

    if grep -qi "homelab\|family\|assistant" "$CONTENT_FILE"; then
        echo "  ✅ Dashboard branding detected"
    else
        echo "  ⚠️  Dashboard branding not found"
    fi

    # Check for JavaScript
    if grep -qi "<script" "$CONTENT_FILE"; then
        SCRIPT_COUNT=$(grep -ci "<script" "$CONTENT_FILE")
        echo "  ✅ JavaScript detected ($SCRIPT_COUNT script tags)"
    else
        echo "  ⚠️  No JavaScript found"
    fi

    # Check for CSS
    if grep -qi "<style\|stylesheet" "$CONTENT_FILE"; then
        echo "  ✅ Styling detected"
    else
        echo "  ⚠️  No styling found"
    fi
fi
echo ""

# Test 3: API Endpoints
echo "Test 3: API Endpoints"
echo "-----------------------------------"

# Test health endpoint
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "http://100.81.76.55:30801/api/health" 2>/dev/null || echo "000")
if [ "$API_HEALTH" = "200" ]; then
    echo "✅ /api/health: Responsive (HTTP $API_HEALTH)"
else
    echo "❌ /api/health: Not responsive (HTTP $API_HEALTH)"
fi

# Test system stats endpoint
API_STATS=$(curl -s -o /dev/null -w "%{http_code}" "http://100.81.76.55:30801/api/system/stats" 2>/dev/null || echo "000")
if [ "$API_STATS" = "200" ]; then
    echo "✅ /api/system/stats: Responsive (HTTP $API_STATS)"

    # Get actual stats data
    curl -s "http://100.81.76.55:30801/api/system/stats" > "$OUTPUT_DIR/system_stats_${TIMESTAMP}.json"
    echo "   📊 System stats saved to: system_stats_${TIMESTAMP}.json"
else
    echo "❌ /api/system/stats: Not responsive (HTTP $API_STATS)"
fi

# Test services endpoint
API_SERVICES=$(curl -s -o /dev/null -w "%{http_code}" "http://100.81.76.55:30801/api/services" 2>/dev/null || echo "000")
if [ "$API_SERVICES" = "200" ]; then
    echo "✅ /api/services: Responsive (HTTP $API_SERVICES)"

    # Get services data
    curl -s "http://100.81.76.55:30801/api/services" > "$OUTPUT_DIR/services_${TIMESTAMP}.json"
    echo "   📊 Services data saved to: services_${TIMESTAMP}.json"
else
    echo "❌ /api/services: Not responsive (HTTP $API_SERVICES)"
fi
echo ""

# Test 4: WebSocket Connection
echo "Test 4: WebSocket Connection"
echo "-----------------------------------"
# Note: Testing WebSocket requires special tools, so we check for upgrade capability
WS_UPGRADE=$(curl -s -I -H "Connection: Upgrade" -H "Upgrade: websocket" "http://100.81.76.55:30801/ws" | grep -i "upgrade" || echo "")
if [ -n "$WS_UPGRADE" ]; then
    echo "✅ WebSocket upgrade supported"
else
    echo "⚠️  WebSocket upgrade not detected (may still work)"
fi
echo ""

# Test 5: Overall Health Assessment
echo "Test 5: Overall Health Assessment"
echo "-----------------------------------"

HEALTH_SCORE=0
MAX_SCORE=5

[ "$HTTP_CODE" = "200" ] && ((HEALTH_SCORE++))
[ "$CONTENT_SIZE" -gt 1000 ] && ((HEALTH_SCORE++))
[ "$API_HEALTH" = "200" ] && ((HEALTH_SCORE++))
[ "$API_STATS" = "200" ] && ((HEALTH_SCORE++))
[ "$API_SERVICES" = "200" ] && ((HEALTH_SCORE++))

echo "Health Score: $HEALTH_SCORE / $MAX_SCORE"

if [ "$HEALTH_SCORE" -eq "$MAX_SCORE" ]; then
    echo "🟢 Overall Status: HEALTHY"
    OVERALL_STATUS="HEALTHY"
elif [ "$HEALTH_SCORE" -ge 3 ]; then
    echo "🟡 Overall Status: DEGRADED"
    OVERALL_STATUS="DEGRADED"
else
    echo "🔴 Overall Status: UNHEALTHY"
    OVERALL_STATUS="UNHEALTHY"
fi
echo ""

# Summary Report
echo "==================================="
echo "Summary Report"
echo "==================================="
cat > "$OUTPUT_DIR/test_report_${TIMESTAMP}.json" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "url": "$DASHBOARD_URL",
  "tests": {
    "httpResponse": {
      "status": "$HTTP_CODE",
      "responseTime": "${RESPONSE_TIME}s",
      "passed": $([ "$HTTP_CODE" = "200" ] && echo "true" || echo "false")
    },
    "content": {
      "size": "$CONTENT_SIZE",
      "hasContent": $([ "$CONTENT_SIZE" -gt 0 ] && echo "true" || echo "false")
    },
    "apiEndpoints": {
      "health": "$API_HEALTH",
      "systemStats": "$API_STATS",
      "services": "$API_SERVICES"
    },
    "websocket": {
      "upgradeSupported": $([ -n "$WS_UPGRADE" ] && echo "true" || echo "false")
    }
  },
  "healthScore": "$HEALTH_SCORE/$MAX_SCORE",
  "overallStatus": "$OVERALL_STATUS",
  "outputDirectory": "$OUTPUT_DIR"
}
EOF

echo "📊 Detailed report saved to: test_report_${TIMESTAMP}.json"
echo "📁 All test artifacts in: $OUTPUT_DIR"
echo ""

# Display HTML content preview
echo "==================================="
echo "HTML Content Preview (first 500 chars)"
echo "==================================="
head -c 500 "$CONTENT_FILE"
echo ""
echo "..."
echo ""

echo "Test completed successfully!"
