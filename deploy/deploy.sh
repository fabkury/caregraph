#!/usr/bin/env bash
#
# CareGraph deploy script — rsync + atomic symlink swap.
#
# Uploads site/dist/ to the VPS and atomically swaps the Nginx root.
# Keeps the last 3 releases for rollback.
#
# Configuration: set these in .env.deploy (gitignored) or as env vars:
#   VPS_HOST    — hostname or IP of the VPS
#   VPS_USER    — SSH user on the VPS (default: deploy)
#   REMOTE_PATH — base path on VPS (default: /var/www/caregraph)
#
# Usage:
#   bash deploy/deploy.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load config from .env.deploy if it exists
ENV_FILE="${REPO_ROOT}/.env.deploy"
if [[ -f "$ENV_FILE" ]]; then
    echo "[deploy] Loading config from .env.deploy"
    set -a
    source "$ENV_FILE"
    set +a
fi

# Configuration with defaults
VPS_HOST="${VPS_HOST:?Error: VPS_HOST not set. Set it in .env.deploy or as an env var.}"
VPS_USER="${VPS_USER:-deploy}"
REMOTE_PATH="${REMOTE_PATH:-/var/www/caregraph}"

DIST_DIR="${REPO_ROOT}/site/dist"
TS=$(date +%Y%m%d-%H%M%S)
RELEASE_DIR="${REMOTE_PATH}/releases/${TS}"

# Verify dist/ exists
if [[ ! -d "$DIST_DIR" ]]; then
    echo "[error] ${DIST_DIR} does not exist. Run 'cd site && npm run build' first."
    exit 1
fi

echo "[deploy] Deploying to ${VPS_USER}@${VPS_HOST}:${RELEASE_DIR}"
echo "[deploy] Timestamp: ${TS}"

# 1. Upload the new release.
#    --link-dest hardlinks unchanged files from the live release,
#    keeping VPS disk usage close to one full release.
echo "[deploy] Step 1: rsync to ${RELEASE_DIR}/"
rsync -avz --delete \
    --link-dest="${REMOTE_PATH}/current/" \
    "${DIST_DIR}/" \
    "${VPS_USER}@${VPS_HOST}:${RELEASE_DIR}/"

# 2. Atomically swap the symlink. Nginx follows it on the next request.
echo "[deploy] Step 2: Atomic symlink swap"
ssh "${VPS_USER}@${VPS_HOST}" "ln -sfn ${RELEASE_DIR} ${REMOTE_PATH}/current"

# 3. Prune old releases, keeping the last 3 for rollback.
echo "[deploy] Step 3: Pruning old releases (keeping last 3)"
ssh "${VPS_USER}@${VPS_HOST}" \
    "cd ${REMOTE_PATH}/releases && ls -1t | tail -n +4 | xargs -r rm -rf"

echo "[deploy] Done. Live at ${REMOTE_PATH}/current -> ${RELEASE_DIR}"
