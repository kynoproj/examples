"""LangGraph A2A conversational agent.

It has no Kynomesh imports; main.py serves it. The agent needs a `messages` key
in its state, which is how A2A text parts reach a LangGraph graph. The model is
configurable via OPENAI_MODEL.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, TypedDict

from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from openai import AsyncOpenAI

_logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a helpful conversational agent. Keep responses brief and engaging."
DEFAULT_MODEL = "gpt-3.5-turbo"


class Context(TypedDict):
    """Context parameters for the agent."""

    my_configurable_param: str


@dataclass
class State:
    """Input state for the agent: A2A conversational messages."""

    messages: List[Dict[str, Any]]


async def call_model(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Process conversational messages and return output using OpenAI."""
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    latest_message = state.messages[-1] if state.messages else {}
    user_content = latest_message.get("content", "No message content")

    try:
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=100,
            temperature=0.7,
        )
        ai_response = response.choices[0].message.content
    except Exception as e:
        _logger.exception("OpenAI call failed")
        ai_response = f"I received your message but had trouble processing it. Error: {str(e)[:50]}..."

    return {"messages": [*state.messages, {"role": "assistant", "content": ai_response}]}


graph = (
    StateGraph(State, context_schema=Context)
    .add_node(call_model)
    .add_edge("__start__", "call_model")
    .compile()
)
