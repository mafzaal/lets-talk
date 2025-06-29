#!/bin/bash

# Test script for LangGraph API access control
# This script tests both public and private endpoint access

set -e

API_BASE_URL="http://localhost:8123"

# Try to load API key from .env.auth file
if [ -f ".env.auth" ]; then
    # Get the first non-empty API key from .env.auth
    API_KEY=$(grep -E "^API_KEY_[0-9]+=.+" .env.auth | head -1 | cut -d'=' -f2)
    if [ -z "$API_KEY" ]; then
        echo "⚠️  Warning: No API keys found in .env.auth file"
        API_KEY="test-key-not-valid"
    else
        echo "✅ Using API key from .env.auth: ${API_KEY:0:10}..."
    fi
else
    echo "⚠️  Warning: .env.auth file not found, using default test key"
    API_KEY="test-key-not-valid"
fi

echo "🧪 Testing LangGraph API Access Control"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local endpoint=$1
    local expected_status=$2
    local headers=$3
    local description=$4
    
    echo -e "\n${YELLOW}Testing:${NC} $description"
    echo "Endpoint: $endpoint"
    
    if [ -n "$headers" ]; then
        response=$(curl -s -w "%{http_code}" -H "$headers" "$API_BASE_URL$endpoint" -o /tmp/response.json)
    else
        response=$(curl -s -w "%{http_code}" "$API_BASE_URL$endpoint" -o /tmp/response.json)
    fi
    
    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $response)"
        if [ "$response" -eq 200 ]; then
            echo "Response preview:"
            head -c 200 /tmp/response.json
            echo "..."
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (Expected HTTP $expected_status, got HTTP $response)"
        echo "Response:"
        cat /tmp/response.json
    fi
}

echo -e "\n${YELLOW}Step 1: Testing Public Endpoints${NC}"
echo "These should work without authentication:"

# Test health endpoint (public)
test_endpoint "/health" 200 "" "Health check (public)"

# Test threads endpoint (public)
test_endpoint "/threads" 200 "" "Threads endpoint (public)"

echo -e "\n${YELLOW}Step 2: Testing Private Endpoints Without Auth${NC}" 
echo "These should return 401 Unauthorized:"

# Test docs without auth (should fail)
test_endpoint "/docs" 401 "" "Documentation without auth (should fail)"

# Test other endpoints without auth (should fail) 
test_endpoint "/runs" 401 "" "Runs endpoint without auth (should fail)"

echo -e "\n${YELLOW}Step 3: Testing Private Endpoints With Auth${NC}"
echo "These should work with valid API key:"

# Test docs with auth (should work)
test_endpoint "/docs" 200 "X-API-Key: $API_KEY" "Documentation with auth (should work)"

# Test OpenAPI spec with auth (should work)
test_endpoint "/openapi.json" 200 "X-API-Key: $API_KEY" "OpenAPI spec with auth (should work)"

echo -e "\n${YELLOW}Step 4: Testing Rate Limiting${NC}"
echo "Testing multiple rapid requests to public endpoint:"

echo "Making 5 rapid requests to /health..."
for i in {1..5}; do
    response=$(curl -s -w "%{http_code}" "$API_BASE_URL/health" -o /dev/null)
    echo "Request $i: HTTP $response"
    if [ "$response" -eq 429 ]; then
        echo -e "${YELLOW}⚠️  Rate limiting detected${NC}"
        break
    fi
done

echo -e "\n${GREEN}🎉 Testing Complete!${NC}"
echo ""
echo "Summary:"
echo "- Public endpoints (/health, /threads) should be accessible"
echo "- Private endpoints should require X-API-Key header"
echo "- Rate limiting should prevent excessive requests"
echo ""
echo "If any tests failed, check:"
echo "1. Services are running: docker-compose ps"
echo "2. API key is correct in this script"
echo "3. nginx.conf contains your API key"
echo "4. nginx service restarted after config changes"

# Cleanup
rm -f /tmp/response.json
