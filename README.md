# Kynomesh examples

Examples of running agents built with popular frameworks on
[Kynomesh](https://github.com/kynoproj/kynomesh), a Kubernetes-native agent mesh
based on the [A2A protocol](https://a2a-protocol.org/). Each example is
self-contained: copy its folder and it runs.

| Framework                    | Example                                         | Shows                                                                                                                                                    |
| ---------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LangGraph                    | [single-agent](langgraph/single-agent)          | A conversational LangGraph agent (OpenAI) served as a one-agent `AgentSet`                                                                               |
| LangGraph                    | [supervisor](langgraph/supervisor)              | A supervisor delegating to two worker agents (researcher, calculator) over A2A, using the `Supervisor` pattern                                           |
| LangGraph                    | [dynamic-peers](langgraph/dynamic-peers)        | A supervisor that discovers its workers from Kynomesh at startup, so adding or removing a worker needs no code change (with `driftReload`)               |
| Claude Agent SDK             | [single-agent](claude-agent-sdk/single-agent)   | A Claude Agent SDK agent with a custom in-process tool, served as a one-agent `AgentSet`                                                                 |
| Claude Agent SDK             | [dynamic-peers](claude-agent-sdk/dynamic-peers) | A Claude supervisor that discovers its Claude workers from Kynomesh at startup, so adding or removing a worker needs no code change (with `driftReload`) |
| Google ADK                   | [single-agent](google-adk/single-agent)         | A Google ADK agent (Gemini) with a function tool, served as a one-agent `AgentSet`                                                                       |
| LangGraph + Claude Agent SDK | [mixed-fleet](mixed-fleet)                      | One `AgentSet` mixing frameworks: a Claude supervisor discovering LangGraph and Claude workers, with no new agent code                                   |
| LangGraph + Claude Agent SDK | [external-agent](external-agent) | A supervisor calling a worker that lives in another `AgentSet`, referenced with `externalAgents` |

Planned: CrewAI, and more multi-agent `AgentSet` patterns (Handoff,
Sequential).

All Python examples use the
[Kynomesh Python SDK](https://github.com/kynoproj/kynomesh-py).

## License

Apache 2.0, see [LICENSE](LICENSE).
