"""A scripted model for driving real ADK runs without calling Gemini."""

from collections.abc import AsyncGenerator

from google.adk.agents import LlmAgent
from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

from adk_assistant.agents import APP_NAME


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


def call(name: str, **args) -> LlmResponse:
    part = types.Part(function_call=types.FunctionCall(name=name, args=args))
    return LlmResponse(content=types.Content(role="model", parts=[part]))


def scripted(runner, *script: LlmResponse) -> tuple[InMemoryRunner, ScriptedLlm]:
    """Rebuild `runner`'s agent on a scripted model; tools and instruction are kept."""
    llm = ScriptedLlm(script=list(script), requests=[])
    agent: LlmAgent = runner.agent.model_copy(update={"model": llm})
    return InMemoryRunner(agent=agent, app_name=APP_NAME), llm
