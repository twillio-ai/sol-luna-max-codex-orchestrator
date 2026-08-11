# Changelog

## 0.1.0 — 2026-08-12

Initial public reference implementation.

### Added

- GPT-5.6 Sol commander / GPT-5.6 Luna Max executor orchestration policy.
- Native Windows PowerShell watcher using `.NET FileSystemWatcher`.
- Dependency-free portable Python watcher.
- Start-at-EOF behavior to prevent historical `task_complete` events from satisfying a new wait.
- Fail-closed handling for truncated or replaced session state.
- Regression tests for historical completion, new completion, partial JSONL writes, truncation, and explicit from-start scanning.
- GitHub Actions validation on Python 3.11, 3.12, 3.13, plus Windows PowerShell parsing.
- Human-first README with explicit answer-engine-friendly project facts and FAQ.
- `llms.txt` project summary.
- Architecture, attribution, contribution, and copy-ready commander-prompt documentation.

### Compatibility note

Codex session formats and executor transports can change. This release treats the local JSONL `event_msg` / `payload.type = task_complete` shape as a version-sensitive observed contract and fails closed when it cannot observe the expected state safely.
