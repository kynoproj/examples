# Kynomesh examples

Examples of running agents built with popular frameworks on
[Kynomesh](https://github.com/kynoproj/kynomesh), a Kubernetes-native agent mesh
based on the [A2A protocol](https://a2a-protocol.org/). Each example is
self-contained: copy its folder and it runs.

| Framework | Example                                  | Shows                                                                                                                                      |
| --------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| LangGraph | [single-agent](langgraph/single-agent)   | A conversational LangGraph agent (OpenAI) served as a one-agent `AgentSet`                                                                 |
| LangGraph | [supervisor](langgraph/supervisor)       | A supervisor delegating to two worker agents (researcher, calculator) over A2A, using the `Supervisor` pattern                             |
| LangGraph | [dynamic-peers](langgraph/dynamic-peers) | A supervisor that discovers its workers from Kynomesh at startup, so adding or removing a worker needs no code change (with `driftReload`) |

Planned: Claude Agent SDK, Google ADK, CrewAI, and multi-agent `AgentSet`
patterns (Supervisor, Handoff, Sequential).

All Python examples use the
[Kynomesh Python SDK](https://github.com/kynoproj/kynomesh-py).

## License

Apache 2.0, see [LICENSE](LICENSE).
