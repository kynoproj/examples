"""Shared Claude Agent SDK plumbing for every role.

Each request runs one `query()`, which spawns the Claude Code CLI bundled with the
SDK. Agents run in pods, so every role is locked down the same way: no built-in
tools (Bash, Read, Write, ...), no filesystem settings, only the role's own
in-process tools, and non-interactive permissions.
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator, Callable, Sequence

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ResultMessage,
    SdkMcpTool,
    create_sdk_mcp_server,
    query,
)

SERVER_NAME = "tools"
MAX_TURNS = 8

QueryFn = Callable[..., AsyncIterator[Any]]


class AgentError(RuntimeError):
    """The Claude run ended without a usable result."""


def locked_down_options(
    *,
    system_prompt: str,
    tools: Sequence[SdkMcpTool],
    server_name: str = SERVER_NAME,
    max_turns: int = MAX_TURNS,
) -> ClaudeAgentOptions:
    """Options for an agent whose only capabilities are `tools`."""
    servers = {server_name: create_sdk_mcp_server(name=server_name, tools=list(tools))} if tools else {}
    return ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=os.getenv("ANTHROPIC_MODEL") or None,
        tools=[],  # disable every built-in tool
        mcp_servers=servers,
        strict_mcp_config=True,  # ignore any other MCP config on disk
        allowed_tools=[f"mcp__{server_name}__{t.name}" for t in tools],
        permission_mode="dontAsk",  # deny anything not allowed instead of prompting
        setting_sources=[],  # load no user/project/local settings
        max_turns=max_turns,
    )


async def run_agent(
    prompt: str,
    *,
    options: ClaudeAgentOptions,
    query_fn: QueryFn = query,
) -> str:
    """Run the agent on `prompt` and return its final text."""
    final: ResultMessage | None = None
    async for message in query_fn(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            final = message
    if final is None:
        raise AgentError("Claude finished without a result message")
    if final.is_error:
        raise AgentError(f"Claude run failed: {final.subtype} {final.errors or ''}".strip())
    return final.result or ""
