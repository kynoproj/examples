IMAGE   ?= crew-pipeline:latest
# Optional: path to a proxy CA (*.pem) for builds behind TLS interception.
CA_CERT ?=
ifneq ($(CA_CERT),)
CACERT_ARG := --build-context cacert=$(dir $(CA_CERT))
endif

.PHONY: test build deploy delete
test: ## Run unit tests.
	uv run pytest

build: ## Build the container image.
	docker buildx build --load -t $(IMAGE) $(CACERT_ARG) .

deploy: ## Apply the AgentSet.
	kubectl apply -f manifests/agentset.yaml

delete: ## Remove the AgentSet.
	kubectl delete -f manifests/agentset.yaml
