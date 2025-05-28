#!/usr/bin/env bash
# ------------------------------------------------------------
# upload_env_to_github.sh
# Uploads all .env variables as GitHub secrets for CI/CD
# ------------------------------------------------------------
set -euo pipefail

REPO="YoderBy/gil-bot"
ENV_FILE="/Users/user/projects/personal/gil-bot-clean/.env"

echo "Setting up secrets for repository: $REPO"
echo "Using .env file: $ENV_FILE"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed. Install it first."
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub. Run: gh auth login"
    exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

echo "Uploading secrets from $ENV_FILE to $REPO..."

while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ -z "$key" || "$key" =~ ^# ]] && continue
    # Remove possible surrounding quotes from value
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"
    echo "Setting $key"
    gh secret set "$key" --repo "$REPO" -b "$value"
done < "$ENV_FILE"

echo "✅ All secrets from $ENV_FILE have been set up in $REPO!"
echo ""
echo "You can view and manage them at:"
echo "https://github.com/YoderBy/gil-bot/settings/secrets/actions"