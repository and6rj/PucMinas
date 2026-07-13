#!/usr/bin/env bash
# Aplica todos os manifests na ordem correta.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

kubectl apply -f "${DIR}/k8s/00-namespace.yaml"
kubectl apply -f "${DIR}/k8s/01-secret.yaml"
kubectl apply -f "${DIR}/k8s/02-postgres.yaml"
kubectl apply -f "${DIR}/k8s/03-backend.yaml"
kubectl apply -f "${DIR}/k8s/04-frontend.yaml"
kubectl apply -f "${DIR}/k8s/05-backend-hpa.yaml"

echo
echo "Aguardando pods ficarem Ready..."
kubectl wait --for=condition=available --timeout=180s \
  deployment/postgres deployment/backend deployment/frontend \
  -n guess-game

echo
kubectl get pods,svc,hpa -n guess-game
echo
echo "Para acessar o frontend:"
echo "  kubectl port-forward -n guess-game svc/frontend 8081:80"
echo "Em seguida abra: http://localhost:8081"
