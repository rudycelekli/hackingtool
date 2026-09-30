"""Atomic replacement for persisted JSON documents (stdlib only)."""
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any


def write_json(path: Path, value: Any, *, sort_keys: bool = False) -> None:
    """Leave the previous document intact if serialization or staging fails."""
    text = json.dumps(value, indent=2, sort_keys=sort_keys)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    staged = Path(name)
    try:
        if path.exists():
            staged.chmod(stat.S_IMODE(path.stat().st_mode))
        with staged.open("w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        staged.replace(path)
    finally:
        staged.unlink(missing_ok=True)
