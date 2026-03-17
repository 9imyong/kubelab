# 10 KEDA Autoscaling (설계 중심)

## 1. 실습 목적
- CPU 기반 HPA를 이벤트 기반(KEDA)으로 확장하는 설계를 이해한다.
- 이 실습으로 배우는 개념: queue-length 기반 스케일링, ScaledObject, cooldown 전략.

## 2. 시나리오 설명
- 현재 worker는 CPU 기반 HPA로 스케일된다.
- 이를 Redis queue length(또는 Kafka lag) 기반 KEDA 스케일링으로 전환하는 설계를 검토한다.

## 3. 사전 조건
- 현재 HPA 동작 확인

```bash
kubectl -n kubeserve-lab get hpa worker
```

- KEDA 설치 필요 (설계 검증 단계에서는 manifest 검토 중심)

## 4. 실행 명령어 (kubectl / bash 포함)
```bash
# 1) ScaledObject 초안 적용 (KEDA 설치 환경에서만 유효)
cat <<'EOF' | kubectl apply -f -
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: worker-queue-scaledobject
  namespace: kubeserve-lab
spec:
  scaleTargetRef:
    name: worker
  minReplicaCount: 1
  maxReplicaCount: 10
  pollingInterval: 15
  cooldownPeriod: 60
  triggers:
    - type: redis
      metadata:
        address: redis.kubeserve-lab.svc.cluster.local:6379
        listName: jobs:queue
        listLength: "20"
EOF

# 2) 리소스 확인
kubectl -n kubeserve-lab get scaledobject
kubectl -n kubeserve-lab describe scaledobject worker-queue-scaledobject

# 3) 부하를 걸어 큐 길이 증가 유도
docker run --rm -i \
  -v "$PWD:/work" -w /work \
  grafana/k6 run tests/load/k6_jobs.js \
  -e BASE_URL=http://host.docker.internal:18080 \
  -e VUS=80 -e DURATION=2m
```

## 5. 관찰 포인트 (metrics, logs, 상태 변화)
- `kubectl -n kubeserve-lab get hpa`에서 KEDA가 생성한 HPA 변화
- queue depth: `LLEN jobs:queue`
- Prometheus
  - `rate(worker_jobs_processed_total[1m])`
  - `rate(worker_jobs_failed_total[1m])`
  - (도입 시) KEDA metrics adapter 지표
- Grafana
  - queue depth 대비 worker replica 상관관계

## 6. 예상 결과
- 큐 길이 임계치 초과 시 worker replica가 빠르게 증가한다.
- 큐가 비면 cooldown 이후 점진적으로 축소된다.

## 7. 문제 발생 시 체크 방법
```bash
kubectl get crd | grep keda
kubectl -n keda logs deploy/keda-operator --tail=200
kubectl -n kubeserve-lab describe scaledobject worker-queue-scaledobject
```
- KEDA 미설치면 `no matches for kind "ScaledObject"`가 발생한다.

## 8. 추가 실험 아이디어
- Redis trigger 대신 Kafka lag trigger 설계를 비교한다.
- `listLength`, `cooldownPeriod` 값을 조정해 scale thrashing을 줄여본다.
