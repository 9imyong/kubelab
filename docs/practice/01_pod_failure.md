# 01 Pod Failure

## 1. 실습 목적
- Pod 강제 삭제 시 Deployment가 자동 복구하는 과정을 확인한다.
- 이 실습으로 배우는 개념: Self-healing, readiness/liveness, 장애 감지 시간.

## 2. 시나리오 설명
- `gateway-api` Pod 하나를 강제로 삭제한다.
- 서비스는 일시 흔들릴 수 있지만, ReplicaSet이 새 Pod를 생성해 정상 상태로 복구되어야 한다.

## 3. 사전 조건
- 클러스터/앱 배포 완료
- 터미널 1개 이상 준비
- 선택: API 포트포워드

```bash
kubectl -n kubeserve-lab port-forward svc/api 18080:8000
```

## 4. 실행 명령어 (kubectl / bash 포함)
```bash
# 1) 현재 상태 확인
kubectl -n kubeserve-lab get pods -l app=gateway-api -w

# 2) 별도 터미널에서 대상 Pod 1개 선택 후 강제 삭제
POD=$(kubectl -n kubeserve-lab get pod -l app=gateway-api -o jsonpath='{.items[0].metadata.name}')
kubectl -n kubeserve-lab delete pod "$POD" --grace-period=0 --force

# 3) API 연속 호출로 가용성 확인 (간단)
for i in {1..20}; do
  curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:18080/live
  sleep 1
done
```

## 5. 관찰 포인트 (metrics, logs, 상태 변화)
- `kubectl -n kubeserve-lab get pods -l app=gateway-api`
- `kubectl -n kubeserve-lab describe pod <new-pod>`
- Prometheus
  - `up{job="gateway-api"}`
  - `rate(gateway_jobs_failed_total[1m])`
  - `histogram_quantile(0.95, sum(rate(gateway_job_submit_latency_seconds_bucket[5m])) by (le))`
- Grafana
  - `Kubeserve Lab Overview`에서 Gateway latency/throughput 변동

## 6. 예상 결과
- 삭제된 Pod는 `Terminating` 후 사라지고 새 Pod가 생성된다.
- 잠깐의 지연 가능성은 있으나, 정상 복구 후 `/live`, `/ready`는 다시 200을 반환한다.

## 7. 문제 발생 시 체크 방법
```bash
kubectl -n kubeserve-lab get deploy gateway-api
kubectl -n kubeserve-lab rollout status deploy/gateway-api
kubectl -n kubeserve-lab describe deploy gateway-api
kubectl -n kubeserve-lab logs deploy/gateway-api --tail=100
```
- Pod가 안 뜨면 이미지 로딩(`make load-kind`) 여부와 리소스 부족 여부를 확인한다.

## 8. 추가 실험 아이디어
- `worker` Pod도 동일하게 삭제해 처리 지연 변화를 비교한다.
- Replica를 1로 줄인 뒤 같은 실습을 해 가용성 차이를 비교한다.
