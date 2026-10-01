import pytest
from hackingtool import engagement

def test_duplicate_create_preserves_existing_engagement(tmp_path, monkeypatch):
    monkeypatch.setattr(engagement, "ENGAGEMENTS_ROOT", tmp_path)
    original = engagement.create("saved", ["example.test"], scope_out=["private.example.test"])
    original.add_run({"pipeline": "recon", "findings": 4})
    path = original.workspace / "engagement.json"
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        engagement.create("saved", ["other.test"])
    assert path.read_bytes() == before
    assert engagement.load("saved").runs == original.runs
    assert engagement.get_or_create("saved").created == original.created


def test_concurrent_creators_publish_exactly_one_complete_document(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    monkeypatch.setattr(engagement, "ENGAGEMENTS_ROOT", tmp_path)
    barrier = Barrier(2)
    now = engagement._now
    def synchronized_now():
        barrier.wait(timeout=5)
        return now()
    monkeypatch.setattr(engagement, "_now", synchronized_now)
    def create(target):
        try:
            return engagement.create("shared", [target])
        except FileExistsError:
            return None
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(create, ["first.test", "second.test"]))
    winners = [result for result in results if result is not None]
    assert len(winners) == 1
    assert engagement.load("shared") == winners[0]
    assert list((tmp_path / "shared").glob(".create-*")) == []


@pytest.mark.parametrize("failure", ["unsupported", "concurrent"])
def test_cli_reports_publication_failure_without_overwriting(tmp_path, monkeypatch, capsys, failure):
    import errno
    import sys
    from hackingtool import cli

    monkeypatch.setattr(engagement, "ENGAGEMENTS_ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["hackingtool", "--engagement", "shared"])
    link = engagement.os.link
    winner = None

    def failing_link(source, destination):
        nonlocal winner
        if failure == "unsupported":
            raise OSError(errno.ENOTSUP, "hard links unsupported")
        # A second process publishes a complete document after this caller's load.
        winner = b'{"name":"shared","created":"winner","targets":[],"runs":[]}'
        destination.write_bytes(winner)
        return link(source, destination)

    monkeypatch.setattr(engagement.os, "link", failing_link)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "Could not open engagement workspace" in output
    if failure == "unsupported":
        assert "hard links unsupported" in output
        assert not (tmp_path / "shared" / "engagement.json").exists()
    else:
        assert (tmp_path / "shared" / "engagement.json").read_bytes() == winner
    assert list((tmp_path / "shared").glob(".create-*")) == []
