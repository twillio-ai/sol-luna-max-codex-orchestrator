# Architecture

## Goal

Keep a high-capability root model responsible for decisions while moving long implementation work and passive waiting away from that root.

Default profile:

- Commander: `gpt-5.6-sol`
- Executor: `gpt-5.6-luna`
- Executor reasoning effort: `max`
- Planner: commander/root
- Advisor: none
- Designer: none
- Wait layer: local operating-system process, not an LLM

This is a control-flow pattern, not a claim that these exact model names must exist forever.

## State machine

```text
USER_REQUEST
     │
     ▼
SOL_BOUND_DELEGATION
     │ goal + constraints + acceptance criteria
     ▼
LUNA_RUNNING
     │ inspect / edit / test
     ▼
LOCAL_PROCESS_WAIT
     │ no Sol/Luna heartbeat
     │ observes new terminal JSONL event
     ▼
SOL_VALIDATING
     │
     ├─ pass ─→ COMPLETE
     │
     └─ fail ─→ BOUNDED_CORRECTION → LUNA_RUNNING
```

## Why a local watcher?

A long executor task contains two different categories of work:

1. **Model work** — reasoning, repository inspection, implementation, and testing.
2. **Passive waiting** — no useful model judgment is required until executor state changes.

Only the first category needs an LLM.

The Windows watcher is a normal PowerShell process. It records the selected Codex JSONL session file's current byte offset, reads only newly appended bytes, parses complete JSONL records, and sleeps locally between filesystem checks. That local polling is intentionally **process-level polling, not model polling**.

Expected terminal record:

```json
{
  "type": "event_msg",
  "payload": {
    "type": "task_complete"
  }
}
```

The watcher does not infer success from elapsed time. It exits successfully only after a structured terminal event is observed.

## Authority vs. activity

Sol remains root authority even when it is not actively running a model turn.

The local watcher cannot:

- reinterpret the user goal;
- approve a code change;
- change architecture;
- accept failed tests;
- select a fallback model;
- decide whether production evidence is sufficient.

It can only observe terminal executor state.

## Bounded delegation packet

The commander should not send a giant duplicated repository dump to Luna. A normal packet contains:

```text
GOAL
- one concrete outcome

KNOWN EVIDENCE
- only facts that materially constrain the task

NON-NEGOTIABLE CONSTRAINTS
- architecture, safety, production and permission boundaries

ACCEPTANCE CRITERIA
- deterministic conditions that prove completion

RETURN CONTRACT
- outcome
- root cause when relevant
- changed files/components
- tests/checks and results
- blockers
```

Luna gathers implementation context directly from the authorized workspace.

## Compact executor handoff

```text
Outcome: PASS | BLOCKED | FAIL
Root cause: <bounded explanation>
Changed: <files/components>
Checks: <test/check → result>
Proof: <acceptance evidence>
Blockers: <none or exact blocker>
```

Avoid full logs or full diffs unless Sol needs a specific section for material validation.

## Correction loop

If validation fails, Sol sends only the failed criterion and minimum new evidence needed to correct it.

Good correction packet:

```text
Validation failed: rollback proof did not exercise the real enqueue function.
Correct only this criterion. Reuse the current executor context and return the
transaction trace plus the targeted test result.
```

Do not retransmit the entire project history by default.

## No duplicate workers

For one bounded unit of work, keep one active Luna executor unless deliberate parallelization was explicitly planned.

Before starting another executor:

1. determine whether the existing executor is still running;
2. reuse/resume it when the transport safely supports continuation;
3. do not duplicate production mutations or external canaries;
4. fail closed if worker identity is ambiguous.

## Wait semantics

Preferred order:

1. If the executor transport provides a true blocking call that returns only on terminal completion, use it.
2. Otherwise, if the executor has an exact local Codex session event stream, use a local non-LLM watcher.
3. Avoid recurring short `wait_thread` / `wait_agent` calls that re-enter the commander model loop.
4. If neither blocking transport nor trustworthy terminal state can be observed, report the limitation rather than inventing completion.

