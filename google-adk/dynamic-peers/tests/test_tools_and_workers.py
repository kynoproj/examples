import pytest

from adk_travel.cards import extra_skills, supervisor_card, worker_card
from adk_travel.tools import get_forecast, search_flights, search_hotels
from adk_travel.workers import WORKERS


def test_tools_return_stub_data():
    assert "NH7" in search_flights("SFO", "Tokyo")["result"]
    assert "Shinjuku" in search_hotels("tokyo")["result"]
    assert "rain" in get_forecast("Tokyo")["result"]


def test_unknown_city_is_a_normal_reply_not_an_error():
    result = search_hotels("Atlantis")
    assert result["status"] == "success"
    assert "No hotels" in result["result"]


@pytest.mark.parametrize("role", WORKERS)
def test_every_worker_tool_has_a_docstring_adk_can_show_the_model(role):
    for tool in WORKERS[role].tools:
        assert tool.__doc__ and "Args:" in tool.__doc__


@pytest.mark.parametrize("role", WORKERS)
def test_worker_cards_advertise_their_skills_and_protocol_version(role):
    card = worker_card(role)
    assert card.name == role
    assert [s.id for s in card.skills] == [s.id for s in WORKERS[role].skills]
    assert all(i.protocol_version for i in card.supported_interfaces)


def test_extra_skills_env_changes_the_card(monkeypatch):
    base = worker_card("hotels")
    monkeypatch.setenv("EXTRA_SKILLS", "price-comparison, loyalty")

    changed = worker_card("hotels")

    assert [s.id for s in changed.skills][-2:] == ["price-comparison", "loyalty"]
    assert changed != base


def test_extra_skills_ignores_blanks():
    assert extra_skills(" , ") == ()


def test_supervisor_card_has_a_skill():
    assert supervisor_card().skills
