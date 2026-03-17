# 07 HPA Test

## 1. 실습 목적
- 부하 기반 scale-out/scale-in을 실제로 확인한다.
- 이 실습으로 배우는 개념: HPA 동작 조건, 관찰 지표, 확장 지연 시간.

## 2. 시나리오 설명
- 부하를 발생시켜 `gateway-api`/`worker` HPA가 확장되는지 관찰한다.

## 3. 사전 조건
- Metrics Server가 클러스터에 설치되어 있어야 한다.

```bash
kubectl top nodes
```

- HPA 확인

```bash
kubectl -n kubeserve-lab get hpa
```

## 4. 실행 명령어 (kubectl / bash 포함)
```bash
# 1) HPA 실시간 관찰
kubectl -n kubeserve-lab get hpa -w

# 2) Pod 개수 관찰
kubectl -n kubeserve-lab get pods -l app=gateway-api -w

# 3) 부하 발생 (별도 터미널)
docker run --rm -i \
  -v "$PWD:/work" -w /work \
  grafana/k6 run tests/load/k6_jobs.js \
  -e BASE_URL=http://host.docker.internal:18080 \
  -e VUS=80 -e DURATION=3m
```

## 5. 관찰 포인트 (metrics, logs, 상태 변화)
- `kubectl -n kubeserve-lab get hpa`
  - `TARGETS` CPU%가 목표(70%)를 넘는지
  - `REPLICAS` 증가 여부
- Prometheus
  - `rate(gateway_jobs_created_total[1m])`
  - `rate(worker_jobs_processed_total[1m])`
  - `rate(container_cpu_usage_seconds_total{namespace="kubeserve-lab"}[1m])`
- Grafana
  - 요청량 증가 후 처리량이 따라오는지

## 6. 예상 결과
- 고부하 구간에서 `gateway-api` 또는 `worker` replica가 증가한다.
- 부하 종료 후 일정 시간 뒤 scale-in 된다.

## 7. 문제 발생 시 체크 방법
```bash
kubectl -n kubeserve-lab describe hpa gateway-api
kubectl -n kubeserve-lab describe hpa worker
kubectl get apiservices | grep metrics
```
- scale이 안 되면 Metrics Server/리소스 요청값 설정을 우선 확인한다.

## 8. 추가 실험 아이디어
- `averageUtilization` 값을 70→50으로 낮춰 민감도를 비교한다.
- `minReplicas`, `maxReplicas`를 바꿔 비용/성능 트레이드오프를 체험한다.
