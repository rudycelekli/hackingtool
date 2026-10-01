import subprocess
import sys
import pytest
from hackingtool import engagement, orchestrator
from hackingtool.findings import load_findings

def setup_pipeline(tmp_path, monkeypatch, steps):
    monkeypatch.setattr(engagement, "ENGAGEMENTS_ROOT", tmp_path)
    monkeypatch.setattr(orchestrator, "load_pipeline", lambda _: {"steps": steps})
    monkeypatch.setattr(orchestrator.shutil, "which", lambda _: "/local/fixture")
    return engagement.create("local", ["example.test"])

def step(tool="httpx", input="targets", output="raw/httpx.jsonl", parser="httpx", args=None):
    return {"tool": tool, "input": input, "output": output, "parser": parser, "args": args or []}

def test_timeout_preserves_partial_evidence_without_forwarding(tmp_path, monkeypatch):
    e = setup_pipeline(tmp_path, monkeypatch, [step()])
    raw = b'{"url":"https://example.test","title":"Partial evidence"}\n'
    def timed_out(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1, output=raw, stderr=b"unfinished")
    monkeypatch.setattr(orchestrator.subprocess, "run", timed_out)
    result = orchestrator.run_pipeline(e)
    assert len(result) == 1
    assert (e.raw_dir / "httpx.jsonl").read_bytes() == raw
    assert load_findings(e.findings_file)[0].name == "Partial evidence"
    assert "partial" in e.log_file.read_text().lower()


def test_real_local_timeout_retains_completed_json_record(tmp_path, monkeypatch):
    code = 'import sys, time; print(\'{"url":"https://example.test","title":"Completed record"}\', flush=True); time.sleep(10)'
    e = setup_pipeline(tmp_path, monkeypatch, [step(tool=sys.executable, args=["-c", code])])
    monkeypatch.setattr(orchestrator, "STEP_TIMEOUT", 0.3)
    result = orchestrator.run_pipeline(e)
    assert [f.name for f in result] == ["Completed record"]
    assert "Completed record" in (e.raw_dir / "httpx.jsonl").read_text()


def test_timeout_partial_discoveries_are_not_forwarded(tmp_path, monkeypatch):
    e = setup_pipeline(tmp_path, monkeypatch, [step(), step("nuclei", input="previous", parser="nuclei", output="raw/nuclei.jsonl")])
    received = []
    def run(cmd, **kwargs):
        if cmd[0] == "httpx":
            raise subprocess.TimeoutExpired(cmd, 1, output=b'{"url":"https://example.test"}\n{"unfinished":')
        received.append(kwargs["input"])
        return subprocess.CompletedProcess(cmd, 0, "", "")
    monkeypatch.setattr(orchestrator.subprocess, "run", run)
    result = orchestrator.run_pipeline(e)
    assert len(result) == 1
    # A dependency-aware runner may skip this consumer entirely. If invoked,
    # it must not receive incomplete-stage discoveries.
    assert not any(received)


@pytest.mark.parametrize('parser', ['subfinder', 'httpx', 'nuclei'])
def test_real_local_timeout_before_output_is_safe_for_every_parser(tmp_path, monkeypatch, parser):
    output = f'raw/{parser}.txt'
    e = setup_pipeline(tmp_path, monkeypatch, [step(
        tool=sys.executable, args=['-c', 'import time; time.sleep(5)'],
        output=output, parser=parser,
    )])
    monkeypatch.setattr(orchestrator, 'STEP_TIMEOUT', 0.05)
    assert orchestrator.run_pipeline(e) == []
    assert (e.workspace / output).read_bytes() == b''
    assert load_findings(e.findings_file) == []
