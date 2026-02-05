# 🐳 Project Nexus Backend - Containerization Guide

## 📋 Overview
The Project Nexus backend is fully containerized with Docker and Docker Compose for easy deployment and development.

## 🏗️ Container Structure

### 📁 Files Included
- ✅ `Dockerfile` - Multi-stage build for production-ready image
- ✅ `docker-compose.yml` - Complete service orchestration
- ✅ `.dockerignore` - Optimized build context

### 🐋 Docker Features
- **Multi-stage build** - Smaller production image
- **Non-root user** - Enhanced security
- **Health checks** - Automatic monitoring
- **Volume persistence** - Data and logs retention
- **Environment variables** - Secure configuration
- **Network isolation** - Service communication

## 🚀 Quick Start

### Prerequisites
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin
```

### Development Setup
```bash
# Clone and navigate to backend
cd /home/khushpatel/Documents/Capstone\ Project/backend

# Build and start the container
docker compose up --build

# Or run in background
docker compose up -d --build
```

### Production Deployment
```bash
# Production build
docker compose -f docker-compose.yml up --build -d

# Check logs
docker compose logs -f

# Stop services
docker compose down
```

## 📊 Container Details

### 🔧 Environment Variables
- All variables loaded from `.env` file
- Secure API keys and configuration
- Database connections and external services

### 📁 Volume Mounts
- `logs_data:/app/logs` - Persistent log storage
- `./data:/app/data` - File uploads and imports

### 🌐 Network Configuration
- **Port**: 8000 (mapped to host)
- **Network**: `nexus_network` (isolated bridge)
- **Health Check**: `/health` endpoint every 30s

### 🔍 Health Monitoring
```bash
# Check container health
docker compose ps

# View health logs
docker inspect project_nexus_backend | grep Health -A 10
```

## 🛠️ Development Workflow

### 🔄 Hot Reload (Development)
```bash
# Mount source code for development
docker compose -f docker-compose.dev.yml up
```

### 📦 Build Optimization
```bash
# Rebuild without cache
docker compose build --no-cache

# View build layers
docker history project_nexus_backend
```

### 🐛 Debugging
```bash
# Enter container shell
docker compose exec backend bash

# View real-time logs
docker compose logs -f backend

# Check resource usage
docker stats project_nexus_backend
```

## 📈 Production Considerations

### 🔒 Security
- ✅ Non-root user execution
- ✅ Read-only filesystem (optional)
- ✅ Resource limits (optional)
- ✅ Secrets management

### ⚡ Performance
- ✅ Multi-stage builds
- ✅ Layer caching optimization
- ✅ Health checks with timeouts
- ✅ Graceful shutdown handling

### 📊 Monitoring
- ✅ Health endpoint monitoring
- ✅ Log aggregation
- ✅ Metrics collection
- ✅ Alerting integration

## 🔄 CI/CD Integration

### 🚀 Automated Deployment
```yaml
# Example GitHub Actions
- name: Build and Deploy
  run: |
    docker compose build
    docker compose up -d
```

### 📋 Container Registry
```bash
# Tag and push to registry
docker tag project_nexus_backend your-registry/nexus-backend:latest
docker push your-registry/nexus-backend:latest
```

## 🆘 Troubleshooting

### Common Issues
1. **Port conflicts**: Change host port mapping
2. **Permission errors**: Check Docker daemon permissions
3. **Environment issues**: Verify `.env` file exists
4. **Health check failures**: Check application startup logs

### Debug Commands
```bash
# Container status
docker compose ps

# Detailed container info
docker inspect project_nexus_backend

# Resource usage
docker stats

# Clean up
docker system prune -f
```

## 📚 Additional Services

### 🗄️ Database Integration
```yaml
# Example with MongoDB
services:
  mongodb:
    image: mongo:7
    volumes:
      - mongodb_data:/data/db
    networks:
      - nexus_network
```

### 🔍 Monitoring Stack
```yaml
# Example with Prometheus
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
```

---

**🎉 The backend is now fully containerized and ready for production deployment!**
