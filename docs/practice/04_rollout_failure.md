# 04 Rollout Failure

## 1. 실습 목적
- 잘못된 이미지 배포로 rollout 실패를 만들고 rollback 절차를 익힌다.
- 이 실습으로 배우는 개념: 배포 실패 탐지, rollout history, 즉시 롤백.

## 2. 시나리오 설명
- `gateway-api` 이미지 태그를 존재하지 않는 값으로 변경한다.
- `ImagePullBackOff`를 유도하고, rollback으로 복구한다.

## 3. 사전 조건
- 현재 정상 배포 상태

```bash
kubectl -n kubeserve-lab rollout status deploy/gateway-api
```

## 4. 실행 명령어 (kubectl / bash 포함)
```bash
# 1) 고의 실패 배포
kubectl -n kubeserve-lab set image deploy/gateway-api \
  gateway-api=kubeserve-lab/gateway-api:not-exists

# 2) 상태 관찰
kubectl -n kubeserve-lab rollout status deploy/gateway-api --timeout=60s || true
kubectl -n kubeserve-lab get pods -l app=gateway-api

# 3) 원인 확인
kubectl -n kubeserve-lab describe pod -l app=gateway-api

# 4) rollback
kubectl -n kubeserve-lab rollout undo deploy/gateway-api
kubectl -n kubeserve-lab rollout status deploy/gateway-api
```

## 5. 관찰 포인트 (metrics, logs, 상태 변화)
- 상태: `ImagePullBackOff`, `ErrImagePull`
- 이벤트: image pull 관련 오류 메시지
- Prometheus
  - `up{job="gateway-api"}` 하락
  - `rate(gateway_jobs_failed_total[1m])` 상승 가능
- Grafana
  - Gateway 트래픽/지연 공백 또는 에러 증가

## 6. 예상 결과
- 잘못된 이미지로 rollout 실패.
- rollback 후 정상 Replica가 복구되고 API 응답이 정상화된다.

## 7. 문제 발생 시 체크 방법
```bash
kubectl -n kubeserve-lab rollout history deploy/gateway-api
kubectl -n kubeserve-lab describe deploy gateway-api
kubectl -n kubeserve-lab get rs -l app=gateway-api
```
- 이전 리비전이 없으면 정상 이미지로 `set image`를 직접 재적용한다.

## 8. 추가 실험 아이디어
- `worker`에도 동일한 실습을 수행해 데이터 처리 지연을 비교한다.
- readiness probe 경로를 일부러 틀리게 바꿔 rollout 실패를 유도해본다.
