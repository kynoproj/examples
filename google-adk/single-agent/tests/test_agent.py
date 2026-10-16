from collections.abc import AsyncGenerator

import pytest
from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

from adk_chat import agent as agent_module
from adk_chat.agent import APP_NAME, DEFAULT_MODEL, AgentError, build_agent, run_agent


class ScriptedLlm(BaseLlm):
    """Replays canned responses, one per model call, and records the requests."""

    model: str = "scripted"
    script: list[LlmResponse]
    requests: list[LlmRequest] = []

    async def generate_content_async(self, llm_request, stream=False) -> AsyncGenerator[LlmResponse, None]:
        self.requests.append(llm_request)
        yield self.script[len(self.requests) - 1]


def text(value: str) -> LlmResponse:
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=value)]))


def tool_call(**args) -> LlmResponse:
    call = types.Part(function_call=types.FunctionCall(name="convert_temperature", args=args))
    return LlmResponse(content=types.Content(role="model", parts=[call]))


def runner_with(*script: LlmResponse) -> tuple[InMemoryRunner, ScriptedLlm]:
    llm = ScriptedLlm(script=list(script), requests=[])
    agent = build_agent().model_copy(update={"model": llm})
    return InMemoryRunner(agent=agent, app_name=APP_NAME), llm


def test_agent_has_only_the_conversion_tool():
    assert [t.__name__ for t in build_agent().tools] == ["convert_temperature"]


def test_model_comes_from_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_MODEL", "gemini-custom")
    assert build_agent().model == "gemini-custom"


def test_model_defaults(monkeypatch):
    monkeypatch.delenv("GOOGLE_MODEL", raising=False)
    assert build_agent().model == DEFAULT_MODEL


async def test_returns_the_final_reply():
    runner, _ = runner_with(text("Hello!"))

    assert await run_agent("hi", runner=runner) == "Hello!"


async def test_calls_the_tool_and_replies_with_its_result():
    runner, llm = runner_with(tool_call(value=72, from_unit="F", to_unit="C"), text("That is 22.22 C."))

    assert await run_agent("What is 72 F in Celsius?", runner=runner) == "That is 22.22 C."
    # The second model call saw the tool's output.
    sent = llm.requests[1].contents[-1].parts[0].function_response
    assert sent.response == {"status": "success", "result": "22.22 C"}


async def test_each_request_gets_a_fresh_session():
    runner, llm = runner_with(text("one"), text("two"))

    await run_agent("first", runner=runner)
    await run_agent("second", runner=runner)

    second_prompts = [p.text for c in llm.requests[1].contents for p in c.parts if p.text]
    assert "first" not in second_prompts


async def test_error_event_raises():
    failure = LlmResponse(error_code="SAFETY", error_message="blocked")
    runner, _ = runner_with(failure)

    with pytest.raises(AgentError, match="SAFETY"):
        await run_agent("hi", runner=runner)


async def test_empty_reply_raises():
    runner, _ = runner_with(LlmResponse(content=types.Content(role="model", parts=[])))

    with pytest.raises(AgentError, match="without a final response"):
        await run_agent("hi", runner=runner)


def test_build_runner_uses_the_app_name():
    assert agent_module.build_runner().app_name == APP_NAME
