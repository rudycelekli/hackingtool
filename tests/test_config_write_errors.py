import os
from pathlib import Path

from hackingtool import config


def test_config_save_error_returns_failure_without_claiming_success(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text('{"theme":"cyan"}')
    monkeypatch.setattr(config, "USER_CONFIG_FILE", path)
    def fail(_cfg):
        raise OSError("disk full")
    monkeypatch.setattr(config, "save", fail)
    ok, message = config.set_value("theme", "blue")
    assert not ok
    assert "disk full" in message
    assert path.read_text() == '{"theme":"cyan"}'


def test_key_file_read_failure_preserves_live_key(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    monkeypatch.setattr(config, "USER_CONFIG_FILE", path)
    env = tmp_path / ".env"
    env.write_bytes(b"\xff")
    monkeypatch.setenv("HACKINGTOOL_AI_KEY", "existing-key")
    ok, message = config.set_ai_key("replacement-key")
    assert not ok
    assert "replacement-key" not in message
    assert config.ai_key() == "existing-key"
    assert env.read_bytes() == b"\xff"


def test_key_write_error_does_not_update_process_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "USER_CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setenv("HACKINGTOOL_AI_KEY", "existing-key")
    def fail(self, *_args, **_kwargs):
        raise PermissionError("denied")
    monkeypatch.setattr(Path, "write_text", fail)
    ok, message = config.set_ai_key("replacement-key")
    assert not ok
    assert "PermissionError" in message
    assert os.environ["HACKINGTOOL_AI_KEY"] == "existing-key"
