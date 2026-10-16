import pytest

from adk_chat.tools import convert, convert_temperature


@pytest.mark.parametrize(
    ("value", "src", "dst", "expected"),
    [(100, "C", "F", 212), (32, "F", "C", 0), (0, "C", "K", 273.15), (72, "f", "c", 22.22)],
)
def test_convert(value, src, dst, expected):
    assert convert(value, src, dst) == pytest.approx(expected, abs=0.01)


def test_convert_rejects_unknown_unit():
    with pytest.raises(ValueError, match="unknown unit"):
        convert(1, "C", "X")


def test_tool_formats_result():
    assert convert_temperature(100, "C", "F") == {"status": "success", "result": "212.00 F"}


def test_tool_reports_errors_to_the_model():
    result = convert_temperature(1, "C", "X")
    assert result["status"] == "error"
    assert "unknown unit" in result["error"]
