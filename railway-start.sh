#!/bin/bash

# Railway startup script for Shipra Backend

# Get port from Railway environment variable
PORT=${PORT:-8000}

echo "Starting Shipra Backend on port $PORT"

# Start the application
exec uvicorn src.main:app --host 0.0.0.0 --port $PORT 