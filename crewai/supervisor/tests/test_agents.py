import asyncio
from unittest.mock import MagicMock

import pytest
from fakes import final, native, native_tool_call, scripted, use_tool

from crew_assistant.agents import (
    DEFAULT_MODEL,
    AgentError,
    build_calculator,
    build_researcher,
    build_supervisor,
    run_agent,
)


def tool_names(agent):
    return [t.name for t in agent.tools]


def test_each_role_has_only_its_own_tools():
    assert tool_names(build_researcher(scripted())) == ["lookup_fact"]
    assert tool_names(build_calculator(scripted())) == ["add", "multiply", "divide"]
    assert tool_names(build_supervisor(MagicMock(), scripted())) == ["ask_researcher", "ask_calculator"]


def test_model_comes_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-custom")
    assert build_researcher().llm.model == "gpt-custom"


def test_model_defaults(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    assert build_researcher().llm.model == DEFAULT_MODEL


async def test_supervisor_delegates_to_both_workers_in_order():
    replies = {"researcher": "France: ~68 million people.", "calculator": "204"}
    asked = []

    def ask_peer(name, text):
        asked.append((name, text))
        return replies[name]

    llm = scripted(
        use_tool("ask_researcher", question="population of France"),
        use_tool("ask_calculator", problem="68 * 3"),
        final("France's population times 3 is about 204 million."),
    )

    reply = await run_agent("population of France times 3?", agent=build_supervisor(ask_peer, llm))

    assert asked == [("researcher", "population of France"), ("calculator", "68 * 3")]
    assert reply.endswith("204 million.")


async def test_supervisor_routes_single_worker():
    asked = []
    llm = scripted(use_tool("ask_researcher", question="capital of France"), final("Paris."))

    await run_agent("capital?", agent=build_supervisor(lambda n, t: asked.append((n, t)) or "Paris", llm))

    assert asked == [("researcher", "capital of France")]


async def test_failed_worker_is_reported_to_the_model_not_raised():
    def ask_peer(name, text):
        raise RuntimeError("down")

    llm = scripted(use_tool("ask_calculator", problem="1+1"), final("The calculator is unavailable."))

    reply = await run_agent("1+1?", agent=build_supervisor(ask_peer, llm))

    assert reply == "The calculator is unavailable."
    observation = "\n".join(m["content"] for m in llm.seen[1])
    assert "Error: worker 'calculator' failed: down" in observation


async def test_researcher_uses_lookup_tool():
    llm = scripted(use_tool("lookup_fact", topic="Japan"), final("Tokyo."))

    assert await run_agent("Japan?", agent=build_researcher(llm)) == "Tokyo."
    assert "124 million" in str(llm.seen[1])


async def test_calculator_uses_arithmetic_tool():
    llm = scripted(use_tool("multiply", a=68, b=3), final("204"))

    assert await run_agent("68*3", agent=build_calculator(llm)) == "204"
    assert "Observation: 204.0" in str(llm.seen[1])


@pytest.mark.parametrize("function_calling", [False, True], ids=["react", "native-function-calling"])
async def test_peer_call_runs_on_the_servers_event_loop(function_calling):
    """CrewAI runs tools on a worker thread; the A2A call must hop back to our loop."""
    from crew_assistant.peers import blocking_ask

    server_loop = asyncio.get_running_loop()
    seen = {}

    async def ask_peer(name, text):
        seen["loop"] = asyncio.get_running_loop()
        return "Paris"

    if function_calling:
        llm = native(native_tool_call("ask_researcher", question="capital?"), "Paris.")
    else:
        llm = scripted(use_tool("ask_researcher", question="capital?"), final("Paris."))
    agent = build_supervisor(blocking_ask(ask_peer, server_loop), llm)

    assert await run_agent("capital?", agent=agent) == "Paris."
    assert seen["loop"] is server_loop


async def test_empty_answer_raises():
    with pytest.raises(AgentError, match="without a final answer"):
        await run_agent("hi", agent=build_researcher(scripted(final(""))))
