import pytest

from claude_chat.tools import convert, convert_temperature


@pytest.mark.parametrize(
    ("value", "src", "dst", "expected"),
    [(100, "C", "F", 212), (32, "F", "C", 0), (0, "C", "K", 273.15), (72, "f", "c", 22.22)],
)
def test_convert(value, src, dst, expected):
    assert convert(value, src, dst) == pytest.approx(expected, abs=0.01)


def test_convert_rejects_unknown_unit():
    with pytest.raises(ValueError, match="unknown unit"):
        convert(1, "C", "X")


async def test_tool_handler_formats_result():
    result = await convert_temperature.handler({"value": 100, "from_unit": "C", "to_unit": "F"})
    assert result == {"content": [{"type": "text", "text": "212.00 F"}]}


async def test_tool_handler_reports_errors_to_the_model():
    result = await convert_temperature.handler({"value": 1, "from_unit": "C", "to_unit": "X"})
    assert result["is_error"] is True
    assert "unknown unit" in result["content"][0]["text"]


async def test_tool_handler_reports_missing_argument():
    result = await convert_temperature.handler({"value": 1})
    assert result["is_error"] is True
