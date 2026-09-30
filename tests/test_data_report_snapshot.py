from hackingtool import ai_report, engagement
from hackingtool.findings import Finding, save_findings
from hackingtool.report import render_report

def test_draft_appendix_uses_same_snapshot_as_model(tmp_path, monkeypatch):
    monkeypatch.setattr(engagement, "ENGAGEMENTS_ROOT", tmp_path)
    e = engagement.create("snapshot", ["example.test"])
    first = Finding("service", "https://example.test", "First snapshot", "info", "httpx", {}, "", "T")
    second = Finding("service", "https://example.test", "Later snapshot", "info", "httpx", {}, "", "T")
    save_findings(e.findings_file, [first])
    def ask(prompt):
        assert "First snapshot" in prompt
        save_findings(e.findings_file, [second])
        return "Observed the first snapshot."
    monkeypatch.setattr(ai_report, "ask", ask)
    result = ai_report.draft_report(e).read_text()
    assert "First snapshot" in result
    assert "Later snapshot" not in result
    assert "Later snapshot" in render_report(e)
