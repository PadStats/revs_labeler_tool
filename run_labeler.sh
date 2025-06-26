#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# build-and-run helper for the Streamlit Property Labeler
# -----------------------------------------------------------------------------
# Usage:
#   ./run_labeler.sh path/to/service_account.json  [--build]
#
# • Reads .env from the repository root (edit as needed).
# • Mounts the given key inside the container at /secrets/key.json (read-only).
# • Optionally rebuilds the Docker image when --build is passed.
# -----------------------------------------------------------------------------

set -euo pipefail

IMAGE_NAME=property-labeler

# -----------------------------------------------------------------------------
# Key-file discovery
# -----------------------------------------------------------------------------

KEY_PATH="${SERVICE_ACCOUNT_JSON:-}"   # 1) from env var if exported

# 2) from .env (already loaded by docker via --env-file, but we need it now)
if [[ -z "$KEY_PATH" ]]; then
  KEY_PATH=$(grep -E '^SERVICE_ACCOUNT_JSON=' .env 2>/dev/null | cut -d'=' -f2- | tr -d '"') || true
fi

# 3) first positional argument
if [[ -z "$KEY_PATH" && -n "${1:-}" && "${1:-}" != "--build" ]]; then
  KEY_PATH=$1
  shift                     # consume the path argument
fi

if [[ -z "$KEY_PATH" || ! -f "$KEY_PATH" ]]; then
  echo "Usage: $0 /path/to/key.json [--build]  OR  set SERVICE_ACCOUNT_JSON env var or .env entry" >&2
  exit 1
fi

# --build flag can appear with or without key path
if [[ "${1:-}" == "--build" ]]; then
  docker build -t "$IMAGE_NAME" ./ || exit 1
  shift
fi

docker run --rm \
  --env-file .env \
  -v "$(realpath "$KEY_PATH")":/secrets/key.json:ro \
  -p 8501:8501 \
  "$IMAGE_NAME" 