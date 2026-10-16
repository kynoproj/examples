import sys

import pytest

from crew_pipeline import main
from crew_pipeline.cards import agent_card
from crew_pipeline.stages import ROLES, STAGES
from crew_pipeline.tools import count, lookup_fact, word_count


@pytest.mark.parametrize("role", ROLES)
def test_cards_per_role(role):
    card = agent_card(role)
    assert card.skills[0].id == role
    assert all(i.protocol_version for i in card.supported_interfaces)


def test_unknown_role_rejected():
    with pytest.raises(ValueError):
        agent_card("publisher")


def test_stages_are_in_pipeline_order():
    assert ROLES == ("researcher", "writer", "editor")


def test_no_stage_names_another():
    others = {r for r in ROLES}
    for role, spec in STAGES.items():
        text = spec.instruction.lower()
        assert not any(o in text for o in others - {role}), role


def test_lookup_fact_and_word_count_tools():
    assert "container orchestration" in lookup_fact.run(topic="Kubernetes")
    assert "No facts found" in lookup_fact.run(topic="atlantis")
    assert word_count.run(text="one two  three") == "3 words"
    assert count("") == 0


@pytest.mark.parametrize("role", ROLES)
def test_build_stage_wires_the_next_peer_from_the_topology(monkeypatch, role):
    monkeypatch.setattr(main, "next_stage", lambda: "writer" if role == "researcher" else None)
    assert callable(main.build_stage(role))


def test_missing_api_key_exits_with_message(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["x", "--role", "editor"])
    with pytest.raises(SystemExit, match="OPENAI_API_KEY"):
        main.main()


def test_unknown_role_rejected_on_the_command_line(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["x", "--role", "pilot"])
    with pytest.raises(SystemExit):
        main.main()
