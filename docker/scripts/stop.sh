#!/bin/bash

# Script to stop Docker containers
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}Stopping Docker containers...${NC}"

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

# Parse arguments
REMOVE_CONTAINERS=false
if [ "$1" == "--remove" ] || [ "$1" == "-r" ]; then
    REMOVE_CONTAINERS=true
fi

# Stop containers
if [ "$REMOVE_CONTAINERS" = true ]; then
    echo -e "${YELLOW}Stopping and removing containers...${NC}"
    $COMPOSE_CMD down
else
    echo -e "${YELLOW}Stopping containers (keeping them)...${NC}"
    $COMPOSE_CMD stop
fi

echo -e "${GREEN}Containers stopped!${NC}"

