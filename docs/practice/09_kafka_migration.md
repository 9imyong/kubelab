# 09 Kafka Migration (설계 중심)

## 1. 실습 목적
- Redis 큐를 Kafka로 전환할 때 필요한 운영 설계 포인트를 정리한다.
- 이 실습으로 배우는 개념: 메시징 보장(At-least-once), 파티션 전략, 소비자 그룹 운영.

## 2. 시나리오 설명
- 현재 `POST /jobs -> Redis list -> worker` 흐름을
  `POST /jobs -> Kafka topic -> consumer group(worker)`로 바꾸는 설계를 검증한다.
- 본 문서는 설계 검증 중심이며, 최소한의 `kubectl` 기반 구조 확인 절차를 포함한다.

## 3. 사전 조건
- 현재 아키텍처 정상 동작
- Kafka 운영 컴포넌트(예: Strimzi) 도입 여부 결정 필요

## 4. 실행 명령어 (kubectl / bash 포함)
```bash
# 1) 현재 큐 경로 확인(기준선)
kubectl -n kubeserve-lab get deploy gateway-api worker redis postgres

# 2) ConfigMap에 메시징 백엔드 전환 변수 초안 추가(설계 실험)
cat <<'EOF' | kubectl -n kubeserve-lab apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: kubeserve-lab
data:
  APP_ENV: localdev
  LOG_LEVEL: INFO
  MESSAGE_BACKEND: kafka
  KAFKA_BOOTSTRAP_SERVERS: kafka-bootstrap.kafka:9092
  KAFKA_TOPIC_JOBS: jobs.v1
  KAFKA_CONSUMER_GROUP: worker.v1
  REDIS_URL: redis://redis:6379/0
  REDIS_QUEUE_KEY: jobs:queue
  POSTGRES_HOST: postgres
  POSTGRES_PORT: "5432"
  POSTGRES_DB: kubeserve
  POSTGRES_USER: app
EOF

# 3) 반영 상태 확인
kubectl -n kubeserve-lab get configmap app-config -o yaml
```

## 5. 관찰 포인트 (metrics, logs, 상태 변화)
- 전환 시 필수 지표(목표)
  - Produce latency
  - Consumer lag (queue depth 대체 지표)
  - 처리 성공/실패율
  - 중복 처리율(재시도 영향)
- Prometheus/Grafana 권장 패널
  - lag per partition
  - consumer rebalance 횟수
  - end-to-end latency (enqueue 시각 ~ 완료 시각)

## 6. 예상 결과
- 단기적으로는 Redis와 Kafka 이중 쓰기(dual-write) 또는 브릿지 모드가 필요하다.
- 전환 완료 기준은 "lag 안정화 + 실패율 허용 범위 + 데이터 유실 없음"이다.

## 7. 문제 발생 시 체크 방법
```bash
kubectl -n kubeserve-lab logs deploy/gateway-api --tail=200
kubectl -n kubeserve-lab logs deploy/worker --tail=200
kubectl -n kubeserve-lab get events --sort-by=.lastTimestamp | tail -n 50
```
- 체크리스트
  - 파티션 키 설계가 균등한가
  - 재처리 시 idempotency 키가 있는가
  - DLQ(dead-letter queue) 정책이 있는가

## 8. 추가 실험 아이디어
- Topic 파티션 수를 바꿔 처리량/재균형 비용을 비교한다.
- worker를 소비자 그룹 1개/2개로 나눠 lag 회복 속도를 비교한다.
