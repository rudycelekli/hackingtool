import io
import json
from pathlib import Path
import pytest
from hackingtool import config, engagement
from hackingtool.findings import Finding, save_findings

@pytest.mark.parametrize("kind", ["config", "engagement", "findings"])
def test_json_save_failure_preserves_previous_document(tmp_path, monkeypatch, kind):
    monkeypatch.setattr(engagement, "ENGAGEMENTS_ROOT", tmp_path)
    monkeypatch.setattr(config, "USER_CONFIG_FILE", tmp_path / "config.json")
    if kind == "config":
        target = config.USER_CONFIG_FILE
        save = lambda: config.save({"changed": True})
    elif kind == "engagement":
        e = engagement.create("saved", ["example.test"])
        target = e.workspace / "engagement.json"
        e.runs.append({"findings": 1})
        save = e.save
    else:
        target = tmp_path / "findings.json"
        f = Finding("service", "example.test", "name", "info", "httpx", {}, "", "T")
        save = lambda: save_findings(target, [f])
    target.write_text('{"previous": true}')
    before = target.read_bytes()
    target.chmod(0o640)
    real_open = io.open
    class FailingWriter:
        def __init__(self, fh): self.fh = fh
        def __enter__(self): return self
        def __exit__(self, *args): self.fh.close()
        def write(self, text):
            self.fh.write(text[:8]); self.fh.flush()
            raise OSError("simulated disk write failure")
        def __getattr__(self, name): return getattr(self.fh, name)
    def open_with_failure(path, mode='r', *args, **kwargs):
        fh = real_open(path, mode, *args, **kwargs)
        return FailingWriter(fh) if mode == "w" else fh
    monkeypatch.setattr(io, "open", open_with_failure)
    with pytest.raises(OSError, match="simulated"):
        save()
    assert target.read_bytes() == before
    assert list(target.parent.glob(f".{target.name}.*.tmp")) == []
    monkeypatch.setattr(io, "open", real_open)
    save()
    assert json.loads(target.read_text())
    assert target.stat().st_mode & 0o777 == 0o640


def test_serialization_failure_does_not_touch_config(tmp_path, monkeypatch):
    target = tmp_path / "config.json"
    monkeypatch.setattr(config, "USER_CONFIG_FILE", target)
    target.write_text('{"previous": true}')
    with pytest.raises(TypeError): config.save({"bad": object()})
    assert json.loads(target.read_text()) == {"previous": True}


def test_replace_failure_preserves_previous_config_and_cleans_stage(tmp_path, monkeypatch):
    target = tmp_path / "config.json"
    target.write_text('{"previous": true}')
    monkeypatch.setattr(config, "USER_CONFIG_FILE", target)
    def fail_replace(self, destination):
        raise OSError("simulated replacement failure")
    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="replacement"):
        config.save({"changed": True})
    assert json.loads(target.read_text()) == {"previous": True}
    assert list(tmp_path.glob(".config.json.*.tmp")) == []
