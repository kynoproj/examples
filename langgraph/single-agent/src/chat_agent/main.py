"""Serve the LangGraph chat agent over A2A via the Kynomesh SDK."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import uuid

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.types.a2a_pb2 import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Message,
    Part,
    Role,
)
from a2a.utils.constants import PROTOCOL_VERSION_CURRENT, TransportProtocol
from kynomesh import server

from chat_agent.graph import graph

logging.basicConfig(level=logging.INFO)


def message_text(message: Message | None) -> str:
    if message is None:
        return ""
    return "".join(part.text for part in message.parts)


class LangGraphExecutor(AgentExecutor):
    """Runs the compiled LangGraph for each incoming A2A message."""

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
                parts=[Part(text=result["messages"][-1]["content"])],
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        del context, event_queue


def agent_card() -> AgentCard:
    # URLs are placeholders for local dev; Kynomesh rewrites them in-cluster.
    return AgentCard(
        name="LangGraph Chat Agent",
        description="A conversational LangGraph agent (OpenAI) served through Kynomesh",
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url="http://127.0.0.1:8088/a2a/jsonrpc",
                protocol_binding=TransportProtocol.JSONRPC.value,
                protocol_version=PROTOCOL_VERSION_CURRENT,
            ),
            AgentInterface(
                url="127.0.0.1:8089",
                protocol_binding=TransportProtocol.GRPC.value,
                protocol_version=PROTOCOL_VERSION_CURRENT,
            ),
        ],
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="chat",
                name="Chat",
                description="Brief, friendly conversational replies",
                tags=["chat"],
                examples=["What is Kubernetes?"],
            )
        ],
    )


async def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY must be set (see README)")
    loop = asyncio.get_running_loop()
    serve_task = asyncio.ensure_future(
        server.start(LangGraphExecutor(graph), agent_card())
    )
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, serve_task.cancel)
    try:
        await serve_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    asyncio.run(main())
