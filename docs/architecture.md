# Architecture

## Goal

Keep GPT-5.6 Sol responsible for high-value judgment while moving long implementation work and passive waiting away from the root model.

Default logical roles:

- Commander: `gpt-5.6-sol`
- Executor: `gpt-5.6-luna`
- Executor reasoning effort: `max`
- Planner: commander/root
- Wait layer: local operating-system process, not an LLM

The executor role is intentionally **transport-agnostic**.

## Role vs transport

The architecture does not require a particular Codex worker API.

```text
ROLE
Luna Max executor

POSSIBLE TRANSPORTS
fresh Codex thread/session
native delegated worker/subagent
isolated Codex execution
another supported Luna-capable route
```

A transport is usable only if it can prove the required execution contract: Luna model, max reasoning, correct workspace, distinct executor identity, and observable terminal state.

If one transport rejects Luna, that is a transport capability result—not permission to silently substitute another model. Mark that route unsupported, avoid repeated retries, and use another explicitly supported Luna-capable transport only when available.

Once one route is verified, subsequent fresh Luna phases should reuse that transport choice rather than re-probing every phase.

## Workspace affinity

The hard execution identity is the authorized repository/workspace/folder.

If the active environment also has project metadata and the chosen transport preserves it, keep that association. Project nesting is useful context, but it is not the definition of the executor architecture.

Do not run broad project discovery when the commander already knows the authoritative work context.

## State machine

```text
USER_REQUEST
     ↓
SOL_BOUND_DELEGATION
     ↓
fresh LUNA_MAX_EXECUTOR
     ↓
LOCAL_PROCESS_WAIT
     ↓
SOL_VALIDATING
     ├─ overall goal complete → COMPLETE
     └─ more bounded work     → fresh LUNA_MAX_EXECUTOR
```

A Luna terminal event completes one executor phase, not necessarily the overall user goal.

## Fresh executor lifecycle

New bounded phases normally receive fresh Luna context. This prevents long implementation history, repeated tool traces, and compaction artifacts from contaminating unrelated later phases.

Same-session reuse is reserved for a short direct correction to the exact same phase when context is still clean and continuation is safe.

A `context_compacted` executor strongly favors fresh-session rollover.

## Bounded delegation packet

A fresh executor receives only what it needs:

```text
GOAL
<one concrete bounded outcome>

KNOWN PROOF
<validated facts that matter now>

CURRENT BLOCKER / NEXT STEP
<remaining work>

WORKSPACE IDENTITY
<repository / branch or worktree / folder / relevant project metadata>

NON-NEGOTIABLE CONSTRAINTS
<architecture, safety, permissions, production boundaries>

ACCEPTANCE CRITERIA
<deterministic proof>

RELEVANT IDENTIFIERS
<commit, workflow, test, canary, row ids when needed>

RETURN CONTRACT
- outcome
- root cause when relevant
- changed files/components
- checks/results
- proof
- blockers
- next bounded execution if any
```

The executor gathers implementation context directly from the authorized workspace instead of receiving a duplicated repository dump from Sol.

## Passive waiting

A long executor task mixes model work and waiting. Only model work needs an LLM.

The Windows watcher is a normal PowerShell process. It records the selected Luna session JSONL file's current byte offset, reads only newly appended bytes, parses complete JSONL records, and sleeps locally between filesystem checks.

Expected terminal record:

```json
{"type":"event_msg","payload":{"type":"task_complete"}}
```

The watcher does not infer success from elapsed time and does not call Sol or Luna.

Preferred waiting order:

1. true blocking executor transport;
2. local non-LLM watcher on the exact Luna executor session;
3. clear transport limitation if trustworthy terminal state cannot be observed.

Avoid recurring short `wait_thread`, `wait_agent`, or status-check loops that re-enter the commander model just to ask whether Luna is done.

## Windows watcher

`scripts/watch-codex-task.ps1`:

- resolves one explicit Luna session file;
- starts at current EOF by default;
- ignores historical `task_complete` records;
- checks the local file at a configurable process interval;
- reads only appended bytes;
- handles partial JSONL records;
- exits `0` on a new completion event;
- exits `124` on configured timeout;
- fails closed on truncation/replacement ambiguity;
- emits bounded terminal metadata only.

`scripts/watch-codex-task.py` provides a dependency-free portable fallback.

## Validation and correction

Sol validates compact Luna evidence rather than automatically accepting delegation output.

If validation fails, Sol returns only the failed criterion and required new evidence. A fresh Luna executor is preferred unless the correction is narrow enough to satisfy the same-session exception.

## Trace-first canaries

For live external canaries, the architecture favors information density over repeated trial-and-error sends:

```text
ONE live canary
→ freeze/correlate
→ live layer matrix
→ safe downstream component probes
→ defect ledger
→ repair phases
→ deterministic proof + deployment parity
→ ONE new end-to-end proof canary
```

Live status and component status remain separate. A downstream component that passes in isolation does not retroactively change a live `NOT_REACHED` layer to `PASS`.

See `skills/sol-luna-max-orchestrator/references/trace-first-canary.md`.

## Failure model

### Executor route rejects Luna

Mark that transport unsupported. Do not retry it repeatedly and do not silently substitute another model. One switch to another explicitly supported Luna-capable transport is allowed before real execution begins.

### Executor identity is ambiguous

Fail closed. The watcher must never guess which session belongs to the current Luna phase.

### Session file is missing, truncated, or replaced

Fail closed rather than associating completion with the wrong executor.

### Timeout

Timeout is not proof that Luna failed. It is a waiting-layer state that requires bounded commander judgment.

### Genuine blocker

A real permission, credential, business, safety, or irreversible-production decision may wake Sol early. Ordinary progress should not.

## Security boundaries

- Never commit Codex session files.
- Treat session logs as sensitive.
- Do not print arbitrary prompt/tool payloads.
- Observe only an explicitly selected Luna session.
- Preserve repository permissions and production approval boundaries.
- Do not weaken trust, tenant, receipt, or provider contracts for orchestration convenience.

## Cost claims

This repository does not promise a fixed savings percentage.

The testable architectural claims are narrower:

- local waiting can eliminate specific root-model polling turns;
- fresh executor rollover can reduce irrelevant carried executor context;
- bounded route verification can avoid repeated model/transport probing;
- trace-first canaries can reduce blind external retries.

Measure representative tasks before drawing broader conclusions.

## Model rationale

OpenAI currently documents GPT-5.6 Sol for complex professional work and GPT-5.6 Luna for cost-sensitive, high-volume workloads, with `max` available as a GPT-5.6 reasoning effort.

References:

- https://developers.openai.com/api/docs/models/gpt-5.6-sol
- https://developers.openai.com/api/docs/models/gpt-5.6-luna
- https://developers.openai.com/api/docs/guides/latest-model

## Non-goals

This project does not try to:

- make subagents mandatory;
- bypass Codex permissions;
- bypass production approvals;
- guarantee one private transport forever;
- guarantee Luna Max is optimal for every workload;
- claim an official OpenAI architecture.

It solves one operational problem: **keep the commander authoritative while execution and passive waiting happen in the layers best suited to them.**
