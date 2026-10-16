"""Shared Google ADK plumbing for every role.

Every role is an `LlmAgent` whose only capabilities are its own tools, run in a
fresh in-memory session per request so requests are independent.
"""

from __future__ import annotations

import os
import uuid
from typing import Callable, Sequence

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner, Runner
from google.genai import types

APP_NAME = "adk-travel"
USER_ID = "a2a"
DEFAULT_MODEL = "gemini-2.5-flash"


class AgentError(RuntimeError):
    """The ADK run ended without a usable reply."""


def build_runner(*, name: str, instruction: str, tools: Sequence[Callable]) -> Runner:
    """A runner for an agent whose only capabilities are `tools`."""
    agent = LlmAgent(
        name=name,
        model=os.getenv("GOOGLE_MODEL") or DEFAULT_MODEL,
        instruction=instruction,
        tools=list(tools),
    )
    return InMemoryRunner(agent=agent, app_name=APP_NAME)


async def run_agent(prompt: str, *, runner: Runner) -> str:
    """Run the agent on `prompt` in a fresh session and return its final text."""
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=str(uuid.uuid4())
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    reply = ""
    async for event in runner.run_async(user_id=USER_ID, session_id=session.id, new_message=message):
        if event.error_code or event.error_message:
            raise AgentError(f"ADK run failed: {event.error_code} {event.error_message or ''}".strip())
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(part.text or "" for part in event.content.parts)
    if not reply:
        raise AgentError("ADK finished without a final response")
    return reply
