# Architecture

## Goal

Keep a high-capability root model responsible for decisions while moving long implementation work and passive waiting away from that root.

The default profile in this repository is:

- Commander: `gpt-5.6-sol`
- Executor: `gpt-5.6-luna`
- Executor reasoning effort: `max`
- Planner: commander/root
- Advisor: none
- Designer: none
- Wait layer: local operating-system process, not an LLM

This is a control-flow pattern, not a claim that these exact model names must exist forever. If OpenAI changes the model catalog, the same architecture can be applied to a premium commander and a lower-cost/high-volume executor after representative evaluation.

## State machine

```text
┌─────────────┐
│ USER_REQUEST│
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ SOL_BOUND_DELEGATION│
│ goal + constraints  │
│ acceptance criteria │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ LUNA_RUNNING        │
│ inspect / edit/test │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ OS_WAITING          │
│ no LLM heartbeat   │
└─────────┬───────────┘
          │ terminal event
          ▼
┌─────────────────────┐
│ SOL_VALIDATING      │
└──────┬─────────┬────┘
       │ pass    │ fail
       ▼         ▼
┌───────────┐  ┌──────────────────┐
│ COMPLETE  │  │ BOUNDED_CORRECT  │
└───────────┘  │ Sol → Luna       │
               └────────┬─────────┘
                        └──────→ LUNA_RUNNING
```

## Why an OS watcher?

A long executor task has two very different kinds of work:

1. **Model work** — reasoning, repository inspection, implementation, testing.
2. **Waiting** — no useful reasoning is required until the worker changes state.

Only the first category needs an LLM. The second can be handled by the operating system.

The primary Windows implementation uses PowerShell and `.NET` `FileSystemWatcher` notifications to observe writes to one Codex JSONL session file. It reads only newly appended bytes and looks for a structured terminal event.

Expected terminal record shape:

```json
{
  "type": "event_msg",
  "payload": {
    "type": "task_complete"
  }
}
```

The watcher does not infer success from wall-clock time. It waits for a structured event.

## Important distinction: authority vs activity

Sol remains the root authority even when it is not actively running a model turn.

The OS watcher cannot:

- reinterpret the user goal;
- approve a code change;
- change architecture;
- accept failed tests;
- select a fallback model;
- decide whether production evidence is sufficient.

It can only report a terminal executor event.

This separation is the point of the design.

## Bounded delegation packet

The commander should not send a giant duplicated repository dump to Luna. A normal packet should contain only:

```text
GOAL
- one concrete outcome

KNOWN EVIDENCE
- identifiers and already-proven facts that matter

NON-NEGOTIABLE CONSTRAINTS
- architecture, safety, production, permission boundaries

ACCEPTANCE CRITERIA
- deterministic conditions that prove completion

RETURN CONTRACT
- outcome
- root cause when relevant
- changed files/components
- tests/checks and results
- blockers
```

Luna should gather implementation context directly from the authorized workspace.

## Compact executor handoff

The executor should normally return:

```text
Outcome: PASS | BLOCKED | FAIL
Root cause: <bounded explanation>
Changed: <files/components>
Checks: <test/check → result>
Proof: <acceptance evidence>
Blockers: <none or exact blocker>
```

Avoid returning full logs or full diffs unless the commander needs a specific section for validation.

## Correction loop

If validation fails, Sol should send only the failed criterion and the minimum new evidence required to correct it.

Bad:

```text
<repeat the entire original prompt and repository history>
```

Good:

```text
Validation failed: rollback proof did not exercise the real enqueue function.
Correct only this criterion. Reuse the current executor context and return the
transaction trace plus the targeted test result.
```

## No duplicate workers

For one bounded unit of work there should be one active Luna executor unless deliberate parallelization is part of the plan.

Before starting another executor:

1. determine whether the existing executor is still running;
2. reuse/resume it when the transport safely supports continuation;
3. do not duplicate production mutations or external canaries;
4. fail closed if worker identity is ambiguous.

## Wait semantics

Preferred order:

1. If the executor transport itself provides a true blocking call that returns only on terminal completion, use it.
2. Otherwise, if the executor has a local Codex session event stream, use the native watcher.
3. Avoid recurring short `wait_thread` / `wait_agent` calls that re-enter the commander model loop.
4. If neither blocking transport nor observable terminal event is available, report the limitation rather than inventing completion.

A local watcher may internally wait, block, or receive filesystem notifications for minutes or hours. That is acceptable because it is not an LLM turn.

## Windows watcher mechanics

`scripts/watch-codex-task.ps1`:

- resolves one explicit session file;
- starts at the current end of the file by default, preventing an older `task_complete` event from falsely satisfying a new wait;
- subscribes to filesystem change notifications;
- reads only newly appended content;
- parses complete JSONL records;
- exits `0` on a new `task_complete` event;
- exits non-zero on timeout, file truncation/rotation ambiguity, or invalid setup;
- prints bounded status only.

Starting at EOF matters because a reused Codex session can contain earlier completed tasks.

## Portable fallback

`scripts/watch-codex-task.py` provides a dependency-free cross-platform fallback. It tails appended JSONL records with a small local file poll interval. This fallback still uses **zero LLM calls** while waiting, although its filesystem mechanism is polling rather than Windows event notifications.

## Failure model

### Executor cannot launch

If Luna is mandatory, report the exact launch/transport failure. Do not silently substitute Terra, Sol, or another model.

### Session file is missing

Fail immediately. Do not guess another session file unless the caller has an authoritative mapping.

### Session file is truncated or replaced

Fail closed by default because a stale watcher could otherwise report completion for the wrong task.

### Timeout

A timeout is not proof of executor failure. Return a timeout state to the orchestration layer. The commander can decide whether to inspect once, extend a process-level wait, or escalate a genuine blocker.

### Executor reports a blocker

A real decision blocker can wake Sol before final completion if the transport exposes it explicitly. Ordinary progress messages should not.

## Security boundaries

- Never commit local `.codex/sessions` files.
- Treat session logs as potentially sensitive.
- The watcher should not echo prompt text, tool arguments, credentials, or arbitrary event payloads.
- Observe only an explicitly selected session file.
- Do not modify the session file.
- Do not weaken repository permissions or production approval gates to keep orchestration automatic.

## Cost claims

This repository deliberately does not promise a fixed percentage saving.

Actual usage depends on task size, model effort, caching, retries, tool calls, context size, and Codex behavior. The architectural claim is narrower and testable:

> Replacing repeated root-model status checks with a non-LLM wait can eliminate those specific root-model polling turns.

Measure the workflow on representative tasks before drawing cost conclusions.

## Model rationale

OpenAI currently documents GPT-5.6 Sol as the frontier model for complex professional work and GPT-5.6 Luna as optimized for cost-sensitive, high-volume workloads. OpenAI also documents `max` as a supported GPT-5.6 reasoning effort.

References:

- https://developers.openai.com/api/docs/models/gpt-5.6-sol
- https://developers.openai.com/api/docs/models/gpt-5.6-luna
- https://developers.openai.com/api/docs/guides/latest-model

## Non-goals

This project is not trying to:

- replace Codex's permission model;
- bypass user approvals;
- guarantee that Luna Max is best for every coding workload;
- create hidden background work outside Codex authority;
- claim an official OpenAI architecture;
- scrape or mutate arbitrary Codex sessions;
- solve distributed scheduling in general.

It solves one narrow operational problem: **keep the commander authoritative without paying the commander to perform passive waiting.**
