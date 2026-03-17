# Troubleshooting

## 증상 1) `ImagePullBackOff`

원인:
- kind 노드에 `localdev` 이미지 미로딩

조치:
1. `make build`
2. `make load-kind`
3. `kubectl -n kubeserve-lab delete pod -l app=gateway-api`
4. `kubectl -n kubeserve-lab delete pod -l app=worker`

## 증상 2) `/ready` 가 503

원인:
- Redis/Postgres 연결 실패

조치:
1. `kubectl -n kubeserve-lab get pods`
2. `kubectl -n kubeserve-lab logs deploy/gateway-api`
3. `kubectl -n kubeserve-lab logs deploy/redis`
4. `kubectl -n kubeserve-lab logs statefulset/postgres`

## 증상 3) 작업이 완료되지 않음

원인:
- Worker 미기동 또는 Redis 큐 적체

조치:
1. `kubectl -n kubeserve-lab get pods -l app=worker`
2. `kubectl -n kubeserve-lab logs deploy/worker`
3. 필요 시 스케일 아웃: `kubectl -n kubeserve-lab scale deploy/worker --replicas=3`

## 증상 4) Prometheus 타겟 DOWN

원인:
- Service/Port 불일치, NetworkPolicy 차단

조치:
1. `kubectl -n kubeserve-lab get svc`
2. `kubectl -n kubeserve-lab port-forward svc/prometheus 9090:9090`
3. `http://127.0.0.1:9090/targets` 확인
4. `kubectl -n kubeserve-lab describe networkpolicy`

## 증상 5) Grafana 로그인 실패

원인:
- 비밀번호 변경/시크릿 미적용

조치:
1. `kubectl -n kubeserve-lab get secret grafana-admin -o yaml`
2. Deployment 재시작: `kubectl -n kubeserve-lab rollout restart deploy/grafana`
3. 기본값 확인: `admin / admin`
