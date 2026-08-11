# Sol + Luna Max Codex Orchestrator

[![test](https://github.com/twillio-ai/sol-luna-max-codex-orchestrator/actions/workflows/test.yml/badge.svg)](https://github.com/twillio-ai/sol-luna-max-codex-orchestrator/actions/workflows/test.yml)

**Keep GPT-5.6 Sol in command. Let fresh GPT-5.6 Luna Max executors do the long work. Let the operating system wait instead of spending premium root-model turns on heartbeat polling.**

This is an independent community orchestration pattern for OpenAI Codex.

> [!IMPORTANT]
> This is not an official OpenAI project and is not affiliated with or endorsed by OpenAI.

## The core idea

Long Codex work mixes three jobs that should not be treated as the same thing:

1. **Judgment** — understand the goal, architecture, constraints, permissions, and proof.
2. **Execution** — investigate, implement, test, deploy, and correct.
3. **Waiting** — observe executor state until something actually requires judgment again.

This project separates them:

```text
USER
  ↓
GPT-5.6 SOL
commander / judgment / validation
  ↓
fresh GPT-5.6 LUNA @ MAX executor
same authorized repository/workspace
  ↓
WINDOWS / LOCAL PROCESS
waits on the exact Luna session
no LLM heartbeat
  ↓
task_complete
  ↓
GPT-5.6 SOL
validate overall goal
  ↓
next phase needed?
  ├─ no  → final report
  └─ yes → fresh Luna Max executor
```

## Executor role is not a transport

**Luna executor does not mean “subagent.”**

`Executor` is the logical role. The active Codex environment may expose that role through different supported transports, for example:

- a fresh Codex thread/session;
- a delegated/native worker route;
- an isolated Codex execution route;
- another supported route that can explicitly run `gpt-5.6-luna` at `max`.

No single transport is the architecture.

A native subagent route is acceptable **only if it actually exposes Luna Max and preserves the required workspace/session identity**. If it rejects Luna, mark that route unsupported for the current environment and do not repeatedly retry it or silently substitute Sol/Terra.

The commander should prefer a route already verified to support Luna Max. If route capability is unknown, perform one bounded capability-resolution pass, then use the valid transport for later fresh-executor rollovers without repeating model probes.

## Workspace and project affinity

Fresh executor context must not mean unrelated work context.

Preserve the exact authorized repository/workspace/folder and relevant instructions. When the active Codex transport also supports an existing project association, preserve it rather than opening an unrelated standalone executor.

The hard requirement is **correct workspace identity**. Project nesting is a useful transport capability when available, not a reason to invent or rediscover project identity that is already known.

Do not run project discovery merely to satisfy an abstraction if the commander already has authoritative workspace/project identity.

## Fresh executor lifecycle

New bounded phases should normally use fresh Luna context:

```text
diagnosis          → fresh Luna A
implementation     → fresh Luna B
deployment proof   → fresh Luna C
external proof     → fresh Luna D
```

A long or `context_compacted` Luna session should not become a permanent container for unrelated later phases.

Reuse the same Luna session only for a short direct correction to the exact same bounded phase when continuation is safe, identity is certain, context is still clean, and no new goal has been introduced.

Sol owns the **overall user goal**, so one Luna `task_complete` event is not automatically the end of the workflow. Sol validates the result and either finishes or rolls into the next bounded Luna phase automatically.

## No expensive heartbeat waiting

The repository includes a native Windows watcher:

```powershell
./scripts/watch-codex-task.ps1 -SessionFile <exact-luna-session-jsonl>
```

It starts at the selected session file's current EOF by default, reads only new JSONL records, and exits when it observes a new terminal `task_complete` event.

Current waiting implementation is ordinary local process polling:

```text
Windows reads local file → yes
OpenAI API call           → no
Sol inference             → no
Luna heartbeat            → no
```

A dependency-free Python fallback is included at `scripts/watch-codex-task.py`.

## Trace-first external canaries

When a live canary crosses many layers, do not immediately patch the first defect and resend.

Use the trace-first pattern documented in `skills/sol-luna-max-orchestrator/references/trace-first-canary.md`:

```text
ONE live canary
→ freeze/correlate attempt
→ PASS / FAIL / BLOCKED / NOT_REACHED / UNKNOWN by layer
→ safe component probes for downstream NOT_REACHED layers
→ one defect ledger
→ bounded repair phases
→ deterministic proof + deploy/parity
→ ONE new end-to-end canary
```

This maximizes evidence per external side effect and avoids one-canary-per-defect loops.

## Quick start

1. Read [`skills/sol-luna-max-orchestrator/SKILL.md`](skills/sol-luna-max-orchestrator/SKILL.md).
2. Adapt [`examples/commander-prompt.md`](examples/commander-prompt.md).
3. Preserve the real repository/workspace, permissions, and production gates.
4. Route Luna through a transport that explicitly supports Luna Max; do not assume a subagent API is required.
5. Attach the local watcher only to the exact Luna executor session.

## What the skill enforces

- Sol remains the single user-facing commander.
- Luna Max performs implementation-heavy phases.
- Sol and Luna are distinct execution contexts.
- The Luna **role is transport-agnostic**; subagent is optional, not canonical.
- No silent fallback to Sol, Terra, or another executor when Luna is required.
- Exact repository/workspace identity is preserved.
- Existing project association is preserved when supported and already known.
- New bounded phases use fresh Luna context by default.
- No recurring Sol `wait_thread` / `wait_agent` heartbeat loops.
- Local process waiting does not invoke a model.
- Sol validates the overall goal and continues automatically when more work remains.
- Trace-first canaries favor one diagnostic attempt, a defect ledger, repair, then one proof attempt.

## FAQ

### Does this require Codex subagents?

No. A subagent interface is only one possible executor transport. Use whichever supported Codex route can explicitly run Luna Max with the correct workspace and observable session identity.

### What if a native worker route says `Unknown model gpt-5.6-luna`?

Treat that **route** as unsupported for Luna in the current environment. Do not silently substitute another model and do not keep retrying the same route. If another supported Codex transport explicitly exposes Luna Max, use it; otherwise fail clearly.

### Should every phase reuse the same Luna chat?

Usually no. Fresh bounded phases should normally get fresh Luna context. Same-session reuse is reserved for narrow direct correction.

### Does Sol stay in control while Windows waits?

Yes. Authority and compute activity are different. The watcher only observes terminal executor state; Sol still owns the goal, validation, correction decisions, and final answer.

### Is this an official OpenAI optimization?

No. It is an independent community pattern built around public OpenAI Codex and GPT capabilities.

## Official OpenAI references

- GPT-5.6 Sol: https://developers.openai.com/api/docs/models/gpt-5.6-sol
- GPT-5.6 Luna: https://developers.openai.com/api/docs/models/gpt-5.6-luna
- GPT-5.6 guidance: https://developers.openai.com/api/docs/guides/latest-model
- Codex: https://developers.openai.com/codex/

## Attribution

Inspired in part by role-based orchestration concepts from the MIT-licensed **Cjbuilds/Codex-Orchestration** project. This repository is an independent implementation.

See [`NOTICE.md`](NOTICE.md).

## License

MIT. See [`LICENSE`](LICENSE).

---

**Stop paying your smartest model to wait. Keep Sol in command, route Luna Max through the transport that actually supports it, and let the operating system watch the task.**
