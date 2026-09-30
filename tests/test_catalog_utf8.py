import os
from pathlib import Path
import subprocess
import sys


def test_catalog_loads_utf8_under_ascii_locale(tmp_path):
    catalog = tmp_path / "catalog"
    catalog.mkdir()
    (catalog / "demo.yaml").write_text(
        "category: {title: 'Référence', icon: '📚'}\ntools: [{title: 'Évidence', kind: reference}]\n",
        encoding="utf-8")
    script = """
import sys
from pathlib import Path
from hackingtool import registry
assert sys.flags.utf8_mode == 0
reg = registry.load(Path(sys.argv[1]))
assert reg.categories[0].title.encode('utf-8') == bytes.fromhex('52c3a966c3a972656e6365')
assert reg.categories[0].tools[0].TITLE.encode('utf-8') == bytes.fromhex('c389766964656e6365')
print('catalog loaded')
"""
    env = dict(os.environ, LC_ALL="C", LANG="C", PYTHONUTF8="0",
               PYTHONCOERCECLOCALE="0", HOME=str(tmp_path),
               PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    result = subprocess.run([sys.executable, "-c", script, str(catalog)],
                            env=env, capture_output=True)
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert result.stdout == b"catalog loaded\n"

def test_first_run_config_and_key_updates_use_utf8_under_ascii_locale(tmp_path):
    script = """
from hackingtool import config, constants, registry
config.ensure_user_files()
assert registry.load().categories
assert config.set_ai_key('fixture-key')[0]
text = (constants.USER_CONFIG_DIR / '.env').read_text(encoding='utf-8')
assert '# hackingtool' in text and 'HACKINGTOOL_AI_KEY=fixture-key' in text
assert config.ai_key() == 'fixture-key'
print('config and catalog initialized')
"""
    env = dict(os.environ, LC_ALL="C", LANG="C", PYTHONUTF8="0",
               PYTHONCOERCECLOCALE="0", HOME=str(tmp_path),
               PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    result = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True)
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert result.stdout == b"config and catalog initialized\n"


def test_utf8_user_config_keeps_theme_and_paths_in_ascii_locale(tmp_path):
    directory = tmp_path / '.hackingtool'
    directory.mkdir()
    (directory / 'config.json').write_text(
        '{"theme":"cyan","tools_dir":"/tmp/Référence"}', encoding='utf-8')
    script = """
from hackingtool import config, constants
assert constants._configured_theme() == 'cyan'
assert config.load()['tools_dir'].encode('utf-8') == bytes.fromhex('2f746d702f52c3a966c3a972656e6365')
print('settings loaded')
"""
    env = dict(os.environ, LC_ALL="C", LANG="C", PYTHONUTF8="0",
               PYTHONCOERCECLOCALE="0", HOME=str(tmp_path),
               PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    result = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True)
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert result.stdout == b"settings loaded\n"
