#!/bin/bash

# Test CORS configuration for thedataguy.pro and subdomains

API_BASE_URL="http://localhost:8123"

echo "🧪 Testing CORS Configuration for thedataguy.pro"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function for CORS
test_cors() {
    local origin=$1
    local description=$2
    
    echo -e "\n${YELLOW}Testing:${NC} $description"
    echo "Origin: $origin"
    
    # Test OPTIONS request (preflight)
    echo "Making OPTIONS (preflight) request..."
    response=$(curl -s -w "%{http_code}" \
        -H "Origin: $origin" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -X OPTIONS \
        "$API_BASE_URL/threads" \
        -o /tmp/cors_response.txt)
    
    if [ "$response" -eq 204 ]; then
        echo -e "${GREEN}✅ OPTIONS request: PASS${NC} (HTTP $response)"
        
        # Check for CORS headers
        cors_origin=$(curl -s -I \
            -H "Origin: $origin" \
            -H "Access-Control-Request-Method: POST" \
            -X OPTIONS \
            "$API_BASE_URL/threads" | grep -i "access-control-allow-origin" | head -1)
        
        if [[ "$cors_origin" =~ "$origin" ]]; then
            echo -e "${GREEN}✅ CORS Origin header: PASS${NC}"
            echo "   Header: $cors_origin"
        else
            echo -e "${RED}❌ CORS Origin header: FAIL${NC}"
            echo "   Expected origin: $origin"
            echo "   Received: $cors_origin"
        fi
    else
        echo -e "${RED}❌ OPTIONS request: FAIL${NC} (HTTP $response)"
        cat /tmp/cors_response.txt
    fi
    
    # Test actual POST request
    echo "Making POST request..."
    post_response=$(curl -s -w "%{http_code}" \
        -H "Origin: $origin" \
        -H "Content-Type: application/json" \
        -X POST \
        -d '{"metadata": {"test": true}}' \
        "$API_BASE_URL/threads" \
        -o /tmp/post_response.txt)
    
    if [ "$post_response" -eq 200 ] || [ "$post_response" -eq 201 ]; then
        echo -e "${GREEN}✅ POST request: PASS${NC} (HTTP $post_response)"
    else
        echo -e "${RED}❌ POST request: FAIL${NC} (HTTP $post_response)"
        echo "Response:"
        cat /tmp/post_response.txt
    fi
}

echo -e "\n${YELLOW}Testing valid origins (should work):${NC}"

# Test main domain
test_cors "https://thedataguy.pro" "Main domain (HTTPS)"
test_cors "http://thedataguy.pro" "Main domain (HTTP)"

# Test subdomains
test_cors "https://chat.thedataguy.pro" "Chat subdomain (HTTPS)"
test_cors "https://api.thedataguy.pro" "API subdomain (HTTPS)"
test_cors "https://blog.thedataguy.pro" "Blog subdomain (HTTPS)"

echo -e "\n${YELLOW}Testing invalid origins (should be blocked):${NC}"

# Test invalid domains
test_cors "https://evil.com" "Different domain (should fail)"
test_cors "https://thedataguy.pro.evil.com" "Domain suffix attack (should fail)"
test_cors "https://nothedataguy.pro" "Similar domain (should fail)"

echo -e "\n${GREEN}🎉 CORS Testing Complete!${NC}"
echo ""
echo "Summary:"
echo "- Valid origins (thedataguy.pro and subdomains) should have CORS headers"
echo "- Invalid origins should be blocked (no CORS headers)"
echo "- All origins can make requests, but browsers will enforce CORS policy"

# Cleanup
rm -f /tmp/cors_response.txt /tmp/post_response.txt
