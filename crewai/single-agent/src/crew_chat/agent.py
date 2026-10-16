"""The agent's logic, built on CrewAI. No Kynomesh imports.

A standalone CrewAI `Agent` answers each request with `kickoff_async`, so there
is no Task or Crew to wire up. Each request starts from a clean conversation.
"""

from __future__ import annotations

import os

from crewai import LLM, Agent
from crewai_core.printer import set_suppress_console_output

from crew_chat.tools import convert_temperature

DEFAULT_MODEL = "gpt-4o-mini"
MAX_ITER = 5


class AgentError(RuntimeError):
    """The CrewAI run ended without a usable reply."""


def build_agent(llm: LLM | None = None) -> Agent:
    return Agent(
        role="Conversational assistant",
        goal="Answer the user's message helpfully and briefly",
        backstory=(
            "You are a helpful conversational agent. Keep responses brief and engaging. "
            "Use the convert_temperature tool for any temperature conversion."
        ),
        llm=llm or LLM(model=os.getenv("OPENAI_MODEL") or DEFAULT_MODEL, temperature=0),
        tools=[convert_temperature],
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
