#!/usr/bin/env bash
# Reads a local .env file and pushes each key=value pair to GitHub secrets
# Usage: ./scripts/upload_env_to_github.sh [path/to/.env] [owner/repo]

set -euo pipefail

ENV_PATH="${1:-.env}"
REPO="${2:-}" # optional second arg

if [[ ! -f "$ENV_PATH" ]]; then
  echo "[ERROR] Env file '$ENV_PATH' not found" >&2
  exit 1
fi

# Auto-detect repo if not supplied
if [[ -z "$REPO" ]]; then
  ORIGIN_URL=$(git config --get remote.origin.url || true)
  if [[ -z "$ORIGIN_URL" ]]; then
    echo "[ERROR] Could not detect git remote; please pass OWNER/REPO as second argument" >&2
    exit 1
  fi
  REPO=$(echo "$ORIGIN_URL" | sed -E 's#(git@|https://)github.com[:/](.*)(\.git)?#\2#')
fi

echo "Uploading secrets to $REPO from $ENV_PATH ..."

while IFS='=' read -r KEY VALUE; do
  [[ -z "$KEY" || "$KEY" =~ ^\s*# ]] && continue
  KEY=$(echo "$KEY" | xargs)
  VALUE=$(echo "$VALUE" | xargs)
  if [[ -z "$VALUE" ]]; then
    echo "[WARN] Skipping $KEY (no value)"
    continue
  fi
  echo "Setting secret $KEY ..."
  printf "%s" "$VALUE" | gh secret set "$KEY" --repo "$REPO" --body - >/dev/null
done < "$ENV_PATH"

echo "✅  Done. Secrets uploaded." 