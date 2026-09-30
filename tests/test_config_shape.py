import json

import pytest

from hackingtool import config, constants


@pytest.mark.parametrize("payload", [[], ["theme"], None, "text", 42, True])
def test_nonobject_config_falls_back_without_rewriting(tmp_path, monkeypatch, payload):
    path = tmp_path / "config.json"
    original = json.dumps(payload)
    path.write_text(original)
    monkeypatch.setattr(config, "USER_CONFIG_FILE", path)
    monkeypatch.setattr(constants, "USER_CONFIG_FILE", path)
    assert config.load() == constants.DEFAULT_CONFIG
    assert constants._configured_theme() == "magenta"
    assert path.read_text() == original


@pytest.mark.parametrize("theme", [[], {}, False, 42, None])
def test_wrong_theme_type_does_not_break_import_time_selection(tmp_path, monkeypatch, theme):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"theme": theme}))
    monkeypatch.setattr(constants, "USER_CONFIG_FILE", path)
    assert constants._configured_theme() == "magenta"


def test_invalid_encoding_is_a_read_only_defaults_fallback(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_bytes(b"\xff\xfe")
    monkeypatch.setattr(config, "USER_CONFIG_FILE", path)
    assert config.load() == constants.DEFAULT_CONFIG
    assert path.read_bytes() == b"\xff\xfe"
