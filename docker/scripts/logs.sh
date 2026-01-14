#!/bin/bash

# Script to view Docker container logs
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

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
SERVICE=""
FOLLOW=false
TAIL=100

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -t|--tail)
            TAIL="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        *)
            if [ -z "$SERVICE" ]; then
                SERVICE="$1"
            fi
            shift
            ;;
    esac
done

# Show logs
if [ -n "$SERVICE" ]; then
    echo -e "${GREEN}Showing logs for service: $SERVICE${NC}"
    if [ "$FOLLOW" = true ]; then
        $COMPOSE_CMD logs -f --tail="$TAIL" "$SERVICE"
    else
        $COMPOSE_CMD logs --tail="$TAIL" "$SERVICE"
    fi
else
    echo -e "${GREEN}Showing logs for all services${NC}"
    if [ "$FOLLOW" = true ]; then
        $COMPOSE_CMD logs -f --tail="$TAIL"
    else
        $COMPOSE_CMD logs --tail="$TAIL"
    fi
fi

