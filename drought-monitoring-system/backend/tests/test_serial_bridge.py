from scripts.serial_bridge import parse_json_line


def test_parse_json_line_accepts_esp32_reading() -> None:
    payload = parse_json_line(
        '{"type":"data_ideal","water_level":1700,'
        '"soil_moisture":2100,"led_color":"GREEN","timestamp_ms":1234}'
    )

    assert payload == {
        "type": "data_ideal",
        "water_level": 1700,
        "soil_moisture": 2100,
        "led_color": "GREEN",
        "timestamp_ms": 1234,
    }


def test_parse_json_line_ignores_human_status_text() -> None:
    assert parse_json_line("Status: Full water supply | LED: GREEN") is None


def test_parse_json_line_rejects_missing_required_field() -> None:
    assert (
        parse_json_line(
            '{"type":"data_ideal","water_level":1700,"timestamp_ms":1234}'
        )
        is None
    )
