# LangGraph: single agent

A conversational [LangGraph](https://langchain-ai.github.io/langgraph/) agent
backed by OpenAI, served as a one-agent Kynomesh `AgentSet`.

| File                      | Role                                                                                  |
| ------------------------- | ------------------------------------------------------------------------------------- |
| `src/chat_agent/graph.py` | The LangGraph agent. No Kynomesh imports.                                             |
| `src/chat_agent/main.py`  | Wraps the graph in an A2A `AgentExecutor` and serves it with `kynomesh.server.start`. |
| `manifests/agentset.yaml` | The `AgentSet` (one agent, `Supervisor` pattern, `entry: chat-agent`).                |

The graph needs a `messages` key in its state: A2A text parts arrive as
`{"role": "user", "content": ...}` and the last message in the result becomes
the A2A reply. `main.py` does this mapping.

## Prerequisites

- Python 3.10+ and [uv](https://docs.astral.sh/uv/)
- An `OPENAI_API_KEY`. The agent refuses to start without one.
- [`a2acli`](https://github.com/kynoproj/a2acli) (optional, for the CLI calls
  below)
- For the cluster run: Docker, `kubectl`, a local Kubernetes cluster with
  [Kynomesh installed](https://github.com/kynoproj/kynomesh/blob/main/docs/quick-start.md)

## 1. Run locally

```shell
uv run pytest                                        # unit tests (OpenAI is mocked)
OPENAI_API_KEY=... uv run python -m chat_agent.main  # HTTP on :8088, gRPC on :8089
```

In another terminal:

```shell
curl localhost:8088/healthz
a2acli -u http://localhost:8088 send 'What is Kubernetes?' -o json
```

## 2. Run on Kynomesh

```shell
make build                     # builds langgraph-chat:latest
# kind:  kind load docker-image langgraph-chat:latest
# k3d:   k3d image import langgraph-chat:latest -c <cluster>
kubectl create secret generic openai-api-key --from-literal=OPENAI_API_KEY=...
make deploy
kubectl get agentset           # PHASE should become Running
kubectl port-forward svc/langgraph-chat-ingress 8490
a2acli -k -u https://localhost:8490 --override-host=localhost:8490 send 'What is Kubernetes?' -o json
make delete
```

Behind a TLS-intercepting proxy the image build fails certificate checks. Pass
the proxy CA: `make build CA_CERT=/path/to/ca.pem`.

> **Note:** the agent card sets `protocol_version` on each interface. Without it
> `a2acli` (a2a-go) fails with `no compatible transports found`.
