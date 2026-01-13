#!/bin/bash
set -e

# Clockwork Hamlet Deployment Script
# Usage: ./scripts/deploy.sh [local|fly]

DEPLOY_TARGET="${1:-local}"

echo "=== Clockwork Hamlet Deployment ==="
echo "Target: $DEPLOY_TARGET"
echo ""

case $DEPLOY_TARGET in
    local)
        echo "Building and starting local Docker containers..."

        # Build images
        docker-compose build

        # Start services
        docker-compose up -d

        echo ""
        echo "Services started!"
        echo "  Frontend: http://localhost:3000"
        echo "  Backend:  http://localhost:8000"
        echo "  Health:   http://localhost:8000/api/health"
        echo ""
        echo "Use 'docker-compose logs -f' to view logs"
        echo "Use 'docker-compose down' to stop services"
        ;;

    fly)
        echo "Deploying to Fly.io..."

        # Check if flyctl is installed
        if ! command -v flyctl &> /dev/null; then
            echo "Error: flyctl is not installed"
            echo "Install it with: curl -L https://fly.io/install.sh | sh"
            exit 1
        fi

        # Deploy backend
        echo "Deploying backend..."
        cd backend
        flyctl deploy --app clockwork-hamlet-api
        cd ..

        # Deploy frontend
        echo "Deploying frontend..."
        cd frontend
        flyctl deploy --app clockwork-hamlet
        cd ..

        echo ""
        echo "Deployment complete!"
        echo "  Frontend: https://clockwork-hamlet.fly.dev"
        echo "  Backend:  https://clockwork-hamlet-api.fly.dev"
        ;;

    *)
        echo "Unknown deployment target: $DEPLOY_TARGET"
        echo "Usage: ./scripts/deploy.sh [local|fly]"
        exit 1
        ;;
esac
