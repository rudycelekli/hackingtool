import json
import pytest
from hackingtool.findings import parse_httpx, parse_nuclei

@pytest.mark.parametrize("bad", [None, [], 5, {"url": ["bad"]}, {"url": {"bad": 1}}])
def test_httpx_skips_invalid_record_and_keeps_later_output(bad):
    raw = json.dumps(bad) + '\n' + json.dumps({"url": "https://example.test", "title": "OK"})
    findings, urls = parse_httpx(raw, "T")
    assert urls == ["https://example.test"]
    assert [f.name for f in findings] == ["OK"]

@pytest.mark.parametrize("bad", [None, [], 5, {"info": "bad"}, {"host": ["bad"]}, {"info": {"severity": []}}])
def test_nuclei_skips_invalid_record_and_keeps_later_output(bad):
    good = {"host": "https://example.test", "template-id": "test", "info": {"name": "OK", "severity": "high"}}
    findings, forwarded = parse_nuclei(json.dumps(bad) + '\n' + json.dumps(good), "T")
    assert [f.name for f in findings] == ["OK"]
    assert forwarded == []

def test_httpx_nontext_title_falls_back_to_url():
    findings, _ = parse_httpx('{"url":"https://example.test","title":["bad"]}', "T")
    assert findings[0].name == "https://example.test"
