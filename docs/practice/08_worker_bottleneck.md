# 08 Worker Bottleneck

## 1. 실습 목적
- 소비자(worker) 병목을 재현하고 queue backlog 관측 방법을 익힌다.
- 이 실습으로 배우는 개념: 생산-소비 불균형, 큐 깊이, 처리량 병목 해소 전략.

## 2. 시나리오 설명
- worker replica를 1로 고정하고 높은 입력 부하를 준다.
- `jobs:queue` 길이 증가와 처리 지연을 관찰한다.

## 3. 사전 조건
- API 포트포워드

```bash
kubectl -n kubeserve-lab port-forward svc/api 18080:8000
```

- worker replica 고정

```bash
kubectl -n kubeserve-lab scale deploy/worker --replicas=1
```

## 4. 실행 명령어 (kubectl / bash 포함)
```bash
# 1) 부하 인가
docker run --rm -i \
  -v "$PWD:/work" -w /work \
  grafana/k6 run tests/load/k6_jobs.js \
  -e BASE_URL=http://host.docker.internal:18080 \
  -e VUS=100 -e DURATION=2m

# 2) queue depth 반복 관찰
REDIS_POD=$(kubectl -n kubeserve-lab get pod -l app=redis -o jsonpath='{.items[0].metadata.name}')
for i in {1..20}; do
  kubectl -n kubeserve-lab exec "$REDIS_POD" -- redis-cli LLEN jobs:queue
  sleep 3
done

# 3) 개선 실험: worker scale-out
kubectl -n kubeserve-lab scale deploy/worker --replicas=4
```

## 5. 관찰 포인트 (metrics, logs, 상태 변화)
- Queue depth: `LLEN jobs:queue`
- Prometheus
  - `rate(gateway_jobs_created_total[1m])` vs `rate(worker_jobs_processed_total[1m])`
  - `worker_inflight_jobs`
  - `histogram_quantile(0.95, sum(rate(worker_job_processing_seconds_bucket[5m])) by (le))`
- Worker 로그
  - 처리 완료 속도와 실패 로그

## 6. 예상 결과
- 입력률 > 처리률이면 queue depth가 증가한다.
- worker scale-out 후 backlog 증가율이 둔화되거나 감소한다.

## 7. 문제 발생 시 체크 방법
```bash
kubectl -n kubeserve-lab get pods -l app=worker
kubectl -n kubeserve-lab logs deploy/worker --tail=200
kubectl -n kubeserve-lab get hpa worker
```
- backlog가 줄지 않으면 DB/Redis 병목도 함께 의심한다.

## 8. 추가 실험 아이디어
- worker sleep(1~3s)을 코드에서 3~5s로 바꿔 병목을 더 크게 만든다.
- worker CPU limit을 낮춰 병목 원인을 CPU로 전환해본다.
