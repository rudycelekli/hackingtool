import io
import os
from pathlib import Path
import pytest
import yaml
from hackingtool import discover

def repo():
    return discover.Repo(full_name="example/new", description="Reference software",
        url="https://github.com/example/new", stars=1, forks=0, pushed_at="",
        created_at="", archived=False, fork=False, license="", language="Python",
        topics=[], owner="example", owner_type="User")

@pytest.mark.parametrize("original", [b"tools: [\n", b"- previous-entry\n",
    b"tools: previous-entry\n", b"category: broken\ntools: []\n", b"\xff\xfe"])
def test_invalid_existing_catalog_is_preserved(original, tmp_path, monkeypatch):
    path = tmp_path / "found.yaml"
    path.write_bytes(original)
    monkeypatch.setattr(discover, "_found_path", lambda: path)
    assert discover.save_repo(repo(), ["web"]) is None
    assert path.read_bytes() == original

def test_failed_publication_preserves_previous_entries(tmp_path, monkeypatch):
    path = tmp_path / "found.yaml"
    original = "category: {title: Discovered tools}\ntools: [{title: Previous, project_url: previous}]\n"
    path.write_text(original)
    monkeypatch.setattr(discover, "_found_path", lambda: path)
    def fail_replace(*args):
        raise OSError("simulated publication failure")
    monkeypatch.setattr(os, "replace", fail_replace)
    assert discover.save_repo(repo(), ["web"]) is None
    assert path.read_text() == original
    assert list(tmp_path.iterdir()) == [path]

def test_read_failure_does_not_replace_existing_catalog(tmp_path, monkeypatch):
    path = tmp_path / "found.yaml"
    path.write_text("tools: []\n")
    monkeypatch.setattr(discover, "_found_path", lambda: path)
    original = path.read_bytes()
    def fail_read(*args, **kwargs):
        raise PermissionError("simulated read failure")
    monkeypatch.setattr(Path, "read_text", fail_read)
    assert discover.save_repo(repo(), ["web"]) is None
    assert path.read_bytes() == original

def test_valid_save_retains_previous_entry(tmp_path, monkeypatch):
    path = tmp_path / "found.yaml"
    path.write_text("category: {title: Discovered tools}\ntools: [{title: Previous, project_url: previous}]\n")
    monkeypatch.setattr(discover, "_found_path", lambda: path)
    assert discover.save_repo(repo(), ["web"]) == path
    data = yaml.safe_load(path.read_text())
    assert [item["title"] for item in data["tools"]] == ["Previous", "new (discovered)"]
    assert list(tmp_path.iterdir()) == [path]

def test_partial_write_failure_preserves_previous_catalog(tmp_path, monkeypatch):
    path = tmp_path / "found.yaml"
    original = "category: {title: Discovered tools}\ntools: [{title: Previous, project_url: previous}]\n"
    path.write_text(original)
    monkeypatch.setattr(discover, "_found_path", lambda: path)
    original_open = io.open
    class PartialWriter:
        def __init__(self, stream):
            self.stream = stream
        def __getattr__(self, name):
            return getattr(self.stream, name)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return self.stream.__exit__(*args)
        def write(self, text):
            self.stream.write(text[:5])
            self.stream.flush()
            raise OSError("simulated disk write failure")
    def failing_open(file, mode="r", *args, **kwargs):
        stream = original_open(file, mode, *args, **kwargs)
        return PartialWriter(stream) if "w" in mode else stream
    monkeypatch.setattr(io, "open", failing_open)
    assert discover.save_repo(repo(), ["web"]) is None
    assert path.read_text() == original
    assert list(tmp_path.iterdir()) == [path]
