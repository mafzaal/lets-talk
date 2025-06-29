#!/bin/bash

# Quick verification script to test the nginx template substitution locally
# This helps debug the configuration before running with Docker

echo "🔧 Testing nginx configuration template substitution..."

# Load environment variables from .env.auth
if [ -f ".env.auth" ]; then
    echo "📁 Loading API keys from .env.auth..."
    export $(cat .env.auth | grep -v '^#' | grep -v '^$' | xargs)
else
    echo "❌ .env.auth file not found!"
    exit 1
fi

# Set empty values for unset API keys
export API_KEY_1=${API_KEY_1:-""}
export API_KEY_2=${API_KEY_2:-""}
export API_KEY_3=${API_KEY_3:-""}

echo "✅ API Keys loaded:"
[ -n "$API_KEY_1" ] && echo "   - API_KEY_1: ${API_KEY_1:0:10}..."
[ -n "$API_KEY_2" ] && echo "   - API_KEY_2: ${API_KEY_2:0:10}..."
[ -n "$API_KEY_3" ] && echo "   - API_KEY_3: ${API_KEY_3:0:10}..."

# Process the template
echo "📝 Processing nginx.conf.template..."
envsubst '${API_KEY_1} ${API_KEY_2} ${API_KEY_3}' < nginx.conf.template > nginx.conf.test

# Clean up empty entries
echo "🧹 Cleaning up empty API key entries..."
sed -i '/^\s*""\s*1;/d' nginx.conf.test

echo "✅ Generated nginx.conf.test successfully!"
echo ""
echo "🔍 API key map section:"
echo "======================"
grep -A 10 "map \$http_x_api_key \$api_key_valid" nginx.conf.test

echo ""
echo "💡 To use this configuration:"
echo "   1. Copy nginx.conf.test to nginx.conf"
echo "   2. Or restart docker-compose to use the automated version"
echo ""
echo "🧪 Test with: docker-compose restart nginx-proxy"
