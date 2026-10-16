from unittest.mock import AsyncMock

import pytest
from a2a.types.a2a_pb2 import AgentCard, AgentSkill

from adk_travel.discovery import WorkerInfo, discover_workers

WARM = AsyncMock()


def card(description: str, *skills: tuple[str, str]) -> AgentCard:
    return AgentCard(
        description=description,
        skills=[AgentSkill(id=n, name=n, description=d) for n, d in skills],
    )


async def test_discovers_every_peer_sorted_by_name_with_card_details():
    cards = {"hotels": card("Finds hotels", ("search", "Hotel options")), "flights": card("Finds flights")}

    workers = await discover_workers(
        list_peers=lambda: ["hotels", "flights"],
        warm_client=WARM,
        resolve_card=AsyncMock(side_effect=lambda name: cards[name]),
    )

    assert workers == (
        WorkerInfo("flights", "Finds flights", ()),
        WorkerInfo("hotels", "Finds hotels", (("search", "Hotel options"),)),
    )


async def test_no_peers_yields_empty_tuple():
    resolve = AsyncMock()
    assert await discover_workers(list_peers=lambda: [], warm_client=WARM, resolve_card=resolve) == ()
    resolve.assert_not_awaited()


async def test_transient_failure_is_retried():
    resolve = AsyncMock(side_effect=[RuntimeError("not ready"), card("Finds flights")])

    workers = await discover_workers(list_peers=lambda: ["flights"], warm_client=WARM, resolve_card=resolve, delay=0)

    assert [w.name for w in workers] == ["flights"]
    assert resolve.await_count == 2


async def test_unreachable_peer_is_skipped_after_retries():
    async def resolve(name):
        if name == "weather":
            raise RuntimeError("down")
        return card("ok")

    workers = await discover_workers(
        list_peers=lambda: ["weather", "flights"], warm_client=WARM, resolve_card=resolve, attempts=2, delay=0
    )

    assert [w.name for w in workers] == ["flights"]


async def test_topology_errors_propagate():
    def boom():
        raise LookupError("no topology")

    with pytest.raises(LookupError):
        await discover_workers(list_peers=boom, warm_client=WARM, resolve_card=AsyncMock())


async def test_every_peer_is_warmed_so_drift_detection_knows_its_card():
    warm = AsyncMock()

    await discover_workers(
        list_peers=lambda: ["hotels", "flights"],
        warm_client=warm,
        resolve_card=AsyncMock(return_value=card("ok")),
    )

    assert [c.args[0] for c in warm.await_args_list] == ["flights", "hotels"]


async def test_peer_that_cannot_be_warmed_is_skipped():
    warm = AsyncMock(side_effect=RuntimeError("unreachable"))
    resolve = AsyncMock()

    workers = await discover_workers(
        list_peers=lambda: ["weather"], warm_client=warm, resolve_card=resolve, attempts=2, delay=0
    )

    assert workers == ()
    resolve.assert_not_awaited()
