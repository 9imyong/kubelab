KIND_CLUSTER ?= local-dev
NAMESPACE ?= kubeserve-lab
API_IMAGE ?= kubeserve-lab/gateway-api:localdev
WORKER_IMAGE ?= kubeserve-lab/worker:localdev

.PHONY: build load-kind deploy test load-test cleanup

build:
	docker build -t $(API_IMAGE) apps/gateway-api
	docker build -t $(WORKER_IMAGE) apps/worker

load-kind:
	kind load docker-image $(API_IMAGE) --name $(KIND_CLUSTER)
	kind load docker-image $(WORKER_IMAGE) --name $(KIND_CLUSTER)

deploy:
	kubectl apply -k deploy/base
	kubectl apply -k observability

test:
	bash tests/smoke_test.sh

load-test:
	docker run --rm -i \
	  -v "$$(pwd):/work" -w /work \
	  grafana/k6 run tests/load/k6_jobs.js -e BASE_URL=http://host.docker.internal:18080

cleanup:
	kubectl delete -k observability --ignore-not-found
	kubectl delete -k deploy/base --ignore-not-found
