#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-kubeserve-lab}"
LOCAL_PORT="${LOCAL_PORT:-18080}"

cleanup() {
  if [[ -n "${PF_PID:-}" ]] && kill -0 "$PF_PID" >/dev/null 2>&1; then
    kill "$PF_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "[smoke] waiting for api rollout..."
kubectl -n "$NAMESPACE" rollout status deploy/gateway-api --timeout=180s

echo "[smoke] port-forward service/api to localhost:${LOCAL_PORT}"
kubectl -n "$NAMESPACE" port-forward svc/api "${LOCAL_PORT}:8000" >/tmp/kubeserve-port-forward.log 2>&1 &
PF_PID=$!
sleep 2

echo "[smoke] live check"
curl -fsS "http://127.0.0.1:${LOCAL_PORT}/live" >/dev/null

echo "[smoke] ready check"
curl -fsS "http://127.0.0.1:${LOCAL_PORT}/ready" >/dev/null

echo "[smoke] enqueue job"
JOB_ID=$(curl -fsS -X POST "http://127.0.0.1:${LOCAL_PORT}/jobs" \
  -H 'content-type: application/json' \
  -d '{"hello":"world"}' | sed -E 's/.*"job_id":"([^"]+)".*/\1/')

echo "[smoke] job_id=${JOB_ID}"

for i in {1..20}; do
  STATUS=$(curl -fsS "http://127.0.0.1:${LOCAL_PORT}/jobs/${JOB_ID}" | sed -E 's/.*"status":"([^"]+)".*/\1/')
  if [[ "$STATUS" == "completed" ]]; then
    echo "[smoke] completed"
    exit 0
  fi
  sleep 1
done

echo "[smoke] timeout waiting for completion"
exit 1
