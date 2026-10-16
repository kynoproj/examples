from unittest.mock import AsyncMock

import pytest
from fakes import call, scripted, text
from google.adk.models import LlmResponse
from google.genai import types

from adk_assistant.agents import (
    DEFAULT_MODEL,
    AgentError,
    build_calculator,
    build_researcher,
    build_supervisor,
    run_agent,
)


def tool_names(runner):
    return [t.__name__ for t in runner.agent.tools]


def test_each_role_has_only_its_own_tools():
    assert tool_names(build_researcher()) == ["lookup_fact"]
    assert tool_names(build_calculator()) == ["add", "multiply", "divide"]
    assert tool_names(build_supervisor(AsyncMock())) == ["ask_researcher", "ask_calculator"]


def test_model_comes_from_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_MODEL", "gemini-custom")
    assert build_researcher().agent.model == "gemini-custom"


def test_model_defaults(monkeypatch):
    monkeypatch.delenv("GOOGLE_MODEL", raising=False)
    assert build_researcher().agent.model == DEFAULT_MODEL


async def test_supervisor_delegates_to_both_workers_in_order():
    ask_peer = AsyncMock(side_effect=["France: ~68 million people.", "204"])
    runner, _ = scripted(
        build_supervisor(ask_peer),
        call("ask_researcher", question="population of France"),
        call("ask_calculator", problem="68 * 3"),
        text("France's population times 3 is about 204 million."),
    )

    reply = await run_agent("population of France times 3?", runner=runner)

    assert [c.args for c in ask_peer.await_args_list] == [
        ("researcher", "population of France"),
        ("calculator", "68 * 3"),
    ]
    assert reply.endswith("204 million.")


async def test_supervisor_routes_single_worker():
    ask_peer = AsyncMock(return_value="Paris")
    runner, _ = scripted(
        build_supervisor(ask_peer),
        call("ask_researcher", question="capital of France"),
        text("Paris."),
    )

    await run_agent("capital of France?", runner=runner)

    ask_peer.assert_awaited_once_with("researcher", "capital of France")


async def test_failed_worker_is_reported_to_the_model_not_raised():
    ask_peer = AsyncMock(side_effect=RuntimeError("down"))
    runner, llm = scripted(
        build_supervisor(ask_peer),
        call("ask_calculator", problem="1+1"),
        text("The calculator is unavailable."),
    )

    assert await run_agent("1+1?", runner=runner) == "The calculator is unavailable."
    sent = llm.requests[1].contents[-1].parts[0].function_response.response
    assert sent["status"] == "error" and "calculator" in sent["error"] and "down" in sent["error"]


async def test_researcher_uses_lookup_tool():
    runner, llm = scripted(build_researcher(), call("lookup_fact", topic="Japan"), text("Tokyo."))

    assert await run_agent("Japan?", runner=runner) == "Tokyo."
    assert "124 million" in llm.requests[1].contents[-1].parts[0].function_response.response["result"]


async def test_calculator_uses_arithmetic_tool():
    runner, llm = scripted(build_calculator(), call("multiply", a=68, b=3), text("204"))

    assert await run_agent("68*3", runner=runner) == "204"
    assert llm.requests[1].contents[-1].parts[0].function_response.response["result"] == 204


async def test_error_event_raises():
    runner, _ = scripted(build_researcher(), LlmResponse(error_code="SAFETY", error_message="blocked"))

    with pytest.raises(AgentError, match="SAFETY"):
        await run_agent("hi", runner=runner)


async def test_empty_reply_raises():
    runner, _ = scripted(build_researcher(), LlmResponse(content=types.Content(role="model", parts=[])))

    with pytest.raises(AgentError, match="without a final response"):
        await run_agent("hi", runner=runner)
