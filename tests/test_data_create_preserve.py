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
