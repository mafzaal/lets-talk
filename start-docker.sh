#!/bin/bash
# Script to set environment variables and manage Docker Compose

# Set default command if no argument provided
COMMAND=${1:-"up -d"}



# Load environment variables from .env.prod if it exists
if [ -f ".env.prod" ]; then
    set -a  # automatically export all variables
    source .env.prod
    set +a  # disable automatic export
    echo "Loaded environment variables from .env.prod"
else
    echo "Warning: .env.prod file not found"
fi

# Set environment variables to override


# Function to display usage
usage() {
    echo "Usage: $0 [COMMAND]"
    echo "Commands:"
    echo "  up -d    Start services in detached mode (default)"
    echo "  down     Stop and remove containers"
    echo "  build    Build and start services"
    echo "  restart  Restart services"
    echo "  logs     Show logs"
    echo ""
    echo "Examples:"
    echo "  $0 'up -d'    # Start services in background"
    echo "  $0 down       # Stop all services"
    echo "  $0 'up -d --build'  # Build and start services"
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
    exit 0
fi

echo "Executing: docker compose $COMMAND"

# Execute the docker compose command
case "$COMMAND" in
    "up -d"|"up -d --build")
        docker compose down
        docker compose $COMMAND
        ;;
    "down")
        docker compose down
        ;;
    "build")
        docker compose down
        docker compose up -d --build
        ;;
    "restart")
        docker compose restart
        ;;
    "logs")
        docker compose logs -f
        ;;
    *)
        echo "Executing custom command: docker compose $COMMAND"
        docker compose $COMMAND
        ;;
esac
