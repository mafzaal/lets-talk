# API Documentation

This document provides information about the Let's Talk API and its comprehensive Swagger documentation.

## Accessing the Documentation

Once you start the API server, you can access the interactive documentation at:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)  
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## Starting the API Server

```bash
cd backend
uv run uvicorn lets_talk.api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints Overview

### Health Endpoints (`/health`)
- **GET /health** - System health check with scheduler status

### Scheduler Endpoints (`/scheduler`)
- **GET /scheduler/status** - Get comprehensive scheduler statistics
- **GET /scheduler/jobs** - List all scheduled jobs
- **POST /scheduler/jobs/cron** - Create cron-based scheduled jobs
- **POST /scheduler/jobs/interval** - Create interval-based scheduled jobs
- **POST /scheduler/jobs/onetime** - Create one-time scheduled jobs
- **DELETE /scheduler/jobs/{job_id}** - Remove scheduled jobs
- **POST /scheduler/jobs/{job_id}/run** - Manually trigger job execution

### Pipeline Endpoints (`/pipeline`)
- Various pipeline management and execution endpoints

### Example Endpoints (`/examples`)
- **GET /examples/items** - List example items with filtering
- **GET /examples/items/{item_id}** - Get specific item by ID
- **POST /examples/items** - Create new example item
- **DELETE /examples/items/{item_id}** - Delete example item

## Documentation Features

### Enhanced OpenAPI Metadata
- Comprehensive API description with feature overview
- Contact information and license details
- Server configuration for development and production
- Security scheme definitions for future authentication

### Detailed Endpoint Documentation
- Clear summaries and descriptions for each endpoint
- Request/response examples with realistic data
- Parameter documentation with validation rules
- Error response documentation with example payloads

### Request/Response Models
- Pydantic models with field descriptions and examples
- Input validation with clear error messages
- Enum values for status fields and other constrained data
- Comprehensive JSON schema generation

### Organized by Tags
- **health**: System monitoring and status endpoints
- **scheduler**: Background task management
- **pipeline**: AI processing workflow management
- **examples**: Demonstration endpoints with best practices

## API Design Patterns

### Standard REST Operations
The API follows REST conventions:
- `GET` for retrieving data
- `POST` for creating resources
- `DELETE` for removing resources
- `PUT/PATCH` for updating resources (where implemented)

### Consistent Response Formats
- Success responses include relevant data
- Error responses follow RFC 7807 problem details format
- HTTP status codes follow standard conventions

### Query Parameters
- Filtering: `?status=active`
- Pagination: `?limit=10&offset=0`
- Searching: `?tags=ai,demo`

### Path Parameters
- Resource identification: `/items/{item_id}`
- Action specification: `/jobs/{job_id}/run`

## Authentication (Future)
Currently, the API does not require authentication. Future versions may include:
- API Key authentication via headers
- JWT Bearer token authentication
- OAuth 2.0 integration

## Rate Limiting (Future)
Rate limiting is planned for future versions to prevent API abuse and ensure fair usage.

## Testing the API

### Using the Interactive Documentation
1. Navigate to the Swagger UI at `/docs`
2. Expand any endpoint section
3. Click "Try it out" button
4. Fill in required parameters
5. Click "Execute" to test the endpoint

### Using curl
```bash
# Health check
curl -X GET "http://localhost:8000/health"

# List example items
curl -X GET "http://localhost:8000/examples/items"

# Create new item
curl -X POST "http://localhost:8000/examples/items" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "description": "A test item", "tags": ["test"]}'

# Get scheduler status
curl -X GET "http://localhost:8000/scheduler/status"
```

### Using Python requests
```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# List items with filtering
response = requests.get("http://localhost:8000/examples/items?status=active&limit=5")
print(response.json())

# Create new item
data = {
    "name": "API Test Item",
    "description": "Created via Python requests",
    "tags": ["python", "api", "test"]
}
response = requests.post("http://localhost:8000/examples/items", json=data)
print(response.json())
```

## Error Handling

The API returns standard HTTP status codes:

- **200 OK**: Successful GET, PUT, PATCH requests
- **201 Created**: Successful POST requests that create resources
- **204 No Content**: Successful DELETE requests
- **400 Bad Request**: Invalid request data or parameters
- **404 Not Found**: Requested resource does not exist
- **422 Unprocessable Entity**: Request validation errors
- **500 Internal Server Error**: Unexpected server errors

Error responses include detailed information:
```json
{
  "detail": "Item with ID 999 not found"
}
```

For validation errors:
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```
