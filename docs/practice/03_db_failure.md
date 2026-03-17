# 03 Postgres Failure

## 1. 실습 목적
- DB 장애 시 API 조회/저장 및 Worker 결과 업데이트 실패를 관찰한다.
- 이 실습으로 배우는 개념: 상태 저장소 장애 영향, 데이터 경로 분리, 복구 절차.

## 2. 시나리오 설명
- Postgres StatefulSet을 중단한다.
- `/ready`, `POST /jobs`, `GET /jobs/{id}`, worker 업데이트 실패를 확인한다.

## 3. 사전 조건
- API 포트포워드

```bash
kubectl -n kubeserve-lab port-forward svc/api 18080:8000
```

## 4. 실행 명령어 (kubectl / bash 포함)
```bash
# 1) Postgres 중단
kubectl -n kubeserve-lab scale statefulset/postgres --replicas=0
kubectl -n kubeserve-lab get pods -l app=postgres -w

# 2) readiness 확인
curl -i http://127.0.0.1:18080/ready

# 3) enqueue 시도
curl -i -X POST http://127.0.0.1:18080/jobs \
  -H 'content-type: application/json' \
  -d '{"case":"db_down"}'

# 4) 복구
kubectl -n kubeserve-lab scale statefulset/postgres --replicas=1
kubectl -n kubeserve-lab rollout status statefulset/postgres
```

## 5. 관찰 포인트 (metrics, logs, 상태 변화)
- API 로그: DB connect/query 예외
- Worker 로그: `UPDATE jobs` 실패 로그
- Prometheus
  - `rate(gateway_jobs_failed_total[1m])`
  - `rate(worker_jobs_failed_total[1m])`
  - `up{job="gateway-api"}`, `up{job="worker"}`
- Grafana
  - Worker failed/sec 증가

## 6. 예상 결과
- Postgres 중단 시 `/ready`는 503.
- `POST /jobs` 성공률이 낮아지거나 실패한다.
- DB 복구 후 신규 요청부터 정상 처리된다.

## 7. 문제 발생 시 체크 방법
```bash
kubectl -n kubeserve-lab describe statefulset postgres
kubectl -n kubeserve-lab logs statefulset/postgres --tail=200
kubectl -n kubeserve-lab get pvc
```
- PVC Pending이면 스토리지 클래스/노드 상태를 확인한다.

## 8. 추가 실험 아이디어
- DB 복구 시간을 변경해 API 장애시간과 상관관계를 측정한다.
- DB restart(삭제 대신)와 scale 0/1의 차이를 비교한다.
