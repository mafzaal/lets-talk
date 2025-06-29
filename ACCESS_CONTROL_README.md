# LangGraph API Access Control Configuration

This setup provides access control for the LangGraph API, allowing anonymous access to the `/threads` endpoint while requiring authentication for all other endpoints.

## Overview

- **Public Access**: `/threads` endpoint is accessible to anonymous users
- **Authenticated Access**: All other endpoints require a valid API key
- **Rate Limiting**: Different rate limits for public and authenticated endpoints
- **CORS Support**: Proper CORS headers for browser-based requests

## Setup

### 1. Configure API Keys

Edit the `.env.auth` file and set your API keys:

```bash
# Replace with your actual API keys
API_KEY_1=your-secure-admin-key-12345
API_KEY_2=your-dev-team-key-67890
```

### 2. Update API Keys

The API keys are automatically loaded from the `.env.auth` file. Edit this file and set your API keys:

```bash
# Replace with your actual API keys  
API_KEY_1=your_api_key_1
API_KEY_2=your_api_key_2
API_KEY_3=your_api_key_3
```

The nginx configuration will automatically use these environment variables - no manual editing of nginx.conf required!

### 3. Start the Services

```bash
docker-compose up -d
```

## Usage

### Public Access (No Authentication Required)

The `/threads` endpoint is publicly accessible:

```bash
# Get threads
curl http://localhost:8123/threads

# Create a new thread
curl -X POST http://localhost:8123/threads \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"user_id": "anonymous"}}'

# Get a specific thread
curl http://localhost:8123/threads/{thread_id}
```

### Health Check (Public)

```bash
curl http://localhost:8123/health
```

### Authenticated Access

All other endpoints require the `X-API-Key` header:

```bash
# Access documentation
curl http://localhost:8123/docs \
  -H "X-API-Key: your-secure-admin-key-12345"

# Access other LangGraph endpoints
curl http://localhost:8123/runs \
  -H "X-API-Key: your-secure-admin-key-12345"

# Pipeline endpoints
curl http://localhost:8123/pipeline/status \
  -H "X-API-Key: your-secure-admin-key-12345"
```

## Rate Limits

- **Public endpoints**: 30 requests per minute per IP
- **Authenticated endpoints**: 100 requests per minute per IP
- **Burst allowances**: 
  - Public: 10 requests
  - Authenticated: 50 requests

## Security Features

1. **API Key Validation**: Only predefined keys are accepted
2. **Rate Limiting**: Prevents abuse and DoS attacks  
3. **CORS Headers**: Proper cross-origin support
4. **Security Headers**: XSS protection, content type sniffing protection
5. **Error Responses**: Clear JSON error messages

## Customization

### Adding New API Keys

1. Add the key to `.env.auth`
2. Restart the nginx-proxy service: `docker-compose restart nginx-proxy`

The nginx configuration template will automatically pick up the new keys from the environment variables.

### Adjusting Rate Limits

Edit the `limit_req_zone` directives in `nginx.conf`:

```nginx
# 60 requests per minute for public API
limit_req_zone $binary_remote_addr zone=public_api:10m rate=60r/m;

# 200 requests per minute for authenticated API  
limit_req_zone $binary_remote_addr zone=auth_api:10m rate=200r/m;
```

### Adding More Public Endpoints

To make additional endpoints public, add location blocks:

```nginx
location /another-public-endpoint {
    limit_req zone=public_api burst=10 nodelay;
    proxy_pass http://langgraph_api;
    # ... other proxy settings
}
```

## Monitoring

### Check nginx logs

```bash
docker-compose logs nginx-proxy
```

### Check access patterns

```bash
# See recent requests
docker-compose logs nginx-proxy | tail -50

# Monitor in real-time
docker-compose logs -f nginx-proxy
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check that you're including the `X-API-Key` header with a valid key
2. **Rate Limited**: Wait for the rate limit window to reset or increase limits
3. **CORS Issues**: Ensure the nginx configuration includes proper CORS headers

### Testing the Setup

```bash
# Test public access (should work)
curl -v http://localhost:8123/threads

# Test private access without key (should return 401)
curl -v http://localhost:8123/docs

# Test private access with key (should work)
curl -v http://localhost:8123/docs -H "X-API-Key: your-secure-admin-key-12345"
```

## Production Notes

- Use strong, unique API keys in production
- Consider implementing JWT tokens for more sophisticated authentication
- Add logging and monitoring for security events
- Use HTTPS in production environments
- Consider using a proper secrets management system for API keys
