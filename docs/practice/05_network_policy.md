# 05 Network Policy

## 1. 실습 목적
- NetworkPolicy가 통신 허용/차단에 미치는 영향을 체감한다.
- 이 실습으로 배우는 개념: Zero-trust 네트워크, 최소 권한 통신, 정책 디버깅.

## 2. 시나리오 설명
- `gateway-api -> redis` egress를 임시 차단하는 정책을 추가한다.
- enqueue 실패와 readiness 변화를 관찰한 뒤 정책을 제거한다.

## 3. 사전 조건
- API 포트포워드

```bash
kubectl -n kubeserve-lab port-forward svc/api 18080:8000
```

## 4. 실행 명령어 (kubectl / bash 포함)
```bash
# 1) 차단 정책 적용
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-api-to-redis
  namespace: kubeserve-lab
spec:
  podSelector:
    matchLabels:
      app: gateway-api
  policyTypes:
    - Egress
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
EOF

# 2) 요청 확인
curl -i http://127.0.0.1:18080/ready
curl -i -X POST http://127.0.0.1:18080/jobs \
  -H 'content-type: application/json' \
  -d '{"case":"np_block"}'

# 3) 정책 제거
kubectl -n kubeserve-lab delete networkpolicy deny-api-to-redis
```

## 5. 관찰 포인트 (metrics, logs, 상태 변화)
- API 로그: Redis connect timeout/refused
- Prometheus
  - `rate(gateway_jobs_failed_total[1m])`
  - `rate(gateway_jobs_created_total[1m])`
- Grafana
  - Gateway 실패율 증가
- 정책 목록
  - `kubectl -n kubeserve-lab get networkpolicy`

## 6. 예상 결과
- 정책 적용 중에는 Redis 접근 실패로 `/ready`가 503이 되거나 `POST /jobs` 실패가 증가한다.
- 정책 삭제 후 정상 복구된다.

## 7. 문제 발생 시 체크 방법
```bash
kubectl -n kubeserve-lab describe networkpolicy gateway-api-policy
kubectl -n kubeserve-lab describe networkpolicy deny-api-to-redis
kubectl -n kubeserve-lab logs deploy/gateway-api --tail=200
```
- ingress-nginx/Prometheus 트래픽까지 차단되지 않았는지 확인한다.

## 8. 추가 실험 아이디어
- `worker -> postgres`만 차단해 처리 실패 패턴을 비교한다.
- DNS egress 정책을 제거했을 때 서비스명 해석 실패를 관찰한다.
