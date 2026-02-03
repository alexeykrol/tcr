#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LatestFile:
    path: Path
    mtime: float
    size: int


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone().isoformat(timespec="seconds")


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).astimezone().isoformat(timespec="seconds")


def _find_latest(md_dir: Path) -> LatestFile | None:
    latest: LatestFile | None = None
    for p in md_dir.glob("*.md"):
        try:
            st = p.stat()
        except FileNotFoundError:
            continue
        item = LatestFile(path=p, mtime=st.st_mtime, size=st.st_size)
        if latest is None or item.mtime > latest.mtime:
            latest = item
    return latest


def _read_state(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text("utf-8"))
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def _write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", "utf-8")
    os.replace(tmp, path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor translation progress by file mtimes.")
    parser.add_argument("--dir", default="chapters_en_us", help="Directory with translated chapters.")
    parser.add_argument("--stall-min", type=int, default=20, help="Alert if no changes for N minutes.")
    parser.add_argument(
        "--state-file",
        default="memory-bank/translation-monitor.json",
        help="Where to store last-seen state.",
    )
    args = parser.parse_args()

    md_dir = Path(args.dir)
    state_path = Path(args.state_file)

    latest = _find_latest(md_dir) if md_dir.exists() else None
    state = _read_state(state_path)

    now = datetime.now(tz=timezone.utc).timestamp()
    stall_seconds = max(1, int(args.stall_min) * 60)

    if latest is None:
        print("# Translation monitor: ALERT\n")
        print(f"- Time: `{_now_iso()}`")
        print(f"- Reason: no files found in `{md_dir}`")
        state.update({"last_run": _now_iso(), "status": "alert", "reason": "no_files"})
        _write_state(state_path, state)
        return 2

    age_seconds = max(0.0, now - latest.mtime)
    age_min = age_seconds / 60.0

    prev_path = state.get("latest_path")
    prev_mtime = float(state.get("latest_mtime", 0) or 0)
    progressed = (prev_path != str(latest.path)) or (latest.mtime > prev_mtime + 1e-6)

    if age_seconds >= stall_seconds:
        print("# Translation monitor: ALERT\n")
        print(f"- Time: `{_now_iso()}`")
        print(f"- Latest file: `{latest.path}`")
        print(f"- Latest update: `{_iso(latest.mtime)}`")
        print(f"- Age: `{age_min:.1f} min` (threshold `{args.stall_min} min`)")
        if not progressed:
            print("- Note: no progress since last check.")
        state.update(
            {
                "last_run": _now_iso(),
                "status": "alert",
                "reason": "stall",
                "latest_path": str(latest.path),
                "latest_mtime": latest.mtime,
                "latest_size": latest.size,
            }
        )
        _write_state(state_path, state)
        return 2

    print("# Translation monitor: OK\n")
    print(f"- Time: `{_now_iso()}`")
    print(f"- Latest file: `{latest.path}`")
    print(f"- Latest update: `{_iso(latest.mtime)}`")
    print(f"- Age: `{age_min:.1f} min` (threshold `{args.stall_min} min`)")
    print(f"- Progress since last check: `{bool(progressed)}`")

    state.update(
        {
            "last_run": _now_iso(),
            "status": "ok",
            "latest_path": str(latest.path),
            "latest_mtime": latest.mtime,
            "latest_size": latest.size,
        }
    )
    _write_state(state_path, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

