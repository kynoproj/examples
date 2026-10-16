"""Bridge between A2A messages and an async `run(prompt) -> reply` callable."""

from __future__ import annotations

import uuid
from typing import Awaitable, Callable

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.types.a2a_pb2 import Message, Part, Role

Run = Callable[[str], Awaitable[str]]


def message_text(message: Message | None) -> str:
    if message is None:
        return ""
    return "".join(part.text for part in message.parts)


class CrewExecutor(AgentExecutor):
    """Runs the agent once per incoming A2A message and replies with its text."""

    def __init__(self, run: Run) -> None:
        self._run = run

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        reply = await self._run(message_text(context.message))
        await event_queue.enqueue_event(
            Message(
                message_id=str(uuid.uuid4()),
                role=Role.ROLE_AGENT,
                parts=[Part(text=reply)],
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        del context, event_queue
