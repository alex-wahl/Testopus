import copy

import pytest

from core.config.config_loader import ConfigError, load_config, merge_configs


class TestMergeConfigs:
    def test_override_takes_precedence_for_scalars(self):
        assert merge_configs({"a": 1, "b": 2}, {"b": 3}) == {"a": 1, "b": 3}

    def test_nested_dicts_merge_recursively(self):
        default = {"x": {"p": 1, "q": 2}}
        override = {"x": {"q": 9, "r": 3}}
        assert merge_configs(default, override) == {"x": {"p": 1, "q": 9, "r": 3}}

    def test_key_only_in_override_is_added(self):
        assert merge_configs({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_non_dict_override_wins(self):
        assert merge_configs({"a": 1}, "scalar") == "scalar"

    def test_does_not_mutate_or_alias_inputs(self):
        default = {"x": {"p": 1}}
        default_snapshot = copy.deepcopy(default)
        override = {"y": {"q": 2}}

        result = merge_configs(default, override)
        # Mutating the result must not leak back into either input (no aliasing).
        result["x"]["p"] = 999
        result["y"]["q"] = 999

        assert default == default_snapshot
        assert override == {"y": {"q": 2}}


class TestLoadConfig:
    def test_missing_file_raises_config_error(self, tmp_path):
        with pytest.raises(ConfigError):
            load_config(str(tmp_path / "nope.yaml"))

    def test_invalid_yaml_raises_config_error(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("a: [unclosed\n")
        with pytest.raises(ConfigError):
            load_config(str(bad))

    def test_non_mapping_raises_config_error(self, tmp_path):
        seq = tmp_path / "list.yaml"
        seq.write_text("- 1\n- 2\n")
        with pytest.raises(ConfigError):
            load_config(str(seq))

    def test_empty_file_returns_empty_dict(self, tmp_path):
        empty = tmp_path / "empty.yaml"
        empty.write_text("")
        assert load_config(str(empty)) == {}

    def test_env_interpolation_uses_environment(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MY_USER", "alice")
        cfg = tmp_path / "c.yaml"
        cfg.write_text("user: ${MY_USER}\n")
        assert load_config(str(cfg)) == {"user": "alice"}

    def test_env_interpolation_falls_back_to_default(self, tmp_path, monkeypatch):
        monkeypatch.delenv("MISSING_VAR", raising=False)
        cfg = tmp_path / "c.yaml"
        cfg.write_text("region: ${MISSING_VAR:-eu}\n")
        assert load_config(str(cfg)) == {"region": "eu"}

    def test_env_interpolation_missing_becomes_empty(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ABSENT_VAR", raising=False)
        cfg = tmp_path / "c.yaml"
        cfg.write_text("token: ${ABSENT_VAR}\n")
        assert load_config(str(cfg)) == {"token": ""}

    def test_env_interpolation_is_recursive(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PW", "s3cret")
        cfg = tmp_path / "c.yaml"
        cfg.write_text("configuration:\n  gasag:\n    password: ${PW}\n")
        assert load_config(str(cfg))["configuration"]["gasag"]["password"] == "s3cret"
