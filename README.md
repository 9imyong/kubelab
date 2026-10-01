# kubelab

kind 기반 Kubernetes 실습 프로젝트입니다.  

리소스 이름과 네임스페이스는 `kubeserve-lab`을 씁니다.
FastAPI API + Worker + Redis + Postgres + Prometheus + Grafana 구성을 통해 운영/장애/스케일링을 연습할 수 있습니다.

## 구성 요소
- `gateway-api` (FastAPI): `/live`, `/ready`, `/jobs`, `/metrics`
- `worker`: Redis 큐 소비, 1~3초 처리 시뮬레이션, Postgres 결과 저장
- `redis`: 작업 큐
- `postgres`: 작업 상태/결과 저장소
- `prometheus`, `grafana`: 메트릭 수집/시각화

## 디렉토리
- `apps/gateway-api`: API 코드
- `apps/worker`: Worker 코드
- `deploy/base`: 순수 YAML/Kustomize 배포
- `observability`: Prometheus/Grafana 리소스
- `tests/load`: k6 부하 스크립트
- `docs`: Runbook, Troubleshooting, Practice 시나리오

## 빠른 시작
### 1) 준비물
- Docker
- kind
- kubectl

### 2) kind 클러스터 생성
```bash
kind create cluster --name kind
```

### 3) ingress-nginx 설치
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s
```

### 4) 이미지 빌드/로드/배포
```bash
make build
make load-kind
make deploy
```

`kind load docker-image` 직접 예시:
```bash
kind load docker-image kubeserve-lab/gateway-api:localdev --name kind
kind load docker-image kubeserve-lab/worker:localdev --name kind
```

### 5) 상태 확인
```bash
kubectl -n kubeserve-lab get pods
kubectl -n kubeserve-lab get svc
kubectl -n kubeserve-lab get ingress
kubectl -n kubeserve-lab get hpa
```

## 사용 방법
### API 확인 (포트포워드)
```bash
kubectl -n kubeserve-lab port-forward svc/api 18080:8000
curl -s http://127.0.0.1:18080/live
curl -s -X POST http://127.0.0.1:18080/jobs \
  -H 'content-type: application/json' \
  -d '{"hello":"world"}'
```

### Ingress 경유 확인
```bash
kubectl -n ingress-nginx port-forward svc/ingress-nginx-controller 8080:80
curl -s http://127.0.0.1:8080/api/live
```

### 관측성 확인
```bash
kubectl -n kubeserve-lab port-forward svc/prometheus 9090:9090
kubectl -n kubeserve-lab port-forward svc/grafana 3000:3000
```
- Grafana URL: `http://127.0.0.1:3000`
- 계정: `admin / admin`
- 기본 대시보드: `Kubeserve Lab Overview`

## 테스트
```bash
make test
make load-test
```

## 롤아웃/롤백
```bash
kubectl -n kubeserve-lab set image deploy/gateway-api gateway-api=kubeserve-lab/gateway-api:localdev
kubectl -n kubeserve-lab rollout status deploy/gateway-api
kubectl -n kubeserve-lab rollout history deploy/gateway-api
kubectl -n kubeserve-lab rollout undo deploy/gateway-api
```

## 실습 문서
- 운영 절차: `docs/runbook.md`
- 장애 대응: `docs/troubleshooting.md`
- 실습 시나리오: `docs/practice/*.md`

## 정리
```bash
make cleanup
kind delete cluster --name kind
```
