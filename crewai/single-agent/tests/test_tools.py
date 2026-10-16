import pytest

from crew_chat.tools import convert, convert_temperature


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
    assert convert_temperature.run(value=100, from_unit="C", to_unit="F") == "212.00 F"


def test_tool_reports_errors_to_the_model():
    assert "unknown unit" in convert_temperature.run(value=1, from_unit="C", to_unit="X")


def test_tool_schema_exposes_its_arguments():
    schema = convert_temperature.args_schema.model_json_schema()
    assert set(schema["properties"]) == {"value", "from_unit", "to_unit"}
