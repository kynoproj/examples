from assistant.tools import add, divide, lookup_fact, multiply


def test_lookup_fact_hit_is_case_insensitive():
    assert "68 million" in lookup_fact.invoke({"topic": "France"})


def test_lookup_fact_miss():
    assert "No facts found" in lookup_fact.invoke({"topic": "atlantis"})


def test_arithmetic():
    assert add.invoke({"a": 2, "b": 3}) == 5
    assert multiply.invoke({"a": 68, "b": 3}) == 204
    assert divide.invoke({"a": 9, "b": 3}) == "3.0"


def test_divide_by_zero_reports_error():
    assert "division by zero" in divide.invoke({"a": 1, "b": 0})
