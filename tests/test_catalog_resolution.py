from types import SimpleNamespace
import pytest
from hackingtool import cli, repl, prompt

@pytest.mark.parametrize("name,title", [("nmap", "Network Map (nmap)"),
    ("sqlmap", "Sqlmap tool"), ("hashcat", "hashcat (GPU hash cracker)"),
    ("john", "John the Ripper (jumbo)")])
def test_canonical_names_resolve_to_actual_catalog_tools(name, title):
    tools = {tool.TITLE: tool for tool, _ in cli._collect_all_tools()}
    assert repl._resolve(name, tools).TITLE == title

def test_exact_title_takes_priority_over_another_tool_alias():
    titled = SimpleNamespace(TITLE="demo", SYSTEM_PKGS={})
    aliased = SimpleNamespace(TITLE="Another", SYSTEM_PKGS={"which": "demo"})
    assert repl._resolve("demo", {"demo": titled, "Another": aliased}) is titled

def test_ambiguous_canonical_alias_does_not_select_arbitrarily():
    tools = {"First": SimpleNamespace(SYSTEM_PKGS={"which": "shared"}),
             "Second": SimpleNamespace(SYSTEM_PKGS={"which": "shared"})}
    assert repl._resolve("shared", tools) is None

@pytest.mark.parametrize("title", ["Network Map (nmap)", "John the Ripper",
                                   "John the Ripper (jumbo)"])
def test_inline_run_preserves_exact_multiword_title(title):
    assert prompt.dispatch("/run " + title, prompt.PromptCtx("home")) == prompt.Open("@" + title)

def test_inline_run_with_command_arguments_keeps_existing_tool_token_behavior():
    assert prompt.dispatch("/run nmap --help", prompt.PromptCtx("home")) == prompt.Open("@nmap")

@pytest.mark.parametrize("raw,title", [("/run @Network Map (nmap)", "Network Map (nmap)"),
    ("/open @john the ripper", "John the Ripper"), ("/run @nmap", "nmap")])
def test_inline_run_accepts_completion_mentions(raw, title):
    assert prompt.dispatch(raw, prompt.PromptCtx("home")) == prompt.Open("@" + title)
