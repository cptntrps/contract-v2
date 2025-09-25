#!/bin/bash
"""
Full system startup script for Contract Analyzer with async processing

This script starts:
1. Redis server (background)
2. Celery worker (background) 
3. Flask web application (foreground)
"""

set -e

echo "=== Contract Analyzer Full System Startup ==="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Redis is available
if ! command -v redis-server &> /dev/null; then
    echo "Warning: Redis not found. Installing Redis..."
    sudo apt-get update && sudo apt-get install -y redis-server
fi

# Start Redis server in background
echo "Starting Redis server..."
redis-server --daemonize yes --port 6379

# Wait for Redis to start
sleep 2

# Check Redis connection
if redis-cli ping | grep -q "PONG"; then
    echo "Redis server started successfully"
else
    echo "Error: Failed to start Redis server"
    exit 1
fi

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A app.async_processing.celery_app worker --loglevel=info --detach --pidfile=celery_worker.pid

# Wait for worker to start
sleep 3

# Check if Celery worker is running
if [ -f "celery_worker.pid" ]; then
    echo "Celery worker started successfully (PID: $(cat celery_worker.pid))"
else
    echo "Warning: Celery worker may not have started properly"
fi

# Create cleanup function
cleanup() {
    echo ""
    echo "=== Shutting down system ==="
    
    # Stop Celery worker
    if [ -f "celery_worker.pid" ]; then
        echo "Stopping Celery worker..."
        celery -A app.async_processing.celery_app control shutdown
        rm -f celery_worker.pid
    fi
    
    # Stop Redis
    echo "Stopping Redis server..."
    redis-cli shutdown || true
    
    echo "System shutdown complete"
    exit 0
}

# Set trap for cleanup on script exit
trap cleanup EXIT INT TERM

# Start Flask application (foreground)
echo "Starting Flask application..."
echo "Dashboard will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the system"
echo ""

python3 run_app.py