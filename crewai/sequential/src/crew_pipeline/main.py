"""Serve one stage (researcher, writer or editor) over A2A via Kynomesh.

One image runs every stage; the AgentSet picks the role with --role and, with
`pattern: Sequential`, the order. Each stage forwards its output to the stage
Kynomesh says comes next.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal

from kynomesh import server

from crew_pipeline.agent import build_agent, run_agent
from crew_pipeline.cards import agent_card
from crew_pipeline.executor import CrewExecutor, Run
from crew_pipeline.peers import ask_peer
from crew_pipeline.pipeline import chain, next_stage
from crew_pipeline.stages import ROLES, STAGES

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("crew_pipeline")


def build_stage(role: str) -> Run:
    spec = STAGES[role]
    agent = build_agent(role=spec.name, instruction=spec.instruction, tools=spec.tools)
    next_peer = next_stage()
    _logger.info("stage %s -> %s", role, next_peer or "(last)")

    async def stage_run(request: str) -> str:
        return await run_agent(request, agent=agent)

    return chain(stage_run=stage_run, label=spec.output_label, next_peer=next_peer, ask_peer=ask_peer)


async def serve(role: str) -> None:
    run = build_stage(role)
    loop = asyncio.get_running_loop()
    serve_task = asyncio.ensure_future(server.start(CrewExecutor(run), agent_card(role)))
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, serve_task.cancel)
    try:
        await serve_task
    except asyncio.CancelledError:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True, choices=ROLES)
    args = parser.parse_args()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY must be set (see README)")
    asyncio.run(serve(args.role))


if __name__ == "__main__":
    main()
