#!/bin/bash
# Docker management script for IT Admin Agent

# Set default environment
ENV=${ENV:-prod}

# Determine which docker-compose files to use
if [ "$ENV" == "dev" ]; then
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
    echo "Using development environment"
else
    COMPOSE_FILES="-f docker-compose.yml"
    echo "Using production environment"
fi

# Check for .env file
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before continuing."
    exit 1
fi

# Function to display help
function show_help {
    echo "IT Admin Agent Docker Management Script"
    echo ""
    echo "Usage: $0 [OPTIONS] COMMAND"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV    Set environment (dev or prod, default: prod)"
    echo "  -h, --help       Show this help message"
    echo ""
    echo "Commands:"
    echo "  up               Start all containers"
    echo "  down             Stop and remove all containers"
    echo "  restart          Restart all containers"
    echo "  build            Build all images"
    echo "  logs             Show logs from all containers"
    echo "  ps               Show container status"
    echo "  shell            Open a shell in the main container"
    echo "  test             Run tests in the main container"
    echo "  clean            Remove all containers, volumes, and images"
    echo ""
    echo "Examples:"
    echo "  $0 --env dev up      Start in development mode"
    echo "  $0 logs              Show logs in production mode"
    echo "  $0 shell             Open a shell in the main container"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENV="$2"
            if [ "$ENV" == "dev" ]; then
                COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
                echo "Using development environment"
            else
                COMPOSE_FILES="-f docker-compose.yml"
                echo "Using production environment"
            fi
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

# Execute commands
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

case "$1" in
    up)
        echo "Starting containers..."
        docker-compose $COMPOSE_FILES up -d
        ;;
    down)
        echo "Stopping containers..."
        docker-compose $COMPOSE_FILES down
        ;;
    restart)
        echo "Restarting containers..."
        docker-compose $COMPOSE_FILES restart
        ;;
    build)
        echo "Building images..."
        docker-compose $COMPOSE_FILES build
        ;;
    logs)
        echo "Showing logs..."
        docker-compose $COMPOSE_FILES logs -f
        ;;
    ps)
        echo "Container status:"
        docker-compose $COMPOSE_FILES ps
        ;;
    shell)
        echo "Opening shell in main container..."
        docker-compose $COMPOSE_FILES exec itadmin bash
        ;;
    test)
        echo "Running tests..."
        docker-compose $COMPOSE_FILES exec itadmin python -m pytest
        ;;
    clean)
        echo "Removing all containers, volumes, and images..."
        docker-compose $COMPOSE_FILES down -v --rmi all
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac 