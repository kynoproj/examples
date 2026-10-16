import pytest

from adk_assistant.cards import ROLES, agent_card


@pytest.mark.parametrize("role", ROLES)
def test_cards_per_role(role):
    card = agent_card(role)
    assert card.skills[0].id == role
    assert all(i.protocol_version for i in card.supported_interfaces)


def test_unknown_role_rejected():
    with pytest.raises(ValueError):
        agent_card("planner")
