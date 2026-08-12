# Sol + Luna Max Codex Orchestrator

[![test](https://github.com/twillio-ai/sol-luna-max-codex-orchestrator/actions/workflows/test.yml/badge.svg)](https://github.com/twillio-ai/sol-luna-max-codex-orchestrator/actions/workflows/test.yml)

**GPT-5.6 Sol commands once. A local blocking controller runs fresh GPT-5.6 Luna Max execution, independent review, correction, and re-review. Sol is not awakened for heartbeat or worker routing.**

This is an independent community orchestration pattern for OpenAI Codex.

> [!IMPORTANT]
> This is not an official OpenAI project and is not affiliated with or endorsed by OpenAI.

## The exact workflow

```text
USER
  ↓
GPT-5.6 SOL
understand goal + constraints + acceptance criteria
  ↓ one blocking controller call
scripts/run_luna_cycle.py
  ↓
fresh GPT-5.6 LUNA @ MAX executor
  ↓ local process waits
DIFFERENT fresh GPT-5.6 LUNA @ MAX reviewer
  ↓ local process waits
  ├─ PASS → return compact proof to Sol
  ├─ FAIL/UNKNOWN → fresh Luna fixer → different fresh Luna reviewer → repeat
  └─ BLOCKED → return verified blocker to Sol
  ↓
GPT-5.6 SOL
cheap final sanity gate + user-facing result
```

There is **no intermediate Sol routing wake** between executor, reviewer, fixer, or re-review.

## The two rules that matter most

```text
Luna executor says done ≠ done
waiting/routing ≠ a reason to wake Sol
```

An executor reaching `task_complete`, returning exit 0, or saying tests passed is only an executor claim.

Final success requires a **different fresh Luna Max reviewer** to independently verify every material acceptance criterion with evidence.

## Zero-wake local controller

The repository includes:

```text
scripts/run_luna_cycle.py
```

Sol launches it once with a compact JSON packet and the exact authorized target workspace. The Python process synchronously chains fresh `codex exec` workers and does not return to Sol until a terminal orchestration state exists:

```text
PASS
BLOCKED
EXHAUSTED
TRANSPORT_ERROR
```

Typical packet:

```json
{
  "goal": "implement the requested production-safe change",
  "acceptance_criteria": [
    "the target behavior works",
    "relevant tests pass"
  ],
  "constraints": [
    "do not change unrelated behavior"
  ],
  "context": "optional essential context only"
}
```

Typical Windows invocation:

```powershell
python scripts/run_luna_cycle.py `
  --packet .\packet.json `
  --workspace C:\path\to\authorized\repo
```

The controller explicitly routes workers to `gpt-5.6-luna`, requests `max` reasoning effort, disables descendant agent fan-out, uses structured outputs, and keeps the executor/reviewer contexts fresh and separate.

## Why `codex exec`

OpenAI documents `codex exec` as the non-interactive Codex mode for scripts and pipelines. It can run against a selected workspace/model/sandbox, block until completion, and emit machine-readable/structured final output. That makes it suitable for mechanical worker chaining without model heartbeat turns.

The controller uses fresh non-interactive runs rather than relying on `agents.spawn_agent`, so a subagent route is not required to expose Luna.

## Mandatory independent review

After every material implementation or correction:

1. implementation Luna becomes terminal;
2. the controller launches a **different fresh Luna Max reviewer** automatically;
3. the reviewer independently inspects the resulting workspace/state;
4. it verifies each acceptance criterion;
5. it returns exactly `PASS`, `FAIL`, `BLOCKED`, or `UNKNOWN`.

A valid `PASS` requires exact criterion coverage, `PASS` for every criterion, concrete evidence, and no unresolved high/critical finding.

The controller defensively downgrades inconsistent `PASS` output to `UNKNOWN`.

## Automatic correction and re-review

A failed review never sends worker management back to the user or to Sol.

```text
FAIL / resolvable UNKNOWN
→ fresh Luna Max fixer
→ local blocking wait
→ different fresh Luna Max reviewer
→ repeat
```

A finite cycle limit prevents infinite token spend. If the limit is reached, the controller returns `EXHAUSTED` with the latest independent review evidence. `EXHAUSTED` is never reported as success.

## No expensive heartbeat or routing turns

While the controller is running:

```text
Sol heartbeat inference  → no
Sol routing inference    → no
Luna status heartbeat    → no
local process waiting    → yes
```

The older session-file watchers remain useful for Luna-capable transports that expose a session JSONL file, but the default zero-wake path is the blocking controller.

## Sol's job after the controller returns

For `PASS`, Sol performs only a cheap commander-level check:

- terminal status is `PASS`;
- independent review evidence covers every material acceptance criterion;
- no unresolved blocker/high-severity finding remains.

Sol should not reread the entire repository or duplicate Luna's deep review just to spend premium tokens again.

For `BLOCKED`, `EXHAUSTED`, or `TRANSPORT_ERROR`, Sol reports the exact terminal state and asks the user only when a genuinely new permission, credential, business/financial decision, or irreversible-production choice is required.

## Workspace and safety

All fresh workers stay on the exact authorized repository/workspace. Fresh context never means a different project.

Existing production, security, tenant, approval, provider, financial, and irreversible-action boundaries remain in force. Automatic worker routing does not authorize duplicate deployments, messages, canaries, purchases, or destructive actions.

## What the project enforces

- One user-facing Sol commander.
- One initial Sol dispatch into the blocking controller.
- Zero recurring Sol heartbeat turns.
- Zero Sol routing wakes between Luna stages.
- Luna Max for implementation-heavy work.
- Different fresh Luna Max reviewer before success.
- Executor/fixer cannot self-certify.
- Automatic correction + re-review.
- Finite correction-cycle limit.
- No silent Luna→Terra/Sol substitution.
- Exact workspace affinity.
- Compact structured handoffs instead of transcript replay.
- User never manually manages worker sessions.

## Files

- `skills/sol-luna-max-orchestrator/SKILL.md` — orchestration contract.
- `scripts/run_luna_cycle.py` — blocking executor/reviewer/correction controller.
- `scripts/watch-codex-task.ps1` — Windows exact-session watcher for alternate transports.
- `scripts/watch-codex-task.py` — dependency-free watcher fallback.
- `examples/commander-prompt.md` — copy-ready Sol instructions.
- `tests/` — regression tests for watcher and orchestration contracts.

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

**Sol commands. Luna executes. A different Luna proves. The local controller routes and waits. Sol wakes only when the cycle is terminal.**
