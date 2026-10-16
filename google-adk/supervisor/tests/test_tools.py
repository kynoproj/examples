from adk_assistant.tools import add, divide, lookup_fact, multiply


def test_lookup_fact_hit_is_case_insensitive():
    assert "68 million" in lookup_fact("France")["result"]


def test_lookup_fact_miss_is_a_normal_reply():
    result = lookup_fact("atlantis")
    assert result["status"] == "success"
    assert "No facts found" in result["result"]


def test_arithmetic():
    assert add(2, 3)["result"] == 5
    assert multiply(68, 3)["result"] == 204
    assert divide(9, 3)["result"] == 3


def test_divide_by_zero_reports_error():
    result = divide(1, 0)
    assert result["status"] == "error"
    assert "division by zero" in result["error"]
