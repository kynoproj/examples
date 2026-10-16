from crew_assistant.tools import add, divide, lookup_fact, multiply


def test_lookup_fact_hit_is_case_insensitive():
    assert "68 million" in lookup_fact.run(topic="France")


def test_lookup_fact_miss():
    assert "No facts found" in lookup_fact.run(topic="atlantis")


def test_arithmetic():
    assert add.run(a=2, b=3) == "5.0"
    assert multiply.run(a=68, b=3) == "204.0"
    assert divide.run(a=9, b=3) == "3.0"


def test_divide_by_zero_reports_error():
    assert "division by zero" in divide.run(a=1, b=0)
