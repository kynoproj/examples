import logging

import pytest
from kynomesh import client

from crew_pipeline.pipeline import chain, handoff_message, next_stage


def stage(output):
    seen = []

    async def run(received):
        seen.append(received)
        return output

    run.seen = seen
    return run


async def ask_never(name, text):
    raise AssertionError("the last stage must not call a peer")


def test_next_stage_is_the_single_peer():
    assert next_stage(lambda: ["writer"]) == "writer"


def test_last_stage_has_no_next():
    assert next_stage(lambda: []) is None


def test_more_than_one_next_stage_is_rejected():
    with pytest.raises(ValueError, match="at most one"):
        next_stage(lambda: ["a", "b"])


def test_outside_kynomesh_the_stage_runs_standalone(caplog):
    def no_topology():
        raise client.TopologyNotAvailableError

    caplog.set_level(logging.WARNING)

    assert next_stage(no_topology) is None
    assert "standalone" in caplog.text


def test_handoff_appends_this_stages_output_to_what_it_received():
    assert handoff_message("req", "Research notes", "- fact") == "req\n\nResearch notes:\n- fact"


async def test_last_stage_returns_its_own_output():
    run = chain(stage_run=stage("final"), label="Final text", next_peer=None, ask_peer=ask_never)

    assert await run("in") == "final"


async def test_middle_stage_forwards_and_returns_the_reply_from_downstream():
    asked = []

    async def ask_peer(name, text):
        asked.append((name, text))
        return "reply from editor"

    run = chain(stage_run=stage("a draft"), label="Draft", next_peer="editor", ask_peer=ask_peer)

    assert await run("request\n\nResearch notes:\n- fact") == "reply from editor"
    assert asked == [("editor", "request\n\nResearch notes:\n- fact\n\nDraft:\na draft")]


async def test_multiparagraph_requests_survive_the_chain():
    asked = []

    async def ask_peer(name, text):
        asked.append(text)
        return "ok"

    request = "Write about Japan.\n\nKeep it friendly."
    await chain(stage_run=stage("notes"), label="Research notes", next_peer="writer", ask_peer=ask_peer)(request)

    assert asked[0].startswith(request)


async def test_downstream_failure_propagates():
    async def ask_peer(name, text):
        raise RuntimeError("writer down")

    run = chain(stage_run=stage("x"), label="Draft", next_peer="writer", ask_peer=ask_peer)

    with pytest.raises(RuntimeError, match="writer down"):
        await run("in")
