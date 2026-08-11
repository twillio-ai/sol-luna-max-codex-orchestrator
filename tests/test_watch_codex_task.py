from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHER = ROOT / "scripts" / "watch-codex-task.py"


def event(kind: str) -> str:
    return json.dumps({"type": "event_msg", "payload": {"type": kind}}) + "\n"


class WatchCodexTaskTests(unittest.TestCase):
    def run_watcher(self, session: Path, *extra: str) -> subprocess.Popen[str]:
        return subprocess.Popen(
            [
                sys.executable,
                str(WATCHER),
                str(session),
                "--poll-interval",
                "0.05",
                *extra,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_historical_completion_is_ignored_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "session.jsonl"
            session.write_text(event("task_complete"), encoding="utf-8")

            proc = self.run_watcher(session, "--timeout", "0.25")
            stdout, stderr = proc.communicate(timeout=2)

            self.assertEqual(proc.returncode, 124)
            self.assertEqual(stdout, "")
            self.assertIn("timed out", stderr.lower())

    def test_new_completion_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "session.jsonl"
            session.write_text(event("task_started"), encoding="utf-8")

            proc = self.run_watcher(session, "--timeout", "2")
            time.sleep(0.15)
            with session.open("a", encoding="utf-8") as handle:
                handle.write(event("agent_reasoning"))
                handle.write(event("task_complete"))
                handle.flush()

            stdout, stderr = proc.communicate(timeout=3)

            self.assertEqual(proc.returncode, 0, stderr)
            marker = json.loads(stdout)
            self.assertEqual(marker["event"], "EXECUTOR_TASK_COMPLETE")
            self.assertEqual(Path(marker["session_file"]), session.resolve())
            self.assertIn("observed_at", marker)

    def test_partial_json_line_is_buffered_until_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "session.jsonl"
            session.write_text("", encoding="utf-8")

            proc = self.run_watcher(session, "--timeout", "2")
            time.sleep(0.15)
            payload = event("task_complete")
            split = len(payload) // 2
            with session.open("a", encoding="utf-8") as handle:
                handle.write(payload[:split])
                handle.flush()
            time.sleep(0.1)
            with session.open("a", encoding="utf-8") as handle:
                handle.write(payload[split:])
                handle.flush()

            stdout, stderr = proc.communicate(timeout=3)

            self.assertEqual(proc.returncode, 0, stderr)
            self.assertEqual(json.loads(stdout)["event"], "EXECUTOR_TASK_COMPLETE")

    def test_truncation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "session.jsonl"
            session.write_text(event("task_started") * 20, encoding="utf-8")

            proc = self.run_watcher(session, "--timeout", "2")
            time.sleep(0.15)
            session.write_text("", encoding="utf-8")

            stdout, stderr = proc.communicate(timeout=3)

            self.assertEqual(proc.returncode, 2)
            self.assertEqual(stdout, "")
            self.assertIn("truncated", stderr.lower())

    def test_from_start_can_observe_existing_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "session.jsonl"
            session.write_text(event("task_complete"), encoding="utf-8")

            proc = self.run_watcher(session, "--timeout", "1", "--from-start")
            stdout, stderr = proc.communicate(timeout=2)

            self.assertEqual(proc.returncode, 0, stderr)
            self.assertEqual(json.loads(stdout)["event"], "EXECUTOR_TASK_COMPLETE")


if __name__ == "__main__":
    unittest.main()
