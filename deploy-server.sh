#!/bin/bash
# Simple deployment script for gil-bot unified container

set -e

echo "🚀 Deploying Gil Bot..."

# Stop and remove existing container if it exists
docker stop gil-bot 2>/dev/null || true
docker rm gil-bot 2>/dev/null || true

# Create gil-network if it doesn't exist
docker network create gil-network 2>/dev/null || true

if ! docker ps | grep -q gil-bot-mongo; then
    echo "📦 Starting MongoDB..."
    docker run -d \
        --name gil-bot-mongo \
        --restart always \
        -v mongo_data:/data/db \
        -e MONGO_INITDB_DATABASE=${MONGODB_DB_NAME:-gil_whatsapp_bot} \
        -e MONGO_INITDB_USERNAME=${MONGO_USER:-user} \
        -e MONGO_INITDB_PASSWORD=${MONGO_PASSWORD:-pass} \
        --network gil-network \
        mongo:latest
fi

# Pull latest image
echo "📥 Pulling latest image..."
docker pull registry.yosefbyd.com/gil-bot:latest

# Start gil-bot container
echo "🏃 Starting Gil Bot container..."
docker run -d \
    --name gil-bot \
    --restart always \
    --network proxy \
    --network gil-network \
    -e DEBUG=${DEBUG:-True} \
    -e PYTHONUNBUFFERED=${PYTHONUNBUFFERED:-1} \
    -e MONGODB_DB_NAME=${MONGODB_DB_NAME:-gil_whatsapp_bot} \
    -e MONGO_USER=${MONGO_USER:-user} \
    -e MONGO_PASSWORD=${MONGO_PASSWORD:-pass} \
    -e OPENAI_API_KEY=${OPENAI_API_KEY} \
    -e ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} \
    -l traefik.enable=true \
    -l traefik.http.services.gil-bot.loadbalancer.server.port=8000 \
    -l traefik.http.routers.gil-bot.rule=Host\(\`gil-bot.yosefbyd.com\`\) \
    -l traefik.docker.network=proxy \
    registry.yosefbyd.com/gil-bot:latest

echo "✅ Gil Bot deployed successfully!"
echo "🌐 Available at: https://gil-bot.yosefbyd.com"
echo "📊 Check status: docker logs gil-bot" 