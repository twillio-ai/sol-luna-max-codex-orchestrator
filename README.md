# Sol + Luna Max Codex Orchestrator

[![test](https://github.com/twillio-ai/sol-luna-max-codex-orchestrator/actions/workflows/test.yml/badge.svg)](https://github.com/twillio-ai/sol-luna-max-codex-orchestrator/actions/workflows/test.yml)

**Keep GPT-5.6 Sol in command. Let fresh GPT-5.6 Luna Max workers execute and independently review. Let the operating system wait instead of spending premium Sol turns on heartbeat polling.**

This is an independent community orchestration pattern for OpenAI Codex.

> [!IMPORTANT]
> This is not an official OpenAI project and is not affiliated with or endorsed by OpenAI.

## The core idea

Long Codex work mixes four jobs that should not be treated as the same thing:

1. **Command** — understand the user goal, constraints, permissions, and acceptance criteria.
2. **Execution** — investigate, implement, test, deploy, and correct.
3. **Independent review** — prove the executor's work instead of trusting its self-report.
4. **Waiting** — observe worker state without spending LLM turns just to ask whether it is done.

This project separates them:

```text
USER
  ↓
GPT-5.6 SOL
commander / bounded delegation
  ↓
fresh GPT-5.6 LUNA @ MAX executor
same authorized repository/workspace
  ↓
LOCAL PROCESS / BLOCKING TRANSPORT
waits without Sol heartbeat polling
  ↓
executor terminal
  ↓
different fresh GPT-5.6 LUNA @ MAX reviewer
independent inspection / proof
  ↓
reviewer verdict
  ├─ PASS → Sol cheap final sanity gate → final report
  ├─ FAIL → fresh Luna fixer → fresh Luna reviewer → repeat
  ├─ UNKNOWN → resolve/review again without claiming success
  └─ BLOCKED → ask user only if a genuinely new decision/permission is required
```

The critical rule is simple:

```text
Luna executor says done ≠ done
```

Final success requires a **different fresh Luna Max reviewer** to verify the resulting workspace/state first.

## Why this exists

Two expensive failure modes are common in long agentic coding work:

- the root model repeatedly wakes just to poll a worker that is still running;
- the root model trusts the executor's own "done" message and reports success before anyone independently checks the result.

This project rejects both patterns.

Sol should spend tokens on commander-level judgment, not heartbeat waiting or duplicate deep repository review. Luna Max performs the long implementation and the independent review in separate fresh contexts.

## Executor and reviewer roles are not transports

`Executor` and `Reviewer` are logical roles. They are not synonyms for `subagent`.

The active Codex environment may expose Luna Max through:

- a fresh Codex thread/session;
- a delegated/native worker route;
- `codex exec` or another isolated non-interactive route;
- another supported mechanism that explicitly runs `gpt-5.6-luna` at `max`.

No single transport is the architecture.

A route is acceptable only when it actually exposes Luna Max, preserves the authorized workspace, gives the worker a distinct identity, and has observable terminal completion.

If a route rejects Luna, mark that route unsupported. Do not repeatedly retry it and do not silently substitute Sol, Terra, or another model.

## Mandatory independent review gate

After every material implementation or correction phase:

1. the implementation Luna reaches a terminal state;
2. a **different fresh Luna Max reviewer** is launched automatically;
3. the reviewer independently inspects the resulting repository/workspace/state;
4. the reviewer verifies every acceptance criterion and returns one verdict:
   - `PASS`
   - `FAIL`
   - `BLOCKED`
   - `UNKNOWN`
5. Sol may report success only after `PASS` plus a concise commander-level sanity check.

The reviewer should be read-only whenever practical. It may run safe deterministic verification, but it must not silently become the fixer.

The implementation worker's summary is context, not proof.

## Automatic correction loop

A failed review does not return worker management to the user.

```text
review FAIL / resolvable UNKNOWN
→ compact failed-criteria packet
→ fresh Luna Max correction executor
→ local/blocking wait
→ different fresh Luna Max reviewer
→ repeat
```

The user should never have to manually say:

```text
check Luna
open another Luna
review Luna
fix what the reviewer found
copy this back to Sol
```

From the user's point of view, it is one Sol conversation.

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

When the verified transport itself blocks until completion, prefer that over polling. OpenAI's Codex non-interactive mode supports pipeline-style `codex exec`, machine-readable JSONL output, final-output files, and structured output schemas, which are useful for local orchestration without recurring root-model status turns.

## Wake policy

The cheapest safe path is:

```text
Sol dispatches once
→ local/blocking execution
→ local/blocking review
→ Sol wakes only for reviewer PASS or a semantic blocker
```

If the active host cannot safely chain executor → reviewer without resuming the root task, one Sol resume at a terminal boundary is allowed only to route the next worker. That routing wake must not:

- reread the whole repository;
- perform implementation;
- announce success;
- accept the executor summary as validation.

It should immediately launch the fresh reviewer and return to waiting.

## Workspace and project affinity

Fresh context must not mean unrelated work context.

Preserve the exact authorized repository/workspace/folder and relevant instructions for every executor, reviewer, and fixer. Existing project association should be preserved when supported and already known.

A fresh worker means a fresh execution context in the same authorized work scope.

## Fresh worker lifecycle

Fresh Luna context is the default for:

```text
diagnosis / implementation  → fresh Luna executor
independent verification     → different fresh Luna reviewer
failed review correction     → fresh Luna fixer
post-correction verification → different fresh Luna reviewer
```

The mandatory reviewer is never the same Luna session that produced the change it reviews.

## Sol's final sanity gate

Sol remains the commander, but it should not duplicate the expensive deep review that Luna already performed.

After reviewer `PASS`, Sol checks only that:

- reviewer identity differs from executor identity;
- the verdict is `PASS`;
- every material acceptance criterion has evidence;
- there is no unresolved blocker, unknown state, severe finding, or unverified external condition.

Then Sol reports the result to the user.

If evidence is incomplete, Sol launches another fresh Luna review instead of celebrating early.

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

## What the skill enforces

- Sol remains the single user-facing commander.
- Luna Max performs implementation-heavy work.
- A different fresh Luna Max reviewer is mandatory before final success.
- Executor self-report is never accepted as proof.
- No premature success language before reviewer `PASS`.
- Failed review automatically produces a fresh correction worker and another fresh review.
- Sol and Luna workers are distinct execution contexts.
- The Luna roles are transport-agnostic; subagents are optional, not canonical.
- No silent fallback to Sol, Terra, or another executor when Luna is required.
- Exact repository/workspace identity is preserved.
- No recurring Sol heartbeat/status loops.
- Local process waiting does not invoke a model.
- The user never manually manages worker sessions.

## Quick start

1. Read [`skills/sol-luna-max-orchestrator/SKILL.md`](skills/sol-luna-max-orchestrator/SKILL.md).
2. Adapt [`examples/commander-prompt.md`](examples/commander-prompt.md).
3. Preserve the real repository/workspace, permissions, and production gates.
4. Route Luna through a transport that explicitly supports Luna Max.
5. Attach local/blocking completion observation only to the exact active Luna worker.
6. Never finish after executor completion alone; run the mandatory fresh Luna review gate.

## FAQ

### Does this require Codex subagents?

No. Subagent is only one possible transport. The executor/reviewer architecture is independent of the mechanism used to launch Luna Max.

### What if a worker route says `Unknown model gpt-5.6-luna`?

Treat that route as unsupported for Luna in the current environment. Do not keep retrying it and do not silently substitute another model. If another supported Codex transport exposes Luna Max, use it; otherwise fail clearly.

### Why use another Luna to review instead of Sol doing the deep review?

Sol remains responsible for the decision, but Luna Max can do the expensive repository inspection and test verification in a fresh independent context. Sol receives a compact verdict/evidence packet and performs the final commander-level sanity gate.

### Can the executor review its own work?

No. Its own tests and summary are useful evidence, but the mandatory independent review must come from a different fresh Luna Max context.

### Does Sol stay in control while the OS waits?

Yes. Authority and compute activity are different. Sol owns the goal; the local wait layer simply avoids spending inference turns on mechanical waiting.

### Is this an official OpenAI optimization?

No. It is an independent community pattern built around public OpenAI Codex and GPT capabilities.

## Official OpenAI references

- GPT-5.6 Sol: https://developers.openai.com/api/docs/models/gpt-5.6-sol
- GPT-5.6 Luna: https://developers.openai.com/api/docs/models/gpt-5.6-luna
- GPT-5.6 guidance: https://developers.openai.com/api/docs/guides/latest-model
- Codex non-interactive mode: https://developers.openai.com/codex/noninteractive
- Codex: https://developers.openai.com/codex/

## Attribution

Inspired in part by role-based orchestration concepts from the MIT-licensed **Cjbuilds/Codex-Orchestration** project. This repository is an independent implementation.

See [`NOTICE.md`](NOTICE.md).

## License

MIT. See [`LICENSE`](LICENSE).

---

**Stop paying your smartest model to wait or duplicate deep review. Sol commands; fresh Luna Max executes; a different fresh Luna Max proves; Sol reports only after proof.**
