"""Shared CrewAI plumbing for every role.

Every role is a standalone CrewAI `Agent` whose only capabilities are its own
tools. `kickoff_async` answers each request from a clean conversation, so there
is no Task or Crew to wire up.
"""

from __future__ import annotations

import os
from typing import Sequence

from crewai import LLM, Agent
from crewai.tools import BaseTool
from crewai_core.printer import set_suppress_console_output

DEFAULT_MODEL = "gpt-4o-mini"
MAX_ITER = 8


class AgentError(RuntimeError):
    """The CrewAI run ended without a usable reply."""


def build_agent(
    *,
    role: str,
    instruction: str,
    tools: Sequence[BaseTool],
    llm: LLM | None = None,
) -> Agent:
    """An agent whose only capabilities are `tools`."""
    return Agent(
        role=role,
        goal=f"Do your job as the {role}, using only your tools",
        backstory=instruction,
        llm=llm or LLM(model=os.getenv("OPENAI_MODEL") or DEFAULT_MODEL, temperature=0),
        tools=list(tools),
        max_iter=MAX_ITER,  # bounds the tool-use loop
        verbose=False,
    )


async def run_agent(prompt: str, *, agent: Agent) -> str:
    """Run the agent on `prompt` and return its final text."""
    set_suppress_console_output(True)  # CrewAI draws panels to stdout; keep pod logs clean
    output = await agent.kickoff_async(prompt)
    if not output.raw:
        raise AgentError("CrewAI finished without a final answer")
    return output.raw
