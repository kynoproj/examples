"""A supervisor whose tools are generated from discovered workers."""

from __future__ import annotations

import logging
import re
from typing import Any, Awaitable, Callable

from claude_agent_sdk import ClaudeAgentOptions, SdkMcpTool, tool

from claude_travel.agent import SERVER_NAME, locked_down_options
from claude_travel.discovery import WorkerInfo
from claude_travel.tools import error_result, text_result

_logger = logging.getLogger(__name__)

AskPeer = Callable[[str, str], Awaitable[str]]

_PROMPT_HEADER = (
    "You are a travel-planning supervisor. You cannot answer travel questions yourself; "
    "delegate to your workers with their tools, calling several when a request spans "
    "more than one. Finish with a short final answer. "
    "If no worker can handle part of a request, say so plainly."
)


def tool_name(worker_name: str) -> str:
    return "ask_" + re.sub(r"[^A-Za-z0-9_-]", "_", worker_name)


def describe(worker: WorkerInfo) -> str:
    skills = "; ".join(f"{n}: {d}" if d else n for n, d in worker.skills)
    parts = [worker.description or f"Worker {worker.name}"]
    if skills:
        parts.append(f"Skills: {skills}.")
    return " ".join(parts)


def build_prompt(workers: tuple[WorkerInfo, ...]) -> str:
    if not workers:
        return _PROMPT_HEADER + "\nYou currently have no workers, so you cannot help with requests."
    lines = [f"- {tool_name(w.name)}: {describe(w)}" for w in workers]
    return _PROMPT_HEADER + "\nYour workers:\n" + "\n".join(lines)


def peer_tools(workers: tuple[WorkerInfo, ...], ask_peer: AskPeer) -> list[SdkMcpTool]:
    """One SDK tool per worker; each delegates to that worker over A2A."""

    def make(worker: WorkerInfo) -> SdkMcpTool:
        async def delegate(args: dict[str, Any]) -> dict[str, Any]:
            try:
                return text_result(await ask_peer(worker.name, args["request"]))
            except KeyError:
                return error_result("Error: missing 'request' argument")
            except Exception as e:  # the model should see a failed worker, not crash the run
                _logger.exception("worker %r failed", worker.name)
                return error_result(f"Error: worker {worker.name!r} failed: {e}")

        return tool(tool_name(worker.name), describe(worker), {"request": str})(delegate)

    return [make(w) for w in workers]


def supervisor_options(workers: tuple[WorkerInfo, ...], ask_peer: AskPeer) -> ClaudeAgentOptions:
    return locked_down_options(
        system_prompt=build_prompt(workers),
        tools=peer_tools(workers, ask_peer),
        server_name=SERVER_NAME,
    )
