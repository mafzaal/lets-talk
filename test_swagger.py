#!/usr/bin/env python3
"""
Test script to verify the API starts correctly and Swagger docs are accessible.
"""
import asyncio
import aiohttp
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

async def test_api_endpoints():
    """Test that the API is running and Swagger docs are accessible."""
    base_url = "http://localhost:8000"
    
    endpoints_to_test = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/examples/items"
    ]
    
    async with aiohttp.ClientSession() as session:
        print("Testing API endpoints...")
        
        for endpoint in endpoints_to_test:
            url = f"{base_url}{endpoint}"
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        print(f"✅ {endpoint} - OK ({response.status})")
                        
                        # Special handling for specific endpoints
                        if endpoint == "/openapi.json":
                            json_data = await response.json()
                            print(f"   - OpenAPI version: {json_data.get('openapi', 'unknown')}")
                            print(f"   - API title: {json_data.get('info', {}).get('title', 'unknown')}")
                            print(f"   - API version: {json_data.get('info', {}).get('version', 'unknown')}")
                            
                        elif endpoint == "/examples/items":
                            json_data = await response.json()
                            print(f"   - Example items count: {len(json_data)}")
                            
                    else:
                        print(f"❌ {endpoint} - Failed ({response.status})")
                        
            except aiohttp.ClientError as e:
                print(f"❌ {endpoint} - Connection error: {e}")
            except Exception as e:
                print(f"❌ {endpoint} - Error: {e}")

def print_swagger_info():
    """Print information about accessing Swagger documentation."""
    print("\n" + "="*60)
    print("🎉 Swagger Documentation Setup Complete!")
    print("="*60)
    print()
    print("📚 Access your API documentation at:")
    print("   • Swagger UI:  http://localhost:8000/docs")
    print("   • ReDoc:       http://localhost:8000/redoc")
    print("   • OpenAPI:     http://localhost:8000/openapi.json")
    print()
    print("🔧 Key Features Added:")
    print("   • Enhanced OpenAPI metadata with contact info and license")
    print("   • Comprehensive endpoint documentation with examples")
    print("   • Request/response model documentation")
    print("   • Tagged endpoints for better organization")
    print("   • Example endpoints demonstrating best practices")
    print()
    print("🚀 To start the API server:")
    print("   cd backend")
    print("   uv run uvicorn lets_talk.api.main:app --reload --host 0.0.0.0 --port 8000")
    print()
    print("📖 Example API calls to try:")
    print("   • GET  /health                    - System health check")
    print("   • GET  /scheduler/status          - Scheduler statistics")
    print("   • GET  /examples/items            - List example items")
    print("   • GET  /examples/items/1          - Get specific item")
    print("   • POST /examples/items            - Create new item")
    print()

if __name__ == "__main__":
    print_swagger_info()
    
    # Only test if the user wants to
    import os
    if os.getenv("TEST_API", "").lower() in ("true", "1", "yes"):
        print("Testing API endpoints (make sure the server is running)...")
        asyncio.run(test_api_endpoints())
    else:
        print("💡 Set TEST_API=true to test the endpoints automatically")
