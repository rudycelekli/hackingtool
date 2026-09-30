"""Normalized findings schema + per-tool parsers. Stdlib only."""
import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Finding:
    kind: str          # subdomain | service | vulnerability
    target: str
    name: str
    severity: str      # info | low | medium | high | critical | unknown
    source_tool: str
    details: dict
    raw: str
    timestamp: str


def parse_subfinder(raw: str, ts: str) -> tuple[list[Finding], list[str]]:
    hosts = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    findings = [Finding("subdomain", h, h, "info", "subfinder", {}, h, ts) for h in hosts]
    return findings, hosts


def parse_httpx(raw: str, ts: str) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    urls: list[str] = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError:
            continue  # skip malformed line, keep going
        if not isinstance(obj, dict):
            continue
        url = obj.get("url") or obj.get("input") or ""
        if not isinstance(url, str) or not url:
            continue
        details = {
            "status_code": obj.get("status_code"),
            "title": obj.get("title"),
            "tech": obj.get("tech"),
            "webserver": obj.get("webserver"),
        }
        title = obj.get("title")
        name = title if isinstance(title, str) and title else url
        findings.append(Finding("service", url, name,
                                "info", "httpx", details, ln, ts))
        urls.append(url)
    return findings, urls


def parse_nuclei(raw: str, ts: str) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        info = obj.get("info") or {}
        if not isinstance(info, dict):
            continue
        target = obj.get("matched-at") or obj.get("host") or ""
        tid = obj.get("template-id", "")
        name = info.get("name") or tid
        severity = info.get("severity")
        if severity is None or severity == "":
            severity = "unknown"
        if (not isinstance(target, str) or not target
                or not isinstance(name, str) or not isinstance(severity, str)):
            continue
        details = {"template_id": tid, "matched_at": obj.get("matched-at"),
                   "type": obj.get("type")}
        findings.append(Finding("vulnerability", target, name,
                                severity, "nuclei",
                                details, ln, ts))
    return findings, []


PARSERS = {"subfinder": parse_subfinder, "httpx": parse_httpx, "nuclei": parse_nuclei}


def save_findings(path: Path, findings: list[Finding]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(f) for f in findings], indent=2))


def load_findings(path: Path) -> list[Finding]:
    if not path.exists():
        return []
    return [Finding(**d) for d in json.loads(path.read_text())]
