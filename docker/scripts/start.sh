#!/bin/bash

# Script to start Docker containers
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}Starting Docker containers...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check if Docker Compose is installed
COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        echo -e "${RED}Error: Docker Compose is not installed${NC}"
        exit 1
    fi
fi

# Change to docker directory
cd "$DOCKER_DIR"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Creating .env from .env.example if it exists...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env file with your configuration${NC}"
    else
        echo -e "${RED}Error: .env.example not found. Please create .env file${NC}"
        exit 1
    fi
fi

# Start containers
echo -e "${YELLOW}Starting containers...${NC}"
$COMPOSE_CMD up -d

# Wait a bit for services to start
sleep 5

# Show status
echo -e "${GREEN}Containers started!${NC}"
echo ""
echo "Container status:"
$COMPOSE_CMD ps

echo ""
echo -e "${GREEN}Services:${NC}"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
echo "  PostgreSQL: localhost:5432"

