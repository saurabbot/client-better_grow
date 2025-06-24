# 🐳 Docker Setup for Shipra Backend

This guide explains how to run the Shipra Backend application using Docker and Docker Compose.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- 10GB free disk space

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd shipra-backend
```

### 2. Environment Configuration
Create a `.env` file with your API keys:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token

# Frappe Configuration
FRAPPE_API_KEY=your_frappe_api_key
FRAPPE_API_SECRET=your_frappe_api_secret
FRAPPE_BASE_URL=https://your-frappe-instance.com

# Optional: Override defaults
HOST=0.0.0.0
PORT=8000
```

### 3. Start the Application
```bash
# Using Makefile (recommended)
make dev

# Or using Docker Compose directly
docker-compose up -d
```

### 4. Verify Installation
```bash
# Check health
make health

# Check service status
make status

# View logs
make logs
```

## 🏗️ Architecture

The Docker setup includes:

- **shipra-backend**: Main FastAPI application
- **postgres**: PostgreSQL database
- **redis**: Redis cache and session storage
- **nginx**: Reverse proxy (production profile)
- **prometheus**: Metrics collection (monitoring profile)
- **grafana**: Monitoring dashboard (monitoring profile)

## 🔧 Available Commands

### Using Makefile
```bash
# Development
make dev          # Start development environment
make run-dev      # Start development services
make logs         # View application logs
make shell        # Open shell in container

# Production
make prod         # Start production environment
make run-prod     # Start production with nginx
make deploy       # Deploy with production config

# Monitoring
make monitor      # Start monitoring stack
make grafana      # Show monitoring URLs

# Database
make db-shell     # Access PostgreSQL shell
make db-backup    # Backup database
make db-restore   # Restore database

# Maintenance
make clean        # Remove containers and volumes
make stop         # Stop all services
make status       # Show service status
```

### Using Docker Compose Directly
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Start specific profiles
docker-compose --profile dev up -d
docker-compose --profile monitoring up -d
docker-compose --profile production up -d

# View logs
docker-compose logs -f shipra-backend

# Stop services
docker-compose down
```

## 🌍 Environment Profiles

### Development Profile
```bash
docker-compose --profile dev up -d
```
- Application on port 8001
- Hot reload enabled
- Source code mounted for live editing
- Development dependencies included

### Production Profile
```bash
docker-compose --profile production up -d
```
- Nginx reverse proxy
- SSL termination
- Load balancing
- Production optimizations

### Monitoring Profile
```bash
docker-compose --profile monitoring up -d
```
- Prometheus metrics collection
- Grafana dashboards
- Application monitoring
- Performance tracking

## 📊 Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| Application | http://localhost:8000 | Main API |
| Development | http://localhost:8001 | Dev environment |
| Health Check | http://localhost:8000/health | Service health |
| Readiness | http://localhost:8000/ready | Service readiness |
| Grafana | http://localhost:3000 | Monitoring dashboard |
| Prometheus | http://localhost:9090 | Metrics collection |

## 🔍 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
lsof -i :8000

# Stop conflicting services
sudo systemctl stop conflicting-service
```

#### 2. Database Connection Issues
```bash
# Check database status
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

#### 3. Memory Issues
```bash
# Check available memory
free -h

# Increase Docker memory limit
# In Docker Desktop: Settings > Resources > Memory
```

#### 4. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix Docker permissions
sudo usermod -aG docker $USER
```

### Debug Commands
```bash
# Check container status
docker-compose ps

# View all logs
docker-compose logs -f

# Check resource usage
docker stats

# Inspect container
docker-compose exec shipra-backend /bin/bash
```

## 🔒 Security Considerations

### Production Deployment
1. **Change default passwords** in `.env`
2. **Enable SSL/TLS** with proper certificates
3. **Configure firewall** rules
4. **Use secrets management** for sensitive data
5. **Enable authentication** for admin endpoints

### Environment Variables
```bash
# Required for production
POSTGRES_PASSWORD=strong_password_here
REDIS_PASSWORD=strong_redis_password
JWT_SECRET_KEY=your_jwt_secret
```

## 📈 Monitoring and Logging

### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping
```

### Log Management
```bash
# View structured logs
docker-compose logs -f shipra-backend

# Export logs
docker-compose logs shipra-backend > app.log

# Log rotation (configure in docker-compose.yml)
```

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy with Docker Compose
        run: |
          docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [PostgreSQL Docker Guide](https://hub.docker.com/_/postgres)
- [Redis Docker Guide](https://hub.docker.com/_/redis)

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Check Docker and system resources
4. Create an issue in the repository 