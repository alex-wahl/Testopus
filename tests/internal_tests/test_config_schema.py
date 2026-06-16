import pytest
from pydantic import ValidationError

from core.config import config_loader
from core.config.config_loader import ConfigError, load_config_from_cli
from core.config.schema import GasagConfig, RootConfig


def test_schema_accepts_valid_config():
    cfg = {
        "configuration": {
            "gasag": {"web_url": "https://x.test", "username": "u", "password": "p"}
        }
    }
    RootConfig.model_validate(cfg)  # must not raise


def test_schema_allows_extra_keys():
    cfg = {
        "configuration": {"gasag": {"web_url": "https://x.test", "extra": 1}},
        "startrack": {"enabled": True},
    }
    RootConfig.model_validate(cfg)  # extra top-level + extra gasag keys allowed


def test_schema_rejects_gasag_without_web_url():
    with pytest.raises(ValidationError):
        GasagConfig.model_validate({"username": "u"})


def test_load_config_from_cli_raises_on_invalid(tmp_path, monkeypatch):
    bad = tmp_path / "default.yaml"
    bad.write_text("configuration:\n  gasag:\n    username: u\n")  # no web_url
    monkeypatch.setattr("sys.argv", ["pytest"])
    monkeypatch.setattr(
        config_loader, "get_config_path", lambda override=False: str(bad)
    )
    with pytest.raises(ConfigError):
        load_config_from_cli(None)


def test_load_config_from_cli_accepts_valid(tmp_path, monkeypatch):
    good = tmp_path / "default.yaml"
    good.write_text("configuration:\n  gasag:\n    web_url: https://x.test\n")
    monkeypatch.setattr("sys.argv", ["pytest"])
    monkeypatch.setattr(
        config_loader, "get_config_path", lambda override=False: str(good)
    )
    cfg = load_config_from_cli(None)
    assert cfg["configuration"]["gasag"]["web_url"] == "https://x.test"