A local watcher may sleep and inspect file length for minutes or hours. That is acceptable because it is ordinary process work and does not invoke Sol or Luna.

## Windows watcher mechanics

`scripts/watch-codex-task.ps1`:

- resolves one explicit session file;
- records the current EOF by default so historical `task_complete` events cannot satisfy a new wait;
- optionally writes a local `ReadyFile` after the starting offset is captured;
- checks the local file at a configurable process-level interval (250 ms by default);
- reads only newly appended bytes;
- buffers partial JSONL records until a newline arrives;
- exits `0` on a new `task_complete` event;
- exits `124` on configured timeout;
- fails closed on truncation or ambiguous replacement;
- prints only bounded terminal status metadata.

The optional readiness signal is useful when a launcher wants to prove the watcher captured its starting offset before starting a very fast executor operation.

Starting at EOF matters because a reused Codex session can contain earlier completed tasks.

## Portable fallback

`scripts/watch-codex-task.py` provides the same dependency-free pattern on Windows, macOS, and Linux. It also performs a small local filesystem poll and makes zero LLM calls while waiting.

## Why not claim filesystem-event-driven waiting?

An earlier prototype used `.NET FileSystemWatcher`. Windows CI showed that syntax validity was not enough to guarantee dependable completion delivery in this use case. The implementation therefore uses explicit local file checks instead.

The orchestration is still **terminal-event-driven at the model boundary**: Sol resumes because a `task_complete` record is observed, not because a timer tells Sol to wake and ask Luna for status.

This distinction is intentional and documented rather than hidden behind marketing language.

## Failure model

### Executor cannot launch

If Luna is mandatory, report the exact launch/transport failure. Do not silently substitute Terra, Sol, or another model.

### Session file is missing

Fail immediately. Do not guess another session file unless the caller has an authoritative mapping.

### Session file is truncated or replaced

Fail closed. A stale offset could otherwise associate completion with the wrong task.

### Timeout

Timeout is not proof of executor failure. Return a timeout state to the orchestration layer. Sol can decide whether one bounded inspection or an extended local wait is appropriate.

### Genuine blocker

A real decision blocker can wake Sol early when the executor transport exposes it explicitly. Ordinary progress messages should not.

## Security boundaries

- Never commit `.codex/sessions` files.
- Treat session logs as potentially sensitive.
- Do not echo prompt text, tool arguments, credentials, or arbitrary event payloads.
- Observe only an explicitly selected session file.
- Do not modify the session file.
- Do not weaken repository permissions or production approval gates to keep orchestration automatic.

## Cost claims

This repository deliberately does not promise a fixed percentage saving.

Actual usage depends on task size, model effort, caching, retries, tool calls, context size, and Codex behavior. The architectural claim is narrower and testable:

> Replacing repeated root-model status checks with a non-LLM local wait can eliminate those specific root-model polling turns.

Measure representative tasks before drawing broader cost conclusions.

## Model rationale

OpenAI currently documents GPT-5.6 Sol as the frontier model for complex professional work and GPT-5.6 Luna as optimized for cost-sensitive, high-volume workloads. OpenAI also documents `max` as a supported GPT-5.6 reasoning effort.

References:

- https://developers.openai.com/api/docs/models/gpt-5.6-sol
- https://developers.openai.com/api/docs/models/gpt-5.6-luna
- https://developers.openai.com/api/docs/guides/latest-model

## Non-goals

This project does not try to:

- replace Codex permissions;
- bypass user approvals;
- guarantee that Luna Max is best for every workload;
- claim an official OpenAI architecture;
- scrape or mutate arbitrary Codex sessions;
- solve distributed scheduling in general.

It solves one narrow operational problem: **keep the commander authoritative without using the commander for passive waiting.**
