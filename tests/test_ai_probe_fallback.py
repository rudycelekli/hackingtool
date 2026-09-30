from hackingtool import ai_recommend, config


def test_auto_probe_uses_the_same_local_fallback_as_ask(monkeypatch):
    monkeypatch.setattr(config, "ai_provider", lambda: "auto")
    monkeypatch.setattr(config, "ai_base_url", lambda: "https://fixture.invalid/v1")
    monkeypatch.setattr(config, "ai_key", lambda: "test-key")
    monkeypatch.setattr(ai_recommend, "_probe_byo", lambda: (False, "remote unavailable"))
    monkeypatch.setattr(ai_recommend, "_probe_ollama", lambda: (True, "local connected"))
    ok, detail = ai_recommend.test_connection()
    assert ok
    assert "local connected" in detail
    assert "remote unavailable" in detail


def test_explicit_remote_provider_does_not_probe_local(monkeypatch):
    monkeypatch.setattr(config, "ai_provider", lambda: "openai-compat")
    monkeypatch.setattr(ai_recommend, "_probe_byo", lambda: (False, "remote unavailable"))
    def unexpected():
        raise AssertionError("explicit remote provider must not fall back")
    monkeypatch.setattr(ai_recommend, "_probe_ollama", unexpected)
    assert ai_recommend.test_connection() == (False, "remote unavailable")


def test_auto_probe_reports_both_failures(monkeypatch):
    monkeypatch.setattr(config, "ai_provider", lambda: "auto")
    monkeypatch.setattr(config, "ai_base_url", lambda: "https://fixture.invalid/v1")
    monkeypatch.setattr(config, "ai_key", lambda: "test-key")
    monkeypatch.setattr(ai_recommend, "_probe_byo", lambda: (False, "remote unavailable"))
    monkeypatch.setattr(ai_recommend, "_probe_ollama", lambda: (False, "local unavailable"))
    ok, detail = ai_recommend.test_connection()
    assert not ok
    assert "remote unavailable" in detail and "local unavailable" in detail
