# 02 Redis Failure

## 1. 실습 목적
- Redis 중단이 API enqueue/worker 처리에 미치는 영향을 확인한다.
- 이 실습으로 배우는 개념: 의존성 장애 전파, readiness 의미, 실패율 관측.

## 2. 시나리오 설명
- Redis Deployment를 0으로 스케일 다운한다.
- `POST /jobs` 실패와 `/ready` 503 변화를 관찰한다.

## 3. 사전 조건
- API 포트포워드

```bash
kubectl -n kubeserve-lab port-forward svc/api 18080:8000
```

- 현재 Redis 상태 확인

```bash
kubectl -n kubeserve-lab get pods -l app=redis
```

## 4. 실행 명령어 (kubectl / bash 포함)
```bash
# 1) Redis 중단
kubectl -n kubeserve-lab scale deploy/redis --replicas=0
kubectl -n kubeserve-lab get pods -l app=redis -w

# 2) readiness 확인
curl -i http://127.0.0.1:18080/ready

# 3) job enqueue 시도
curl -i -X POST http://127.0.0.1:18080/jobs \
  -H 'content-type: application/json' \
  -d '{"case":"redis_down"}'

# 4) Redis 복구
kubectl -n kubeserve-lab scale deploy/redis --replicas=1
kubectl -n kubeserve-lab rollout status deploy/redis
```

## 5. 관찰 포인트 (metrics, logs, 상태 변화)
- API 로그: `kubectl -n kubeserve-lab logs deploy/gateway-api -f`
- Worker 로그: `kubectl -n kubeserve-lab logs deploy/worker -f`
- Prometheus
  - `rate(gateway_jobs_failed_total[1m])`
  - `rate(gateway_jobs_created_total[1m])`
  - `up{job="gateway-api"}`
- Grafana
  - Gateway 실패/지연 패널

## 6. 예상 결과
- Redis 중단 시 `/ready`는 503으로 내려간다.
- `POST /jobs`는 5xx가 증가한다.
- Redis 복구 후 재시도하면 enqueue가 정상 동작한다.

## 7. 문제 발생 시 체크 방법
```bash
kubectl -n kubeserve-lab describe deploy redis
kubectl -n kubeserve-lab get events --sort-by=.lastTimestamp | tail -n 30
kubectl -n kubeserve-lab logs deploy/gateway-api --tail=200
```
- 복구 후에도 실패하면 NetworkPolicy 및 DNS 해석을 점검한다.

## 8. 추가 실험 아이디어
- Redis를 반복 중단/복구해 MTTR(복구 시간)을 측정한다.
- HPA scale 상태에서 장애 시 에러율 변화를 비교한다.
