"""The agent's logic, built on Google ADK.

Each request runs in its own in-memory session, so requests are independent.
The agent has one function tool and no code execution or other built-ins.
"""

from __future__ import annotations

import os
import uuid

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner, Runner
from google.genai import types

from adk_chat.tools import convert_temperature

APP_NAME = "adk-chat"
USER_ID = "a2a"
DEFAULT_MODEL = "gemini-2.5-flash"
INSTRUCTION = (
    "You are a helpful conversational agent. Keep responses brief and engaging. "
    "Use the convert_temperature tool for any temperature conversion."
)


class AgentError(RuntimeError):
    """The ADK run ended without a usable reply."""


def build_agent() -> LlmAgent:
    return LlmAgent(
        name="chat_agent",
        model=os.getenv("GOOGLE_MODEL") or DEFAULT_MODEL,
        instruction=INSTRUCTION,
        tools=[convert_temperature],
    )


def build_runner() -> Runner:
    return InMemoryRunner(agent=build_agent(), app_name=APP_NAME)


async def run_agent(prompt: str, *, runner: Runner | None = None) -> str:
    """Run the agent on `prompt` in a fresh session and return its final text."""
    runner = runner or build_runner()
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
