# Optional: path to a proxy CA (*.pem) for builds behind TLS interception.
CA_CERT ?=
CA_ARG  := $(if $(CA_CERT),CA_CERT=$(abspath $(CA_CERT)),)

.PHONY: build deploy delete
build: ## Build both images this example uses (from the sibling examples).
	$(MAKE) -C ../langgraph/dynamic-peers build $(CA_ARG)
	$(MAKE) -C ../claude-agent-sdk/dynamic-peers build $(CA_ARG)

deploy: ## Apply the AgentSet.
	kubectl apply -f manifests/agentset.yaml

delete: ## Remove the AgentSet.
	kubectl delete -f manifests/agentset.yaml
