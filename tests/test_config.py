from trade_pipeline.config import load_settings


def test_default_log_level(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    settings = load_settings()

    assert settings.log_level == "INFO"


def test_log_level_from_env(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = load_settings()

    assert settings.log_level == "DEBUG"

    