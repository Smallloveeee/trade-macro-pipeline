import pytest
import requests

from trade_pipeline.clients import comtrade
from trade_pipeline.clients.comtrade import ComtradeError, fetch_trade, parse_trade


def make_row(customs="C00", mot=0, partner2=0, value=100.0):
    return {
        "reporterCode": 276, "partnerCode": 156, "flowCode": "X",
        "cmdCode": "27", "period": "2023",
        "customsCode": customs, "motCode": mot, "partner2Code": partner2,
        "primaryValue": value, "fobvalue": value, "cifvalue": None,
    }


def test_parse_trade_picks_only_total_row():
    payload = {"data": [make_row("C03", 1000, 0, 5.0), make_row(value=176.0)]}

    result = parse_trade(payload)

    assert len(result) == 1
    assert result[0]["primary_value"] == 176.0


def test_parse_trade_raises_on_duplicate_total():
    payload = {"data": [make_row(), make_row()]}

    with pytest.raises(ComtradeError):
        parse_trade(payload)


def test_parse_trade_raises_when_total_missing():
    payload = {"data": [make_row("C03", 1000, 0)]}

    with pytest.raises(ComtradeError):
        parse_trade(payload)


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = str(self._payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


def test_fetch_retries_then_succeeds(monkeypatch):
    responses = [FakeResponse(503), FakeResponse(200, {"data": []})]
    sleeps = []
    monkeypatch.setattr(comtrade.requests, "get", lambda *a, **k: responses.pop(0))
    monkeypatch.setattr(comtrade.time, "sleep", sleeps.append)

    payload = fetch_trade("key", "276", "156", "X", "27", "2023")

    assert payload == {"data": []}
    assert sleeps == [2]


def test_fetch_does_not_retry_client_error(monkeypatch):
    sleeps = []
    monkeypatch.setattr(comtrade.requests, "get", lambda *a, **k: FakeResponse(401))
    monkeypatch.setattr(comtrade.time, "sleep", sleeps.append)

    with pytest.raises(requests.HTTPError):
        fetch_trade("key", "276", "156", "X", "27", "2023")

    assert sleeps == []