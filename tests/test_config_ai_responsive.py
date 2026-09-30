import threading
import time

from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from hackingtool import ai_recommend, config, config_ui


def test_modal_can_exit_while_connection_probe_is_still_pending(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    monkeypatch.setattr(config, 'describe', lambda: [('theme', 'magenta', True)])
    def probe():
        started.set()
        try:
            release.wait(timeout=2)
            return True, 'connected'
        finally:
            finished.set()
    monkeypatch.setattr(ai_recommend, 'test_connection', probe)
    with create_pipe_input() as inputs, create_app_session(input=inputs, output=DummyOutput()):
        def keys():
            time.sleep(0.05)
            inputs.send_text('t')
            assert started.wait(timeout=1)
            inputs.send_text('\x03')  # Ctrl-C closes the modal, even during a probe.
            # Ensure the old blocking implementation eventually exits so the
            # regression fails cleanly instead of leaving a hung test process.
            release.wait(timeout=0.6)
            release.set()
        feeder = threading.Thread(target=keys, daemon=True)
        feeder.start()
        config_ui.open_editor()
        was_pending_on_exit = not finished.is_set()
        release.set()
        feeder.join(timeout=2)
        assert finished.wait(timeout=2)
    assert was_pending_on_exit, 'A network probe must not block the settings event loop'
