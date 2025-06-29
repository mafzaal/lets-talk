#!/bin/bash

# Test CORS configuration with parameterized domains

API_BASE_URL="http://localhost:8123"

echo "🧪 Testing Parameterized CORS Configuration"
echo "==========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function for CORS
test_cors() {
    local origin=$1
    local description=$2
    local expected_result=$3
    
    echo -e "\n${YELLOW}Testing:${NC} $description"
    echo "Origin: $origin"
    echo "Expected: $expected_result"
    
    # Test OPTIONS request (preflight)
    cors_origin=$(curl -s -I \
        -H "Origin: $origin" \
        -H "Access-Control-Request-Method: POST" \
        -X OPTIONS \
        "$API_BASE_URL/threads" | grep -i "access-control-allow-origin" | head -1 | cut -d' ' -f2- | tr -d '\r')
    
    if [ "$expected_result" = "ALLOWED" ]; then
        if [[ "$cors_origin" == *"$origin"* ]]; then
            echo -e "${GREEN}✅ PASS${NC} - Origin allowed"
            echo "   Header: Access-Control-Allow-Origin: $cors_origin"
        else
            echo -e "${RED}❌ FAIL${NC} - Origin should be allowed but wasn't"
            echo "   Expected: $origin"
            echo "   Got: $cors_origin"
        fi
    else
        if [[ -z "$cors_origin" || "$cors_origin" == "Access-Control-Allow-Origin:" ]]; then
            echo -e "${GREEN}✅ PASS${NC} - Origin blocked as expected"
        else
            echo -e "${RED}❌ FAIL${NC} - Origin should be blocked but was allowed"
            echo "   Got: $cors_origin"
        fi
    fi
}

echo -e "\n${YELLOW}Testing domains from .env.auth configuration:${NC}"

# Read CORS domains from .env.auth
if [ -f ".env.auth" ]; then
    source .env.auth
    
    echo "Configured CORS domains:"
    [ -n "$CORS_DOMAIN_1" ] && echo "  - CORS_DOMAIN_1: $CORS_DOMAIN_1"
    [ -n "$CORS_DOMAIN_2" ] && echo "  - CORS_DOMAIN_2: $CORS_DOMAIN_2"
    [ -n "$CORS_DOMAIN_3" ] && echo "  - CORS_DOMAIN_3: $CORS_DOMAIN_3"
else
    echo -e "${RED}❌ .env.auth file not found${NC}"
    exit 1
fi

# Test configured domains
[ -n "$CORS_DOMAIN_1" ] && {
    test_cors "https://$CORS_DOMAIN_1" "Domain 1 (HTTPS)" "ALLOWED"
    test_cors "http://$CORS_DOMAIN_1" "Domain 1 (HTTP)" "ALLOWED"
}

[ -n "$CORS_DOMAIN_2" ] && {
    test_cors "https://$CORS_DOMAIN_2" "Domain 2 (HTTPS)" "ALLOWED"
    test_cors "http://$CORS_DOMAIN_2" "Domain 2 (HTTP)" "ALLOWED"
}

[ -n "$CORS_DOMAIN_3" ] && {
    test_cors "https://$CORS_DOMAIN_3" "Domain 3 (HTTPS)" "ALLOWED"
    test_cors "http://$CORS_DOMAIN_3" "Domain 3 (HTTP)" "ALLOWED"
}

# Test subdomains if they should be allowed
if [ "$CORS_ALLOW_SUBDOMAINS" = "true" ]; then
    echo -e "\n${YELLOW}Testing subdomains (should be allowed):${NC}"
    [ -n "$CORS_DOMAIN_1" ] && test_cors "https://chat.$CORS_DOMAIN_1" "Domain 1 subdomain" "ALLOWED"
    [ -n "$CORS_DOMAIN_2" ] && test_cors "https://api.$CORS_DOMAIN_2" "Domain 2 subdomain" "ALLOWED"
fi

# Test invalid domains
echo -e "\n${YELLOW}Testing invalid domains (should be blocked):${NC}"
test_cors "https://evil.com" "Evil domain" "BLOCKED"
test_cors "https://thedataguy.pro.evil.com" "Domain suffix attack" "BLOCKED"
test_cors "https://nothedataguy.pro" "Similar domain" "BLOCKED"

echo -e "\n${GREEN}🎉 CORS Domain Testing Complete!${NC}"
echo ""
echo "Summary:"
echo "- Configured domains should be allowed"
echo "- Invalid domains should be blocked"
echo "- Subdomains behavior depends on CORS_ALLOW_SUBDOMAINS setting"
