import json

import pytest

from hackingtool import ai_recommend, config


class Response:
    def __init__(self, value):
        self.value = value
    def __enter__(self): return self
    def __exit__(self, *_args): pass
    def read(self): return json.dumps(self.value).encode()


@pytest.fixture(autouse=True)
def transport(monkeypatch):
    monkeypatch.setattr(config, "ai_base_url", lambda: "https://fixture.invalid/v1")
    monkeypatch.setattr(config, "ai_key", lambda: "test-key")
    monkeypatch.setattr(config, "ai_model", lambda: "fixture-model")


@pytest.mark.parametrize("value", [None, [], {"choices": None}, {"choices": [None]},
    {"choices": [{"message": None}]}, {"choices": [{"message": {"content": []}}]},
    {"choices": [{"message": {"content": ""}}]}])
def test_invalid_completion_is_unavailable_in_transport_and_probe(monkeypatch, value):
    monkeypatch.setattr(ai_recommend.urllib.request, "urlopen", lambda *_args, **_kwargs: Response(value))
    assert ai_recommend._byo_key("fixture") is None
    assert ai_recommend._probe_byo()[0] is False


@pytest.mark.parametrize("content", [None, True, [], {}, 42, "", "   "])
def test_invalid_local_model_text_is_unavailable(monkeypatch, content):
    monkeypatch.setattr(ai_recommend.urllib.request, "urlopen", lambda *_args, **_kwargs: Response({"response": content}))
    assert ai_recommend._ollama("fixture") is None
    assert ai_recommend._probe_ollama()[0] is False


def test_valid_text_remains_available(monkeypatch):
    monkeypatch.setattr(ai_recommend.urllib.request, "urlopen", lambda *_args, **_kwargs: Response({"choices": [{"message": {"content": "connected"}}]}))
    assert ai_recommend._byo_key("fixture") == "connected"
    assert ai_recommend._probe_byo()[0] is True
