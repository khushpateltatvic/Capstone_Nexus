# 🚀 Project Nexus Backend - Deployment Script

#!/bin/bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="project-nexus"
BACKEND_DIR="/home/khushpatel/Documents/Capstone Project/backend"
CONTAINER_NAME="project_nexus_backend"
PORT="8000"

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  INFO: $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ SUCCESS: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        log_error ".env file not found in $BACKEND_DIR"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

build_image() {
    log_info "Building Docker image..."
    cd "$BACKEND_DIR"
    
    docker compose build --no-cache
    log_success "Docker image built successfully"
}

start_container() {
    log_info "Starting container..."
    cd "$BACKEND_DIR"
    
    # Stop existing container if running
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        log_warning "Container $CONTAINER_NAME is already running. Stopping it first..."
        docker compose down
    fi
    
    # Start new container
    docker compose up -d
    
    log_success "Container started successfully"
}

wait_for_health() {
    log_info "Waiting for container to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:$PORT/health &> /dev/null; then
            log_success "Container is healthy and ready!"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: Container not ready yet..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Container failed to become healthy after $max_attempts attempts"
    return 1
}

show_status() {
    log_info "Container status:"
    docker compose ps
    
    echo ""
    log_info "Recent logs:"
    docker compose logs --tail=20 backend
}

deploy_development() {
    log_info "🚀 Deploying to DEVELOPMENT environment..."
    
    check_prerequisites
    build_image
    start_container
    
    if wait_for_health; then
        show_status
        log_success "🎉 Development deployment completed successfully!"
        log_info "🌐 Backend is available at: http://localhost:$PORT"
        log_info "📊 Health check: http://localhost:$PORT/health"
    else
        log_error "❌ Development deployment failed!"
        exit 1
    fi
}

deploy_production() {
    log_info "🚀 Deploying to PRODUCTION environment..."
    
    # Production-specific checks
    check_prerequisites
    
    # Additional production checks
    log_info "Running production-specific checks..."
    
    # Check if port is available
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
        log_error "Port $PORT is already in use. Please stop the existing service first."
        exit 1
    fi
    
    build_image
    start_container
    
    if wait_for_health; then
        log_success "🎉 Production deployment completed successfully!"
        log_info "🌐 Backend is available at: http://localhost:$PORT"
        log_info "📊 Health check: http://localhost:$PORT/health"
        
        # Additional production monitoring
        log_info "Setting up monitoring..."
        # Add monitoring setup here
        
    else
        log_error "❌ Production deployment failed!"
        exit 1
    fi
}

rollback() {
    log_warning "🔄 Rolling back deployment..."
    
    cd "$BACKEND_DIR"
    docker compose down
    
    # You could implement version-specific rollback here
    log_info "Rollback completed. Container stopped."
}

cleanup() {
    log_info "🧹 Cleaning up Docker resources..."
    
    cd "$BACKEND_DIR"
    docker compose down -v
    docker system prune -f
    
    log_success "Cleanup completed"
}

show_help() {
    echo "🐳 Project Nexus Backend Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev         Deploy to development environment"
    echo "  prod        Deploy to production environment"
    echo "  rollback    Rollback deployment (stop container)"
    echo "  cleanup     Clean up Docker resources"
    echo "  status      Show container status"
    echo "  logs        Show container logs"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev      # Deploy to development"
    echo "  $0 prod     # Deploy to production"
    echo "  $0 status   # Check container status"
}

# Main script logic
case "${1:-help}" in
    "dev")
        deploy_development
        ;;
    "prod")
        deploy_production
        ;;
    "rollback")
        rollback
        ;;
    "cleanup")
        cleanup
        ;;
    "status")
        show_status
        ;;
    "logs")
        cd "$BACKEND_DIR"
        docker compose logs -f backend
        ;;
    "help"|*)
        show_help
        ;;
esac
