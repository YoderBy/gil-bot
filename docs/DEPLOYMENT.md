# Gil WhatsApp Bot Deployment Guide

This guide provides step-by-step instructions for deploying the Gil WhatsApp Bot to the homelab infrastructure using the CI/CD stack.

## Prerequisites

1. **GitHub CLI** installed and authenticated:
   ```bash
   brew install gh  # or apt install gh
   gh auth login
   ```

2. **Access to the homelab server** (10.0.0.13) with Docker and the proxy network already set up

3. **Cloudflare account** with the domain configured and tunnel created

## Initial Setup

### 1. Create and Configure Environment File

1. Copy the example environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Edit `backend/.env` and fill in the actual values:
   - `MONGODB_URL`: Update with actual MongoDB credentials
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `WHATSAPP_API_TOKEN`: Your WhatsApp API token (if applicable)
   - `JWT_SECRET_KEY`: Generate a secure random string
   - `CLOUDFLARE_TOKEN`: Your Cloudflare tunnel token

### 2. Upload Secrets to GitHub

Upload all environment variables to GitHub:
```bash
# Upload the entire .env file as a single secret
gh secret set ENV_FILE --repo YourGitHubUser/Gil-Whatsapp-Bot < backend/.env

# Or use the helper script to upload individual variables
chmod +x scripts/upload_env_to_github.sh
./scripts/upload_env_to_github.sh backend/.env YourGitHubUser/Gil-Whatsapp-Bot
```

Upload deployment credentials:
```bash
# Set deployment user (your server username)
gh secret set DEPLOY_USER --repo YourGitHubUser/Gil-Whatsapp-Bot -b "yoder"

# Set deployment host
gh secret set DEPLOY_HOST --repo YourGitHubUser/Gil-Whatsapp-Bot -b "10.0.0.13"

# Set SSH key for deployment
gh secret set DEPLOY_SSH_KEY --repo YourGitHubUser/Gil-Whatsapp-Bot < ~/.ssh/id_ed25519

# Set registry credentials
gh secret set REGISTRY_USER --repo YourGitHubUser/Gil-Whatsapp-Bot -b "yoder"
gh secret set REGISTRY_PASS --repo YourGitHubUser/Gil-Whatsapp-Bot -b "your-registry-password"
```

### 3. Initial Manual Deployment

For the first deployment, you need to manually start the containers on the server:

1. SSH into the server:
   ```bash
   ssh yoder@10.0.0.13
   ```

2. Create the application directory:
   ```bash
   sudo mkdir -p /opt/gil-bot
   sudo chown $USER:$USER /opt/gil-bot
   cd /opt/gil-bot
   ```

3. Copy the production docker-compose file:
   ```bash
   # From your local machine
   scp docker-compose.prod.yml yoder@10.0.0.13:/opt/gil-bot/docker-compose.yml
   ```

4. Copy the .env file:
   ```bash
   # From your local machine
   scp backend/.env yoder@10.0.0.13:/opt/gil-bot/.env
   ```

5. On the server, ensure you're logged into the registry:
   ```bash
   docker login registry.yosefbyd.com
   # Enter username: yoder
   # Enter password: your-registry-password
   ```

6. Start the containers:
   ```bash
   cd /opt/gil-bot
   docker compose pull
   docker compose up -d
   ```

## Continuous Deployment

After the initial setup, the CI/CD pipeline will automatically:

1. **Build and push images** when you push to the `main` branch
2. **Deploy updates** to the server automatically
3. **Watchtower** will monitor and update running containers

To trigger a deployment:
```bash
git add .
git commit -m "Deploy Gil WhatsApp Bot"
git push origin main
```

## Service URLs

Once deployed, your services will be available at:

- **Frontend**: https://gil-bot.yosefbyd.com
- **Backend API**: https://gil-bot-api.yosefbyd.com
- **API Documentation**: https://gil-bot-api.yosefbyd.com/docs

## Monitoring and Troubleshooting

### Check Service Status

```bash
# On the server
cd /opt/gil-bot
docker compose ps
docker compose logs -f
```

### View Traefik Dashboard

Access the Traefik dashboard at http://10.0.0.13:8080/dashboard/ to see routing status.

### Common Issues

1. **502 Bad Gateway**: Check if containers are running and properly labeled for Traefik
2. **Container not starting**: Check logs with `docker compose logs <service>`
3. **MongoDB connection issues**: Verify MongoDB credentials in .env file
4. **Image pull failures**: Ensure registry login is successful

### Useful Commands

```bash
# Restart services
docker compose restart

# View logs for specific service
docker compose logs -f backend

# Check container health
docker compose ps

# Force recreate containers
docker compose up -d --force-recreate
```

## Updating the Application

1. Make your code changes
2. Commit and push to `main` branch
3. GitHub Actions will build and push new images
4. Watchtower will automatically update the running containers

## Security Notes

- Keep your `.env` file secure and never commit it to Git
- Regularly update your dependencies and base images
- Use strong passwords for all services
- Consider implementing Cloudflare Access policies for sensitive endpoints 