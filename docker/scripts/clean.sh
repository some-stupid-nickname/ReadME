#!/bin/bash

# Script to clean Docker containers, images, and volumes
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}Cleaning Docker resources...${NC}"

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
CLEAN_VOLUMES=false
CLEAN_IMAGES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --volumes|-v)
            CLEAN_VOLUMES=true
            shift
            ;;
        --images|-i)
            CLEAN_IMAGES=true
            shift
            ;;
        --all|-a)
            CLEAN_VOLUMES=true
            CLEAN_IMAGES=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Stop and remove containers
echo -e "${YELLOW}Stopping and removing containers...${NC}"
$COMPOSE_CMD down

# Remove volumes if requested
if [ "$CLEAN_VOLUMES" = true ]; then
    echo -e "${YELLOW}Removing volumes...${NC}"
    $COMPOSE_CMD down -v
    echo -e "${RED}Warning: All data in volumes will be lost!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        docker volume ls | grep rag- | awk '{print $2}' | xargs -r docker volume rm || true
        echo -e "${GREEN}Volumes removed${NC}"
    else
        echo -e "${YELLOW}Volumes removal cancelled${NC}"
    fi
fi

# Remove images if requested
if [ "$CLEAN_IMAGES" = true ]; then
    echo -e "${YELLOW}Removing images...${NC}"
    docker images | grep "rag-" | awk '{print $3}' | xargs -r docker rmi -f || true
    echo -e "${GREEN}Images removed${NC}"
fi

# Clean up unused resources
echo -e "${YELLOW}Cleaning up unused Docker resources...${NC}"
docker system prune -f

echo -e "${GREEN}Cleanup completed!${NC}"

