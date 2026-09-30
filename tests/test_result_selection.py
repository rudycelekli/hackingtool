from types import SimpleNamespace
import pytest
from hackingtool import cli

@pytest.mark.parametrize("index", [98, 99, 100])
def test_large_result_list_can_open_every_index(index, monkeypatch):
    opened = []
    matches = [(SimpleNamespace(show_options=lambda i=i: opened.append(i)), "Test")
               for i in range(1, 101)]
    monkeypatch.setattr(cli, "ask", lambda *a, **k: str(index))
    cli._pick_tool(matches)
    assert opened == [index]

@pytest.mark.parametrize("answer", ["b", "back", "99", "", "0", "101"])
def test_return_and_invalid_choices_do_not_open_tools(answer, monkeypatch):
    opened = []
    matches = [(SimpleNamespace(show_options=lambda: opened.append(True)), "Test")]
    monkeypatch.setattr(cli, "ask", lambda *a, **k: answer)
    cli._pick_tool(matches)
    assert not opened

def test_result_table_displays_unambiguous_back_key(monkeypatch):
    rendered = []
    monkeypatch.setattr(cli.console, "print", lambda table: rendered.append(table))
    cli._tool_table([], "Test")
    assert rendered[0].columns[0]._cells[-1] == "b"

def test_search_displays_same_back_key(monkeypatch):
    rendered = []
    tool = SimpleNamespace(TITLE="Demo", DESCRIPTION="Description", TAGS=[])
    monkeypatch.setattr(cli, "_collect_all_tools", lambda: [(tool, "Test")])
    monkeypatch.setattr(cli.console, "print", lambda table: rendered.append(table))
    monkeypatch.setattr(cli, "_pick_tool", lambda matches: None)
    cli.search_tools("Demo")
    assert rendered[0].columns[0]._cells[-1] == "b"
