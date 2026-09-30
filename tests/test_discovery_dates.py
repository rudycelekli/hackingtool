from datetime import datetime, timezone
import pytest
from hackingtool import discover

NOW = datetime(2026, 7, 26, tzinfo=timezone.utc)

def repo(**overrides):
    data = dict(full_name="example/tool", description="Useful maintained reference software",
                url="https://github.com/example/tool", stars=1000, forks=10,
                pushed_at="2026-06-01T00:00:00Z", created_at="2020-01-01T00:00:00Z",
                archived=False, fork=False, license="MIT", language="Python", topics=[],
                owner="example", owner_type="User")
    data.update(overrides)
    return discover.Repo(**data)

@pytest.mark.parametrize("stamp", ["2026-06-01T00:00:00", "2026-06-01"])
def test_naive_cached_dates_rank_like_utc(stamp):
    cached = repo(pushed_at=stamp, created_at="2020-01-01T00:00:00")
    canonical = repo()
    discover._rank([cached, canonical], now=NOW)
    assert cached.score == canonical.score
    assert cached.why == canonical.why

@pytest.mark.parametrize("stamp", ["", "not-a-date", None, 123, []])
def test_unknown_activity_is_not_advertised_as_active(stamp):
    unknown = repo(pushed_at=stamp, created_at=stamp)
    discover._rank([unknown], now=NOW)
    assert "active" not in unknown.why
    assert "brand new" not in unknown.why
    assert "activity unknown" in unknown.why

def test_find_returns_results_from_cache_with_naive_dates(monkeypatch):
    item = dict(full_name="example/tool", description="A useful maintained reference",
                html_url="https://github.com/example/tool", stargazers_count=1000,
                pushed_at="2026-06-01T00:00:00", created_at="2020-01-01T00:00:00")
    monkeypatch.setattr(discover, "_cache_get", lambda query: [item])
    monkeypatch.setattr(discover, "_fetch", lambda url: pytest.fail("no network expected"))
    assert discover.find("forensic analysis").repos
