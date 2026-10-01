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


def test_failed_probe_dispatch_does_not_block_a_second_test(monkeypatch):
    import asyncio

    dispatch_failed = threading.Event()
    retried = threading.Event()
    calls = []
    original_dispatch = asyncio.BaseEventLoop.call_soon_threadsafe

    def dispatch(loop, callback, *args, **kwargs):
        if getattr(callback, '__name__', '') == 'finish' and not dispatch_failed.is_set():
            dispatch_failed.set()
            raise ValueError('local dispatch fixture failure')
        return original_dispatch(loop, callback, *args, **kwargs)

    def probe():
        calls.append('probe')
        if len(calls) == 2:
            retried.set()
        return True, 'connected'

    monkeypatch.setattr(config, 'describe', lambda: [('theme', 'magenta', True)])
    monkeypatch.setattr(ai_recommend, 'test_connection', probe)
    monkeypatch.setattr(asyncio.BaseEventLoop, 'call_soon_threadsafe', dispatch)
    with create_pipe_input() as inputs, create_app_session(input=inputs, output=DummyOutput()):
        def keys():
            time.sleep(0.05)
            inputs.send_text('t')
            assert dispatch_failed.wait(timeout=1)
            # Let the failed worker finish before submitting the next key.
            time.sleep(0.05)
            inputs.send_text('t')
            retried.wait(timeout=1)
            inputs.send_text('\x03')
        feeder = threading.Thread(target=keys, daemon=True)
        feeder.start()
        config_ui.open_editor()
        feeder.join(timeout=2)
    assert len(calls) == 2, 'A failed dispatch must release the in-flight probe guard'
