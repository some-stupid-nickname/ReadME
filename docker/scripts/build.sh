#!/bin/bash

# Script to build all Docker images
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$DOCKER_DIR")"

echo -e "${GREEN}Building Docker images...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Change to docker directory
cd "$DOCKER_DIR"

# Build images
echo -e "${YELLOW}Building backend image...${NC}"
docker build -f Dockerfile.backend -t rag-backend:latest "$PROJECT_ROOT"

echo -e "${YELLOW}Building frontend image...${NC}"
docker build -f Dockerfile.frontend -t rag-frontend:latest "$PROJECT_ROOT"

echo -e "${YELLOW}Building telegram-bot image...${NC}"
docker build -f Dockerfile.telegram-bot -t rag-telegram-bot:latest "$PROJECT_ROOT"

echo -e "${GREEN}All images built successfully!${NC}"
echo ""
echo "Built images:"
docker images | grep "rag-" || echo "No images found"

