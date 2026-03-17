# Runbook

## 1) 운영 점검 체크리스트

- 파드 상태
  - `kubectl -n kubeserve-lab get pods`
- 엔드포인트 상태
  - `curl -sf http://127.0.0.1:18080/live`
  - `curl -sf http://127.0.0.1:18080/ready`
- HPA 상태
  - `kubectl -n kubeserve-lab get hpa`
- 이벤트 확인
  - `kubectl -n kubeserve-lab get events --sort-by=.lastTimestamp`

## 2) 배포 절차

1. `make build`
2. `make load-kind`
3. `make deploy`
4. `kubectl -n kubeserve-lab rollout status deploy/gateway-api`
5. `kubectl -n kubeserve-lab rollout status deploy/worker`

## 3) 검증 절차

- 기본 기능 검증: `make test`
- 메트릭 검증
  - Prometheus `up{job="gateway-api"}`
  - Prometheus `up{job="worker"}`

## 4) 장애 대응 (요약)

- API `/ready` 가 503이면 의존성 확인
  - Redis: `kubectl -n kubeserve-lab logs deploy/redis`
  - Postgres: `kubectl -n kubeserve-lab logs statefulset/postgres`
- 작업 처리 지연
  - Worker replica 증가: `kubectl -n kubeserve-lab scale deploy/worker --replicas=3`
- 네트워크 통신 이슈
  - `kubectl -n kubeserve-lab describe networkpolicy`

## 5) 롤백

1. `kubectl -n kubeserve-lab rollout history deploy/gateway-api`
2. `kubectl -n kubeserve-lab rollout undo deploy/gateway-api`
3. `kubectl -n kubeserve-lab rollout status deploy/gateway-api`

## 6) 운영 커맨드 모음

- API 로그: `kubectl -n kubeserve-lab logs deploy/gateway-api -f`
- Worker 로그: `kubectl -n kubeserve-lab logs deploy/worker -f`
- DB 접속 테스트:
  - `kubectl -n kubeserve-lab exec -it statefulset/postgres -- psql -U app -d kubeserve -c 'select now();'`
