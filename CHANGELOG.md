# Changelog

## 0.1.0 — 2026-08-12

Initial public reference implementation.

### Added

- GPT-5.6 Sol commander / GPT-5.6 Luna Max executor orchestration policy.
- Native Windows PowerShell process watcher with explicit start-at-EOF semantics and configurable local polling; passive waiting does not invoke Sol or Luna.
- Dependency-free portable Python watcher.
- Start-at-EOF behavior to prevent historical `task_complete` events from satisfying a new wait.
- Optional watcher readiness signal for deterministic launcher/test synchronization.
- Fail-closed handling for truncated or replaced session state.
- Regression tests for historical completion, new completion, partial JSONL writes, truncation, and explicit from-start scanning.
- GitHub Actions validation on Python 3.11, 3.12, 3.13, plus a Windows PowerShell parse and end-to-end completion test.
- Human-first README with explicit answer-engine-friendly project facts and FAQ.
- `llms.txt` project summary.
- Architecture, attribution, contribution, and copy-ready commander-prompt documentation.

### Implementation note

A `.NET FileSystemWatcher` prototype was tested and intentionally replaced by deterministic local PowerShell file checks after Windows CI showed unreliable completion delivery for this use case. The orchestration boundary remains terminal-event-driven: Sol resumes when a new `task_complete` record is observed, while the wait itself is ordinary local process work.

### Compatibility note

Codex session formats and executor transports can change. This release treats the local JSONL `event_msg` / `payload.type = task_complete` shape as a version-sensitive observed contract and fails closed when it cannot observe the expected state safely.
