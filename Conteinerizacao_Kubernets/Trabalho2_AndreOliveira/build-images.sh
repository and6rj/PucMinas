#!/usr/bin/env bash
# Constrói as imagens localmente com as mesmas tags do Docker Hub (sem push).
# Uso normal do laboratório: imagens já estão no Hub — use só ./apply.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DOCKER_USER="${DOCKER_USER:-and6rj}"
TAG="${IMAGE_TAG:-latest}"
BACKEND_IMAGE="${DOCKER_USER}/and6rj-guess-game-backend:${TAG}"
FRONTEND_IMAGE="${DOCKER_USER}/and6rj-guess-game-frontend:${TAG}"

echo "==> Backend (${BACKEND_IMAGE})"
docker build \
  -t "${BACKEND_IMAGE}" \
  -f "${ROOT}/guess_game/Dockerfile" \
  "${ROOT}/guess_game"

echo "==> Frontend (${FRONTEND_IMAGE})"
docker build \
  -t "${FRONTEND_IMAGE}" \
  -f "${ROOT}/nginx/Dockerfile" \
  "${ROOT}"

echo "Imagens locais prontas. Para publicar: ./push-images.sh"
