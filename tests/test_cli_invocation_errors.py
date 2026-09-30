import pytest
from hackingtool import cli, config

@pytest.mark.parametrize("argv", [["--report"], ["--targets", "example.invalid"],
                                  ["--classic", "--report"], ["typo"], ["-z"],
                                  ["--classic", "typo"]])
def test_invalid_invocations_exit_nonzero_without_opening_menu(argv, monkeypatch):
    entered = []
    monkeypatch.setattr("sys.argv", ["hackingtool", *argv])
    monkeypatch.setattr(cli, "get_tools_dir", lambda: None)
    monkeypatch.setattr(config, "ensure_user_files", lambda: None)
    monkeypatch.setattr("hackingtool.repl._use_repl", lambda classic: False)
    monkeypatch.setattr(cli, "interact_menu", lambda: entered.append(True))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    assert not entered

def test_valid_headless_invocation_still_dispatches(monkeypatch):
    called = []
    monkeypatch.setattr("sys.argv", ["hackingtool", "--engagement", "test", "--report"])
    monkeypatch.setattr(cli, "_run_headless", lambda args: called.append(args))
    cli.main()
    assert called[0].engagement == "test" and called[0].report

def test_classic_without_headless_arguments_still_opens_menu(monkeypatch):
    entered = []
    monkeypatch.setattr("sys.argv", ["hackingtool", "--classic"])
    monkeypatch.setattr(cli, "get_tools_dir", lambda: None)
    monkeypatch.setattr(config, "ensure_user_files", lambda: None)
    monkeypatch.setattr("hackingtool.repl._use_repl", lambda classic: False)
    monkeypatch.setattr(cli, "interact_menu", lambda: entered.append(True))
    cli.main()
    assert entered == [True]
