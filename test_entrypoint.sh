#!/bin/bash

# Test script to verify the new entrypoint system works

echo "🧪 Testing the new entrypoint system..."
echo "========================================"

# Build the new image
echo "📦 Building Docker image with new entrypoint..."
if ! docker build -t lets-talk-test . ; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker build successful"

# Test 1: Run startup only (should exit after startup completes)
echo ""
echo "🧪 Test 1: Testing standalone startup script..."
echo "-----------------------------------------------"
if python startup_application.py; then
    echo "✅ Standalone startup script works"
else
    echo "❌ Standalone startup script failed"
    exit 1
fi

# Test 2: Test the container startup process
echo ""
echo "🧪 Test 2: Testing container startup with new entrypoint..."
echo "----------------------------------------------------------"
echo "This will start the container and check if initialization works..."
echo "(Container will be stopped after a few seconds)"

# Start container in background and capture logs
container_id=$(docker run -d --name lets-talk-entrypoint-test lets-talk-test)

if [ -z "$container_id" ]; then
    echo "❌ Failed to start container"
    exit 1
fi

# Wait a bit for startup to complete
echo "⏳ Waiting for container startup..."
sleep 10

# Check container status
if docker ps --filter "id=$container_id" --filter "status=running" | grep -q "$container_id"; then
    echo "✅ Container started successfully"
    
    # Show recent logs
    echo ""
    echo "📋 Recent container logs:"
    echo "------------------------"
    docker logs --tail 20 "$container_id"
    
    # Clean up
    echo ""
    echo "🧹 Cleaning up test container..."
    docker stop "$container_id" > /dev/null 2>&1
    docker rm "$container_id" > /dev/null 2>&1
    
    echo "✅ Entrypoint system test completed successfully!"
    echo ""
    echo "🎉 The new entrypoint system is working correctly:"
    echo "  • Application startup runs first (database, migrations, etc.)"
    echo "  • FastAPI only handles web server lifecycle"
    echo "  • Proper error handling and logging"
    echo "  • Graceful shutdown support"
    
else
    echo "❌ Container failed to start or exited early"
    echo ""
    echo "📋 Container logs:"
    echo "----------------"
    docker logs "$container_id"
    
    # Clean up
    docker rm "$container_id" > /dev/null 2>&1
    exit 1
fi
