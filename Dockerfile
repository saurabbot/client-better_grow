# Multi-stage Dockerfile for Shipra Backend (Railway Optimized)
# Stage 1: Base Python image with system dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Stage 2: Dependencies
FROM base as dependencies

# Set work directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Production
FROM dependencies as production

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY pyproject.toml .
COPY setup.py .
COPY railway-start.sh .

# Make startup script executable
RUN chmod +x railway-start.sh

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Set proper permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (Railway will set PORT environment variable)
EXPOSE 8000

# Default command (Railway will override PORT)
CMD ["./railway-start.sh"] 