#!/usr/bin/env bash
set -Eeuo pipefail

NAMESPACE="microservices"
PRODUCT_PORT="18001"
ORDER_PORT="18002"
PRODUCT_PID=""
ORDER_PID=""

cleanup() {
  if [[ -n "$PRODUCT_PID" ]]; then
    kill "$PRODUCT_PID" 2>/dev/null || true
  fi

  if [[ -n "$ORDER_PID" ]]; then
    kill "$ORDER_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT

wait_for_url() {
  local url="$1"
  local attempts=0

  until curl --silent --fail "$url" >/dev/null; do
    attempts=$((attempts + 1))

    if [[ "$attempts" -ge 30 ]]; then
      echo "ERROR: Timed out waiting for $url"
      return 1
    fi

    sleep 1
  done
}

echo "==> Checking Kubernetes context"
kubectl config current-context

echo "==> Applying application configuration"
kubectl apply -f k8s/order-service-config.yaml

echo "==> Applying Product Service"
kubectl apply -f k8s/product-service.yaml

echo "==> Applying Order Service"
kubectl apply -f k8s/order-service.yaml

echo "==> Waiting for rollouts"
kubectl rollout status deployment/product-service \
  -n "$NAMESPACE" --timeout=120s
kubectl rollout status deployment/order-service \
  -n "$NAMESPACE" --timeout=120s

echo "==> Starting temporary port forwards"
kubectl port-forward -n "$NAMESPACE" \
  service/product-service "$PRODUCT_PORT:8000" \
  >/tmp/product-port-forward.log 2>&1 &
PRODUCT_PID=$!

kubectl port-forward -n "$NAMESPACE" \
  service/order-service "$ORDER_PORT:8000" \
  >/tmp/order-port-forward.log 2>&1 &
ORDER_PID=$!

echo "==> Waiting for API endpoints"
wait_for_url "http://127.0.0.1:$PRODUCT_PORT/health"
wait_for_url "http://127.0.0.1:$ORDER_PORT/health"

echo "==> Checking Product Service health"
curl --silent --show-error --fail \
  "http://127.0.0.1:$PRODUCT_PORT/health"
echo

echo "==> Checking Product Service product lookup"
curl --silent --show-error --fail \
  "http://127.0.0.1:$PRODUCT_PORT/products/1"
echo

echo "==> Checking Order Service dependency call"
ORDER_RESPONSE=$(curl --silent --show-error --fail \
  "http://127.0.0.1:$ORDER_PORT/orders/demo")

echo "$ORDER_RESPONSE"

if ! grep -q '"total":2500' <<< "$ORDER_RESPONSE"; then
  echo "ERROR: Unexpected demo order total"
  exit 1
fi

echo "==> Deployment and smoke tests passed"
