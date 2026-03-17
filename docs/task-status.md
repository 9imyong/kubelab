# 작업 태스크 현황 (설계 반영 점검)

기준일: 2026-03-17  
상태 기준: `완료`, `부분완료`, `미착수`

## 1) apps/gateway-api

- [x] 완료 - FastAPI 사용
  - 근거: `apps/gateway-api/main.py`
- [x] 완료 - 엔드포인트 `GET /live`
  - 근거: `apps/gateway-api/main.py`
- [x] 완료 - 엔드포인트 `GET /ready`
  - 근거: `apps/gateway-api/main.py`
- [x] 완료 - 엔드포인트 `POST /jobs`
  - 근거: `apps/gateway-api/main.py`
- [x] 완료 - 엔드포인트 `GET /jobs/{job_id}`
  - 근거: `apps/gateway-api/main.py`
- [x] 완료 - 엔드포인트 `GET /metrics`
  - 근거: `apps/gateway-api/main.py`
- [x] 완료 - `POST /jobs`에서 Redis 큐 enqueue + `job_id` 반환
  - 근거: `apps/gateway-api/main.py`
- [x] 완료 - readiness가 Redis/Postgres 연결 상태 반영
  - 근거: `apps/gateway-api/main.py`
- [x] 완료 - `prometheus_client` 기반 메트릭 노출
  - 근거: `apps/gateway-api/main.py`

## 2) apps/worker

- [x] 완료 - Redis 큐 작업 소비
  - 근거: `apps/worker/worker.py`
- [x] 완료 - 처리 시 1~3초 sleep 시뮬레이션
  - 근거: `apps/worker/worker.py`
- [x] 완료 - 처리 결과 Postgres 저장
  - 근거: `apps/worker/worker.py`
- [x] 완료 - 처리 건수/실패 건수/처리 시간 메트릭 노출
  - 근거: `apps/worker/worker.py`

## 3) deploy/base

- [x] 완료 - Namespace
  - 근거: `deploy/base/namespace.yaml`
- [x] 완료 - ConfigMap
  - 근거: `deploy/base/configmap.yaml`
- [x] 완료 - Secret
  - 근거: `deploy/base/secret.yaml`
- [x] 완료 - Deployment (`gateway-api`, `worker`, `redis`)
  - 근거: `deploy/base/deployment-gateway-api.yaml`, `deploy/base/deployment-worker.yaml`, `deploy/base/deployment-redis.yaml`
- [x] 완료 - StatefulSet (`postgres`)
  - 근거: `deploy/base/statefulset-postgres.yaml`
- [x] 완료 - Service (`api`, `redis`, `postgres`)
  - 근거: `deploy/base/service-api.yaml`, `deploy/base/service-redis.yaml`, `deploy/base/service-postgres.yaml`
- [x] 완료 - Ingress (`/api -> gateway-api`)
  - 근거: `deploy/base/ingress-api.yaml`
- [x] 완료 - HPA (`gateway-api`, `worker`)
  - 근거: `deploy/base/hpa-gateway-api.yaml`, `deploy/base/hpa-worker.yaml`
- [x] 완료 - NetworkPolicy (필요 통신만 허용)
  - 근거: `deploy/base/networkpolicy-*.yaml`
- [x] 완료 - resources requests/limits
  - 근거: 각 Deployment/StatefulSet YAML
- [x] 완료 - liveness/readiness/startup probe
  - 근거: 각 Deployment/StatefulSet YAML

## 4) observability

- [x] 완료 - Prometheus 배포 + scrape 설정
  - 근거: `observability/prometheus-deployment.yaml`, `observability/prometheus-configmap.yaml`
- [x] 완료 - Grafana 배포
  - 근거: `observability/grafana-deployment.yaml`
- [x] 완료 - 기본 대시보드 JSON/설정 포함
  - 근거: `observability/grafana-dashboard-configmap.yaml`, `observability/grafana-dashboard-provider-configmap.yaml`

## 5) developer experience

- [x] 완료 - Makefile 제공 (`build`, `load-kind`, `deploy`, `test`, `load-test`, `cleanup`)
  - 근거: `Makefile`
- [x] 완료 - README (아키텍처/실행/확인 명령/장애 실습/rollout&rollback)
  - 근거: `README.md`
- [x] 완료 - `docs/runbook.md`
  - 근거: `docs/runbook.md`
- [x] 완료 - `docs/troubleshooting.md`
  - 근거: `docs/troubleshooting.md`
- [x] 완료 - 샘플 부하 테스트 스크립트
  - 근거: `tests/load/k6_jobs.js`

## 6) 로컬(kind) 기준

- [x] 완료 - kind 기준 실행 흐름 문서화
  - 근거: `README.md`, `Makefile`
- [x] 완료 - ingress-nginx 설치 방법 포함
  - 근거: `README.md`
- [x] 완료 - 이미지 태그 `localdev` 사용
  - 근거: `Makefile`, `deploy/base/deployment-*.yaml`
- [x] 완료 - `kind load docker-image` 예시 포함
  - 근거: `README.md`, `Makefile`

## 7) 코드 스타일/운영 관점

- [x] 완료 - Python 3.12 베이스 이미지 사용
  - 근거: `apps/gateway-api/Dockerfile`, `apps/worker/Dockerfile`
- [x] 완료 - 환경변수 기반 설정
  - 근거: `apps/gateway-api/main.py`, `apps/worker/worker.py`
- [x] 완료 - 예외 처리 + 로그 포함
  - 근거: `apps/gateway-api/main.py`, `apps/worker/worker.py`
- [x] 완료 - health check가 실제 의존성 상태 반영
  - 근거: `apps/gateway-api/main.py` (`/ready`)

## 추가 요구사항

- [x] 완료 - Helm 없이 순수 YAML/Kustomize
  - 근거: `deploy/base/kustomization.yaml`, `observability/kustomization.yaml`
- [x] 완료 - 이후 Helm 확장 가능한 깔끔한 구조 유지
  - 근거: 앱/배포/관측성 분리 디렉토리 구조
- [x] 완료 - 각 YAML 파일에 필요 이유 주석 추가
  - 근거: `deploy/base/*.yaml`, `observability/*.yaml` 상단 주석
- [x] 완료 - 초보자 학습 가능한 문서화
  - 근거: `README.md`, `docs/runbook.md`, `docs/troubleshooting.md`

## 검증 메모

- `kubectl kustomize deploy/base` 렌더링 성공
- `kubectl kustomize observability` 렌더링 성공
- Python 문법(AST) 검증 성공 (`apps/gateway-api/main.py`, `apps/worker/worker.py`)
