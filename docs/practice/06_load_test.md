# 06 Load Test

## 1. 실습 목적
- 부하 테스트로 지연/에러율/처리량 변화를 수치로 확인한다.
- 이 실습으로 배우는 개념: baseline 측정, SLO 지표 해석, 병목 탐색 시작점.

## 2. 시나리오 설명
- 제공된 k6 스크립트(`tests/load/k6_jobs.js`)로 API에 지속 요청을 보낸다.
- 요청량(VUS)을 단계적으로 올리며 성능 변화를 기록한다.

## 3. 사전 조건
- API 포트포워드

```bash
kubectl -n kubeserve-lab port-forward svc/api 18080:8000
```

- Prometheus/Grafana 포트포워드

```bash
kubectl -n kubeserve-lab port-forward svc/prometheus 9090:9090
kubectl -n kubeserve-lab port-forward svc/grafana 3000:3000
```

## 4. 실행 명령어 (kubectl / bash 포함)
```bash
# 1) 기본 부하
make load-test

# 2) 강한 부하
docker run --rm -i \
  -v "$PWD:/work" -w /work \
  grafana/k6 run tests/load/k6_jobs.js \
  -e BASE_URL=http://host.docker.internal:18080 \
  -e VUS=30 -e DURATION=2m

# 3) 더 높은 부하
docker run --rm -i \
  -v "$PWD:/work" -w /work \
  grafana/k6 run tests/load/k6_jobs.js \
  -e BASE_URL=http://host.docker.internal:18080 \
  -e VUS=60 -e DURATION=2m
```

## 5. 관찰 포인트 (metrics, logs, 상태 변화)
- 핵심 지표
  - latency: `histogram_quantile(0.95, sum(rate(gateway_job_submit_latency_seconds_bucket[5m])) by (le))`
  - error rate: `rate(gateway_jobs_failed_total[1m]) / clamp_min(rate(gateway_jobs_created_total[1m]), 1)`
  - throughput: `rate(gateway_jobs_created_total[1m])`
  - worker 처리율: `rate(worker_jobs_processed_total[1m])`
- Redis queue depth

```bash
REDIS_POD=$(kubectl -n kubeserve-lab get pod -l app=redis -o jsonpath='{.items[0].metadata.name}')
kubectl -n kubeserve-lab exec "$REDIS_POD" -- redis-cli LLEN jobs:queue
```

## 6. 예상 결과
- VUS 증가에 따라 p95 latency와 queue depth가 증가한다.
- worker 처리율이 입력률을 못 따라가면 backlog가 쌓인다.

## 7. 문제 발생 시 체크 방법
```bash
kubectl -n kubeserve-lab top pods
kubectl -n kubeserve-lab get hpa
kubectl -n kubeserve-lab logs deploy/gateway-api --tail=200
kubectl -n kubeserve-lab logs deploy/worker --tail=200
```
- k6에서 연결 실패 시 포트포워드와 URL을 먼저 확인한다.

## 8. 추가 실험 아이디어
- worker replica를 1/2/4로 바꿔 backlog 감소 속도를 비교한다.
- CPU limit을 낮춰 throttling이 latency에 미치는 영향을 본다.
