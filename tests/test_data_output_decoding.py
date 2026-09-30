import subprocess
import sys
from hackingtool import engagement, orchestrator
from hackingtool.findings import load_findings

def setup_pipeline(tmp_path, monkeypatch, steps):
    monkeypatch.setattr(engagement, "ENGAGEMENTS_ROOT", tmp_path)
    monkeypatch.setattr(orchestrator, "load_pipeline", lambda _: {"steps": steps})
    monkeypatch.setattr(orchestrator.shutil, "which", lambda _: "/local/fixture")
    return engagement.create("local", ["example.test"])

def step(tool="httpx", input="targets", output="raw/httpx.jsonl", parser="httpx", args=None):
    return {"tool": tool, "input": input, "output": output, "parser": parser, "args": args or []}

def test_non_utf8_stdout_preserves_valid_jsonl_results(tmp_path, monkeypatch):
    code = 'import sys; sys.stdout.buffer.write(b\'\\xffdiagnostic\\n{"url":"https://example.test","title":"OK"}\\n\'); sys.stderr.buffer.write(b\'\\xffnote\')'
    e = setup_pipeline(tmp_path, monkeypatch, [step(tool=sys.executable, args=["-c", code])])
    result = orchestrator.run_pipeline(e)
    assert [f.name for f in result] == ["OK"]
    assert "\ufffd" in (e.raw_dir / "httpx.jsonl").read_text()
