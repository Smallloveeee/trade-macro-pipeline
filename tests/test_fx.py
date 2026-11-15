from datetime import date

from trade_pipeline.clients.fx import parse_rates

RAW = [
    {"date": "2023-12-29", "base": "EUR", "quote": "USD", "rate": 1.105},
    {"date": "2024-01-02", "base": "EUR", "quote": "usd", "rate": "1.0956"},
]


def test_parse_rates_drops_rows_outside_range():
    result = parse_rates(RAW, date(2024, 1, 1), date(2024, 1, 31))

    assert len(result) == 1
    assert result[0]["date"] == date(2024, 1, 2)


def test_parse_rates_normalizes_types():
    result = parse_rates(RAW, date(2024, 1, 1), date(2024, 1, 31))

    assert result[0]["quote"] == "USD"
    assert result[0]["rate"] == 1.0956


def test_parse_rates_empty_input():
    result = parse_rates([], date(2024, 1, 1), date(2024, 1, 31))

    assert result == []