import pytest

from travel.cards import extra_skills, supervisor_card, worker_card
from travel.tools import get_forecast, search_flights, search_hotels
from travel.workers import WORKERS


def test_tools_return_stub_data_and_handle_unknown_cities():
    assert "NH7" in search_flights.invoke({"origin": "SFO", "destination": "Tokyo"})
    assert "Shinjuku" in search_hotels.invoke({"city": "tokyo"})
    assert "rain" in get_forecast.invoke({"city": "Tokyo"})
    assert "No hotels" in search_hotels.invoke({"city": "Atlantis"})


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
