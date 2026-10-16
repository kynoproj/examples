import asyncio
import threading

import pytest

from crew_travel.peers import blocking_ask


async def test_runs_the_coroutine_on_the_given_loop_from_another_thread():
    loop = asyncio.get_running_loop()
    seen = {}

    async def ask(name, text):
        seen["loop"] = asyncio.get_running_loop()
        return f"{name}:{text}"

    call = blocking_ask(ask, loop)
    result = await asyncio.to_thread(call, "calc", "1+1")

    assert result == "calc:1+1"
    assert seen["loop"] is loop


async def test_errors_from_the_peer_propagate():
    async def ask(name, text):
        raise ValueError("bad peer")

    with pytest.raises(ValueError, match="bad peer"):
        await asyncio.to_thread(blocking_ask(ask, asyncio.get_running_loop()), "x", "y")


async def test_timeout_names_the_peer_and_cancels_the_call():
    cancelled = threading.Event()

    async def ask(name, text):
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    call = blocking_ask(ask, asyncio.get_running_loop(), timeout=0.05)
    with pytest.raises(TimeoutError, match="'slow'"):
        await asyncio.to_thread(call, "slow", "x")

    await asyncio.sleep(0.05)
    assert cancelled.is_set()


async def test_calling_on_the_loop_thread_fails_fast_instead_of_deadlocking():
    async def ask(name, text):
        return "never"

    call = blocking_ask(ask, asyncio.get_running_loop())

    with pytest.raises(RuntimeError, match="deadlock"):
        call("x", "y")
