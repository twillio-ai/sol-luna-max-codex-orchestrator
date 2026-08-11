#!/usr/bin/env python3
"""Wait for a new Codex task_complete event without invoking an LLM.

This is the dependency-free portable fallback for environments where the native
Windows PowerShell watcher is not used. It watches one explicit JSONL session file
and starts at the current EOF by default so historical task_complete events cannot
satisfy a new wait.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

EXIT_INVALID = 2
EXIT_TIMEOUT = 124


def is_task_complete(line: bytes) -> bool:
    """Return True only for one structured Codex task_complete event."""
    if not line.strip():
        return False
    try:
        record = json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(record, dict)
        and record.get("type") == "event_msg"
        and isinstance(record.get("payload"), dict)
        and record["payload"].get("type") == "task_complete"
    )


def emit_terminal_marker(path: Path) -> None:
    print(
        json.dumps(
            {
                "event": "EXECUTOR_TASK_COMPLETE",
                "session_file": str(path),
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
            separators=(",", ":"),
        ),
        flush=True,
    )


def watch(
    path: Path,
    *,
    timeout: float,
    poll_interval: float,
    from_start: bool,
) -> int:
    path = path.expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError("session file must be one regular file")

    offset = 0 if from_start else path.stat().st_size
    buffer = b""
    deadline = time.monotonic() + timeout if timeout > 0 else None

    while True:
        size = path.stat().st_size
        if size < offset:
            raise RuntimeError(
                "session file was truncated or replaced while waiting; "
                "refusing ambiguous completion state"
            )

        if size > offset:
            with path.open("rb") as handle:
                handle.seek(offset)
                chunk = handle.read(size - offset)
            offset += len(chunk)
            buffer += chunk

            parts = buffer.split(b"\n")
            buffer = parts.pop()
            for line in parts:
                if is_task_complete(line.rstrip(b"\r")):
                    emit_terminal_marker(path)
                    return 0

        if deadline is not None and time.monotonic() >= deadline:
            print(
                "timed out waiting for a new task_complete event",
                file=sys.stderr,
            )
            return EXIT_TIMEOUT

        time.sleep(poll_interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Wait for a new Codex JSONL task_complete event without an LLM heartbeat."
        )
    )
    parser.add_argument("session_file", type=Path)
    parser.add_argument(
        "--timeout",
        type=float,
        default=0.0,
        help="seconds before returning exit 124; 0 means no timeout",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.5,
        help="local filesystem poll interval in seconds (default: 0.5)",
    )
    parser.add_argument(
        "--from-start",
        action="store_true",
        help="scan existing records too; default is to start at current EOF",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.timeout < 0:
        parser.error("--timeout must be >= 0")
    if args.poll_interval <= 0:
        parser.error("--poll-interval must be > 0")

    try:
        return watch(
            args.session_file,
            timeout=args.timeout,
            poll_interval=args.poll_interval,
            from_start=args.from_start,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
