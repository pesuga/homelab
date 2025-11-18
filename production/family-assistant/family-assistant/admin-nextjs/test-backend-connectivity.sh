#!/bin/bash

echo "=========================================="
echo "Backend Connectivity Test"
echo "=========================================="
echo ""

API_BASE="http://100.81.76.55:30080"

echo "1. Testing Health Endpoint..."
echo "GET $API_BASE/health"
curl -s "$API_BASE/health" | python3 -m json.tool
echo ""
echo ""

echo "2. Testing Login Endpoint Structure..."
echo "POST $API_BASE/api/v1/auth/login"
echo "Payload: {\"email\": \"test@example.com\", \"password\": \"test123\"}"
curl -s -X POST "$API_BASE/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}' | python3 -m json.tool
echo ""
echo ""

echo "3. Testing OpenAPI Documentation..."
echo "GET $API_BASE/openapi.json (auth endpoints only)"
curl -s "$API_BASE/openapi.json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
auth_paths = {k: v for k, v in data['paths'].items() if 'auth' in k.lower()}
print('Auth Endpoints Found:')
for path in sorted(auth_paths.keys()):
    methods = list(auth_paths[path].keys())
    print(f'  {path}: {methods}')
"
echo ""
echo ""

echo "4. Checking CORS Headers..."
curl -s -I -X OPTIONS "$API_BASE/api/v1/auth/login" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" | grep -i "access-control"
echo ""

echo "=========================================="
echo "Backend connectivity test complete!"
echo "=========================================="
