#!/usr/bin/env bash
# Publica as imagens no Docker Hub (usuário and6rj).
#   and6rj/and6rj-guess-game-backend:latest
#   and6rj/and6rj-guess-game-frontend:latest
#
# Pré-requisito: docker login (usuário and6rj)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DOCKER_USER="${DOCKER_USER:-and6rj}"
TAG="${IMAGE_TAG:-latest}"
BACKEND_IMAGE="${DOCKER_USER}/and6rj-guess-game-backend:${TAG}"
FRONTEND_IMAGE="${DOCKER_USER}/and6rj-guess-game-frontend:${TAG}"

echo "==> Build backend → ${BACKEND_IMAGE}"
docker build \
  -t "${BACKEND_IMAGE}" \
  -f "${ROOT}/guess_game/Dockerfile" \
  "${ROOT}/guess_game"

echo "==> Build frontend → ${FRONTEND_IMAGE}"
docker build \
  -t "${FRONTEND_IMAGE}" \
  -f "${ROOT}/nginx/Dockerfile" \
  "${ROOT}"

echo "==> Push ${BACKEND_IMAGE}"
docker push "${BACKEND_IMAGE}"

echo "==> Push ${FRONTEND_IMAGE}"
docker push "${FRONTEND_IMAGE}"

echo
echo "Imagens públicas no Docker Hub:"
echo "  https://hub.docker.com/r/${DOCKER_USER}/and6rj-guess-game-backend"
echo "  https://hub.docker.com/r/${DOCKER_USER}/and6rj-guess-game-frontend"
echo
echo "No cluster (ex.: k3d-meu-cluster) basta: ./apply.sh"
echo "Não é necessário rebuild nem k3d image import."
