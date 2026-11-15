from trade_pipeline.consume_trade import validate

GOOD = {
    "reporter_code": 276, "partner_code": 156, "flow_code": "X",
    "cmd_code": "27", "period": 2023, "primary_value": 100.0,
}


def test_validate_accepts_good_row():
    assert validate(GOOD) == []


def test_validate_rejects_bad_flow_and_negative_value():
    row = {**GOOD, "flow_code": "Z", "primary_value": -5}

    errors = validate(row)

    assert "bad flow_code" in errors
    assert "negative primary_value" in errors


def test_validate_reports_missing_fields():
    errors = validate({"flow_code": "X"})

    assert "missing reporter_code" in errors