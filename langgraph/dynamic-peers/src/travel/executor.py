"""Bridge between A2A messages and a LangGraph agent that keeps `messages` state."""

from __future__ import annotations

import uuid

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.types.a2a_pb2 import Message, Part, Role


def message_text(message: Message | None) -> str:
    if message is None:
        return ""
    return "".join(part.text for part in message.parts)


def reply_text(result: dict) -> str:
    content = result["messages"][-1].content
    return content if isinstance(content, str) else str(content)


class LangGraphExecutor(AgentExecutor):
    """Runs the compiled graph once per incoming A2A message."""

    def __init__(self, graph) -> None:
        self._graph = graph

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        result = await self._graph.ainvoke(
            {"messages": [{"role": "user", "content": message_text(context.message)}]}
        )
        await event_queue.enqueue_event(
            Message(
                message_id=str(uuid.uuid4()),
                role=Role.ROLE_AGENT,
                parts=[Part(text=reply_text(result))],
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        del context, event_queue
