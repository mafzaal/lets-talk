#!/bin/sh

# Startup script for nginx with environment variable substitution
# This script processes the nginx.conf.template and creates nginx.conf with actual values

echo "🔧 Starting nginx with environment variable substitution..."

# Check if required environment variables are set
if [ -z "$API_KEY_1" ] && [ -z "$API_KEY_2" ] && [ -z "$API_KEY_3" ]; then
    echo "❌ Error: No API keys found in environment variables"
    echo "   Please set at least one of: API_KEY_1, API_KEY_2, API_KEY_3"
    echo "   Check your .env.auth file and docker-compose.yml configuration"
    exit 1
fi

# Set empty values for unset API keys to avoid envsubst errors
export API_KEY_1=${API_KEY_1:-""}
export API_KEY_2=${API_KEY_2:-""}
export API_KEY_3=${API_KEY_3:-""}

# Set default values for CORS domains if not provided
export CORS_DOMAIN_1=${CORS_DOMAIN_1:-""}
export CORS_DOMAIN_2=${CORS_DOMAIN_2:-""}
export CORS_DOMAIN_3=${CORS_DOMAIN_3:-""}

echo "✅ Found API keys:"
[ -n "$API_KEY_1" ] && echo "   - API_KEY_1: ${API_KEY_1:0:10}..."
[ -n "$API_KEY_2" ] && echo "   - API_KEY_2: ${API_KEY_2:0:10}..."
[ -n "$API_KEY_3" ] && echo "   - API_KEY_3: ${API_KEY_3:0:10}..."

echo "✅ Found CORS domains:"
[ -n "$CORS_DOMAIN_1" ] && echo "   - CORS_DOMAIN_1: $CORS_DOMAIN_1"
[ -n "$CORS_DOMAIN_2" ] && echo "   - CORS_DOMAIN_2: $CORS_DOMAIN_2"
[ -n "$CORS_DOMAIN_3" ] && echo "   - CORS_DOMAIN_3: $CORS_DOMAIN_3"

# Create the nginx configuration from template
echo "📝 Generating nginx.conf from template..."
envsubst '${API_KEY_1} ${API_KEY_2} ${API_KEY_3} ${CORS_DOMAIN_1} ${CORS_DOMAIN_2} ${CORS_DOMAIN_3}' < /etc/nginx/nginx.conf.template > /tmp/nginx.conf

# Clean up empty API key entries from the map
echo "🧹 Cleaning up empty API key entries..."
sed -i '/^\s*""\s*1;/d' /tmp/nginx.conf

# Clean up empty CORS domain checks
echo "🧹 Cleaning up empty CORS domain checks..."
sed -i '/if.*~\*.*\${}\$/d' /tmp/nginx.conf

# Move the cleaned configuration to the final location
mv /tmp/nginx.conf /etc/nginx/nginx.conf

# Validate the generated configuration
echo "🔍 Validating nginx configuration..."
if nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration validation failed"
    echo "Generated configuration:"
    cat /etc/nginx/nginx.conf
    exit 1
fi

# Start nginx
echo "🚀 Starting nginx..."
exec nginx -g 'daemon off;'
