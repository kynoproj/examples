"""The agent's logic, built on the Claude Agent SDK.

Each request runs one `query()`, which spawns the Claude Code CLI bundled with
the SDK. The agent runs in a pod, so it is locked down: no built-in tools (Bash,
Read, Write, ...), no filesystem settings, only our in-process tool, and
non-interactive permissions.
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator, Callable

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, create_sdk_mcp_server, query

from claude_chat.tools import convert_temperature

SERVER_NAME = "tools"
SYSTEM_PROMPT = (
    "You are a helpful conversational agent. Keep responses brief and engaging. "
    "Use the convert_temperature tool for any temperature conversion."
)
MAX_TURNS = 5

QueryFn = Callable[..., AsyncIterator[Any]]


class AgentError(RuntimeError):
    """The Claude run ended without a usable result."""


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        model=os.getenv("ANTHROPIC_MODEL") or None,
        tools=[],  # disable every built-in tool
        mcp_servers={SERVER_NAME: create_sdk_mcp_server(name=SERVER_NAME, tools=[convert_temperature])},
        strict_mcp_config=True,  # ignore any other MCP config on disk
        allowed_tools=[f"mcp__{SERVER_NAME}__{convert_temperature.name}"],
        permission_mode="dontAsk",  # deny anything not allowed instead of prompting
        setting_sources=[],  # load no user/project/local settings
        max_turns=MAX_TURNS,
    )


async def run_agent(
    prompt: str,
    *,
    options: ClaudeAgentOptions | None = None,
    query_fn: QueryFn = query,
) -> str:
    """Run the agent on `prompt` and return its final text."""
    final: ResultMessage | None = None
    async for message in query_fn(prompt=prompt, options=options or build_options()):
        if isinstance(message, ResultMessage):
            final = message
    if final is None:
        raise AgentError("Claude finished without a result message")
    if final.is_error:
        raise AgentError(f"Claude run failed: {final.subtype} {final.errors or ''}".strip())
    return final.result or ""
