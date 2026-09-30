import subprocess

import pytest

from hackingtool import session


@pytest.mark.parametrize("has_session", [True, False])
def test_failed_window_creation_is_reported_and_never_sends_input(monkeypatch, has_session):
    calls = []
    monkeypatch.setattr(session, "_unique_label", lambda value: value)
    monkeypatch.setattr(session, "_has_session", lambda: has_session)
    def run(args, capture=False):
        calls.append(args)
        return subprocess.CompletedProcess(args, 1, "", "cannot create window")
    monkeypatch.setattr(session, "_run", run)
    with pytest.raises(RuntimeError, match="cannot create window"):
        session.run("fixture", "/missing", command="", banner="fixture")
    assert len(calls) == 1
    assert calls[0][0] in {"new-session", "new-window"}


def test_failed_command_delivery_is_not_reported_successful(monkeypatch):
    monkeypatch.setattr(session, "_unique_label", lambda value: value)
    monkeypatch.setattr(session, "_has_session", lambda: True)
    def run(args, capture=False):
        return subprocess.CompletedProcess(args, 0 if args[0] == "new-window" else 1, "", "window disappeared")
    monkeypatch.setattr(session, "_run", run)
    with pytest.raises(RuntimeError, match="window disappeared"):
        session.run("fixture", "/fixture", command="fixture")


def test_console_reports_creation_failure_without_a_started_message(monkeypatch):
    from types import SimpleNamespace
    from hackingtool import cli, prompt, repl
    tool = SimpleNamespace(TITLE="Fixture", _get_tool_dir=lambda: "/fixture")
    messages = []
    monkeypatch.setattr(session, "enabled", lambda: True)
    monkeypatch.setattr(prompt, "_catalog", lambda: ({"Fixture": tool}, {}))
    monkeypatch.setattr(repl, "_resolve", lambda *_args: tool)
    monkeypatch.setattr(prompt, "_usage_banner", lambda _tool: "fixture")
    monkeypatch.setattr(cli.console, "print", messages.append)
    def fail(*_args, **_kwargs):
        raise session.SessionError("cannot create window")
    monkeypatch.setattr(session, "run", fail)
    assert prompt._run_command("fixture &", prompt.PromptCtx("home")) is prompt.CONTINUE
    assert any("cannot create window" in message for message in messages)
    assert not any("started" in message for message in messages)
