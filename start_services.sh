#!/bin/bash

# BD Law Assistant - Service Startup Script
# Starts the required services in the correct order

echo "==============================================="
echo "BD Law Assistant - Starting Services"
echo "==============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Function to start services
start_services() {
    echo "Starting infrastructure services..."
    docker-compose up -d redis postgres

    echo "Waiting for services to be healthy..."
    sleep 10

    echo "Starting scraper services..."
    docker-compose up -d scraper scraper-scheduler web-ui

    echo ""
    echo "==============================================="
    echo "Services started successfully!"
    echo "==============================================="
    echo ""
    echo "Access points:"
    echo "  - Web UI: http://localhost:5000"
    echo "  - Redis: localhost:6379"
    echo "  - PostgreSQL: localhost:5432"
    echo ""
    echo "To view logs: docker-compose logs -f [service_name]"
    echo "To stop all services: docker-compose down"
    echo "==============================================="
}

# Function to run locally (development mode)
run_local() {
    echo "Starting services locally (development mode)..."

    # Start Redis if not running
    if ! nc -z localhost 6379 2>/dev/null; then
        echo "Starting Redis..."
        redis-server --port 6379 --daemonize yes
    fi

    # Start the web UI
    echo "Starting web UI..."
    cd services/scraper
    python web_crawler_app.py &

    echo ""
    echo "==============================================="
    echo "Local services started!"
    echo "==============================================="
    echo ""
    echo "Access the Web UI at: http://localhost:5000"
    echo "==============================================="
}

# Parse command line arguments
case "$1" in
    local)
        run_local
        ;;
    docker)
        start_services
        ;;
    *)
        echo "Usage: $0 {local|docker}"
        echo "  local  - Run services locally (development)"
        echo "  docker - Run services in Docker containers"
        exit 1
        ;;
esac