#!/bin/bash

# AssetTrack Build and Push Script
# Builds all services and pushes to Harbor registry

set -e

# Configuration
HARBOR_REGISTRY="${HARBOR_REGISTRY:-192.168.0.70/assettrack}"
HARBOR_USERNAME="${HARBOR_USERNAME:-admin}"
HARBOR_PASSWORD="${HARBOR_PASSWORD:-Harbor12345}"
TAG="${TAG:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Login to Harbor
login_harbor() {
    log_info "Logging into Harbor registry..."
    echo "$HARBOR_PASSWORD" | docker login "$HARBOR_REGISTRY" -u "$HARBOR_USERNAME" --password-stdin
}

# Build and push a service
build_and_push() {
    local service_name=$1
    local context=$2
    local dockerfile=$3
    
    log_info "Building $service_name..."
    
    # Build image
    docker build -t "$HARBOR_REGISTRY/$service_name:$TAG" \
        -f "$context/$dockerfile" \
        "$context"
    
    log_info "Pushing $service_name to Harbor..."
    docker push "$HARBOR_REGISTRY/$service_name:$TAG"
    
    log_info "$service_name build and push completed"
}

# Main build process
main() {
    log_info "Starting AssetTrack build and push process..."
    log_info "Registry: $HARBOR_REGISTRY"
    log_info "Tag: $TAG"
    
    # Login to Harbor
    login_harbor
    
    # Build and push all services
    build_and_push "agent-service" "app/agent-service" "Dockerfile"
    build_and_push "collector-service" "app/collector-service" "Dockerfile"
    build_and_push "processor-service" "app/processor-service" "Dockerfile"
    build_and_push "api-service" "app/api-service" "Dockerfile"
    build_and_push "webapp-ui" "app/webapp-ui/frontend" "Dockerfile"
    
    log_info "All services built and pushed successfully!"
    
    # Display summary
    echo
    log_info "Build Summary:"
    echo "  - agent-service: $HARBOR_REGISTRY/agent-service:$TAG"
    echo "  - collector-service: $HARBOR_REGISTRY/collector-service:$TAG"
    echo "  - processor-service: $HARBOR_REGISTRY/processor-service:$TAG"
    echo "  - api-service: $HARBOR_REGISTRY/api-service:$TAG"
    echo "  - webapp-ui: $HARBOR_REGISTRY/webapp-ui:$TAG"
}

# Handle errors
trap 'log_error "Build failed with exit code $?"' ERR

# Run main function
main "$@"

