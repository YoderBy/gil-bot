#!/bin/bash
# Deploy Gil Bot on the server

# Stop and remove existing container if it exists
docker stop gil-bot 2>/dev/null || true
docker rm gil-bot 2>/dev/null || true

# Pull the latest image
docker pull registry.yosefbyd.com/gil-bot:latest

# Run the container
docker run -d \
  --name gil-bot \
  --restart=always \
  --network proxy \
  -e DEBUG="${DEBUG:-False}" \
  -e PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
  -e WHATSAPP_API_KEY="${WHATSAPP_API_KEY}" \
  -e WHATSAPP_PHONE_NUMBER="${WHATSAPP_PHONE_NUMBER}" \
  -l "traefik.enable=true" \
  -l "traefik.http.services.gil-bot.loadbalancer.server.port=8000" \
  -l "traefik.http.routers.gil-bot.rule=Host(\`gil-bot.yosefbyd.com\`)" \
  -l "traefik.docker.network=proxy" \
  registry.yosefbyd.com/gil-bot:latest

echo "Gil Bot deployed! Check https://gil-bot.yosefbyd.com" 