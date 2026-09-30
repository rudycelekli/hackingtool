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

def test_empty_previous_handoff_skips_dependents_but_runs_independent_step(tmp_path, monkeypatch):
    steps = [step("subfinder", parser="subfinder", output="raw/subfinder.txt"), step(input="previous"), step("nuclei", input="targets", parser="nuclei", output="raw/nuclei.jsonl")]
    e = setup_pipeline(tmp_path, monkeypatch, steps)
    calls = []
    def run(cmd, **kwargs):
        calls.append(cmd[0]); return subprocess.CompletedProcess(cmd, 0, "", "")
    monkeypatch.setattr(orchestrator.subprocess, "run", run)
    assert orchestrator.run_pipeline(e) == []
    assert calls == ["subfinder", "nuclei"]
    assert "no previous" in e.log_file.read_text()
