import pytest
from hackingtool import prompt

@pytest.mark.parametrize("raw", ["/", "/   ", "/\t", "  /  "])
@pytest.mark.parametrize("mode", ["home", "tool"])
def test_empty_slash_returns_to_prompt(raw, mode, monkeypatch):
    shown = []
    monkeypatch.setattr("hackingtool.cli.show_help", lambda: shown.append(True))
    assert prompt.dispatch(raw, prompt.PromptCtx(mode)) is prompt.CONTINUE
    assert shown == [True]
