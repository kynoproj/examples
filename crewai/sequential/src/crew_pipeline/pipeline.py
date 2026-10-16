"""One stage of the chain: do this stage's work, then pass it to the next stage.

A stage learns who comes next from the Kynomesh topology, not from its code. Under
`pattern: Sequential` each agent sees only the next agent, so `client.peers()` has
one entry, except for the last stage, which has none. The reply travels back up the
chain: every stage returns whatever its successor returned.
"""

from __future__ import annotations

import logging
from typing import Awaitable, Callable

from kynomesh import client

_logger = logging.getLogger(__name__)

Run = Callable[[str], Awaitable[str]]
AskPeer = Callable[[str, str], Awaitable[str]]


def next_stage(list_peers: Callable[[], list[str]] = client.peers) -> str | None:
    """The one stage after this one, or None for the last stage.

    Outside a Kynomesh pod there is no topology: the stage then runs on its own,
    which is handy for trying one stage locally.
    """
    try:
        peers = list_peers()
    except client.TopologyNotAvailableError:
        _logger.warning("no Kynomesh topology: running as a standalone stage")
        return None
    if len(peers) > 1:
        raise ValueError(f"a Sequential stage has at most one next stage; got {sorted(peers)}")
    return peers[0] if peers else None


def handoff_message(received: str, label: str, output: str) -> str:
    """What the next stage receives: everything this stage received, plus its output.

    The message grows into a transcript (request, research notes, draft), so each
    stage sees the whole trail and nothing has to be parsed back out.
    """
    return f"{received}\n\n{label}:\n{output}"


def chain(
    *,
    stage_run: Run,
    label: str,
    next_peer: str | None,
    ask_peer: AskPeer,
) -> Run:
    """Wrap this stage's work so it forwards its output to `next_peer`, if any."""

    async def run(received: str) -> str:
        output = await stage_run(received)
        if next_peer is None:
            return output
        _logger.info("forwarding %s to %r", label.lower(), next_peer)
        return await ask_peer(next_peer, handoff_message(received, label, output))

    return run
