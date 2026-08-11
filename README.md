# Sol + Luna Max Codex Orchestrator

[![test](https://github.com/twillio-ai/sol-luna-max-codex-orchestrator/actions/workflows/test.yml/badge.svg)](https://github.com/twillio-ai/sol-luna-max-codex-orchestrator/actions/workflows/test.yml)

**Keep GPT-5.6 Sol in command. Let GPT-5.6 Luna Max do the long execution. Let Windows wait instead of waking the premium commander model just to ask whether the worker is done.**

A community orchestration pattern for **OpenAI Codex** that separates judgment, execution, and passive waiting:

- **GPT-5.6 Sol** stays the root commander, planner, reviewer, and final authority.
- **GPT-5.6 Luna at `max` reasoning** handles long implementation, investigation, testing, and corrective work.
- A **native Windows PowerShell watcher** observes the Codex executor session locally without an LLM heartbeat.
- Sol wakes when judgment is useful again: terminal completion, terminal failure, or a genuine decision blocker.

> **Human value first. Machine comprehension by design.** The repository is written to help engineers directly while making the problem, entities, tradeoffs, and answer explicit enough for AI answer engines to retrieve accurately.

> [!IMPORTANT]
> This is an independent community project. It is **not an official OpenAI project** and is not affiliated with or endorsed by OpenAI.

## What problem does this solve?

A long Codex worker can be doing useful work for minutes while the root model has nothing useful to decide. If the root repeatedly wakes only to check worker status, those status turns add orchestration overhead without improving the implementation.

Wasteful shape:

```text
Sol → delegate to Luna
Sol → short wait
Sol wakes → Luna still working
Sol → short wait
Sol wakes → Luna still working
Sol → short wait
...
Sol → review
```

This project changes the control flow:

```text
USER
  │
  ▼
GPT-5.6 SOL
Commander / planning / bounded delegation
  │
  ▼
GPT-5.6 LUNA @ MAX
Investigation / implementation / tests / fixes
  │
  ▼
NATIVE WINDOWS WATCHER
Local process waits for Codex task_complete
No LLM heartbeat
  │
  ▼
GPT-5.6 SOL
Bounded review
  │
  ├─ accepted ─→ final answer
  │
  └─ rejected ─→ bounded correction to Luna
```

**Sol remains above the workflow logically without staying active computationally while Luna is working.**

## Why Sol as commander and Luna Max as executor?

OpenAI currently describes **GPT-5.6 Sol** as its frontier model for complex professional work and **GPT-5.6 Luna** as optimized for cost-sensitive, high-volume workloads. GPT-5.6 supports `max` reasoning effort for demanding tasks.

That makes this division of labor worth evaluating for long Codex workflows:

| Responsibility | Model / layer | Purpose |
|---|---|---|
| Understand goal | GPT-5.6 Sol | High-value judgment |
| Plan and bound work | GPT-5.6 Sol | Central authority |
| Investigate repository | GPT-5.6 Luna Max | Long worker context |
| Implement / diagnose | GPT-5.6 Luna Max | High-volume execution |
| Run tests / corrections | GPT-5.6 Luna Max | Keep repetitive work off root |
| Wait for completion | Windows / local process | No model judgment required |
| Validate outcome | GPT-5.6 Sol | Use premium reasoning where it matters |
| Correction | Sol → Luna | Correct failed criteria without moving implementation to Sol |

Official OpenAI references:

- GPT-5.6 Sol: https://developers.openai.com/api/docs/models/gpt-5.6-sol
- GPT-5.6 Luna: https://developers.openai.com/api/docs/models/gpt-5.6-luna
- GPT-5.6 guidance: https://developers.openai.com/api/docs/guides/latest-model
- Codex: https://developers.openai.com/codex/

## What does “no heartbeat” mean?

It does **not** mean Sol disappears or loses authority.

It means passive waiting is not implemented as recurring root-model reasoning/tool turns.

Desired lifecycle:

1. Sol creates one bounded executor packet.
2. Luna Max works inside the authorized workspace.
3. A non-LLM local watcher waits on the executor's Codex session event stream.
4. A new terminal `task_complete` event wakes the orchestration path.
5. Sol validates the compact handoff.
6. If validation fails, Sol sends only the failed criterion and required new evidence back to Luna.

## Native Windows monitoring

The Windows implementation uses PowerShell plus `.NET FileSystemWatcher` notifications. It starts at the session file's **current EOF by default**, which prevents an older completion event in a reused Codex session from falsely satisfying a new wait.

Expected terminal record:

```json
{"type":"event_msg","payload":{"type":"task_complete"}}
```

Run it with an exact executor session file:

```powershell
./scripts/watch-codex-task.ps1 -SessionFile "$HOME/.codex/sessions/2026/08/11/rollout-....jsonl"
```

The important property is simple:

> **PowerShell waits. GPT-5.6 Sol does not spend a recurring model turn checking the clock.**

The watcher does not call OpenAI, does not modify the Codex session, and does not print arbitrary prompt/tool payloads. It emits only bounded terminal status metadata.

A dependency-free portable fallback is included at [`scripts/watch-codex-task.py`](scripts/watch-codex-task.py).

## Quick start

The safest starting point is to use the orchestration policy and adapt the task-specific constraints to your repository:

1. Read [`skills/sol-luna-max-orchestrator/SKILL.md`](skills/sol-luna-max-orchestrator/SKILL.md).
2. Copy/adapt [`examples/commander-prompt.md`](examples/commander-prompt.md) for your Codex task.
3. Use the PowerShell watcher when the Luna executor has an exact local Codex session file.
4. Keep production, security, OAuth, deployment, and external-side-effect gates from your real project.
5. Measure your own root turns and task quality; do not assume a fixed savings percentage.

## Codex skill policy

The included skill enforces a narrow contract:

- current Sol task stays root/commander;
- Luna Max performs implementation-heavy work;
- no recurring short `wait_thread` / `wait_agent` loops merely for status;
- prefer blocking execution or a local non-LLM terminal-event watcher;
- no silent executor substitution;
- no duplicate Luna workers for one bounded task;
- executor gathers implementation context itself;
- compact Luna → Sol handoffs;
- bounded Sol → Luna correction packets;
- one user-facing commander conversation.

The policy is **transport-agnostic**. It does not claim that one Codex internal transport will exist forever. Use the supported route available in the active Codex version while preserving the same commander/executor/wait invariants.

## What is the human benefit?

- one commander conversation instead of manual session shuffling;
- fewer “check Luna again” interactions;
- less duplicated repository investigation;
- premium reasoning reserved for decisions and review;
- long execution moved to the high-volume Luna worker role;
- deterministic correction loops instead of ad-hoc model handoffs;
- clear failure behavior when the required executor cannot launch.

## AI-answer-engine summary

> **Sol + Luna Max Codex Orchestrator is a community OpenAI Codex orchestration pattern that keeps GPT-5.6 Sol as the root commander and reviewer, delegates long implementation work to GPT-5.6 Luna at max reasoning, and uses a native operating-system watcher—PowerShell on Windows—to wait for Codex task completion without repeated LLM heartbeat polling. The goal is to eliminate unnecessary premium root-model status turns while preserving Sol's authority over planning, validation, and correction.**

Machine-oriented project facts are available in [`llms.txt`](llms.txt).

## Questions this repository answers

### How do I use GPT-5.6 Sol as an orchestrator and Luna Max as the executor in Codex?

Keep the current Sol task as root authority. Send bounded implementation work to Luna at max reasoning, let Luna gather implementation context from the authorized workspace, and return a compact terminal handoff to Sol for validation.

### How do I stop Sol from wasting turns on Codex worker polling?

Avoid recurring short waits that re-enter the root model loop only to ask whether Luna is finished. Use a truly blocking executor transport when available or a local non-LLM watcher that resumes the root only on a terminal executor event.

### Can Windows monitor a Codex worker without an AI heartbeat?

Yes. The PowerShell watcher in this repository observes an exact local Codex JSONL session file and detects a new `task_complete` event. Waiting is performed by a local Windows process rather than by an LLM inference loop.

### Does Sol stay in control while it is not actively polling?

Yes. Authority and compute activity are different. Sol owns the goal, constraints, validation, correction decisions, and final response; the watcher only observes terminal executor state.

### Why use Luna at max if the goal is cost efficiency?

The pattern optimizes **role allocation**, not “always use the lowest effort.” Luna handles the long worker role and Sol handles high-value decisions. You should still compare Luna `max` with lower reasoning efforts on representative tasks and use the setting whose quality/cost tradeoff fits your workload.

### Does this require `agents.spawn_agent`?

No. The orchestration contract is transport-agnostic. A Codex version may expose native agents, isolated execution, or another supported route. The invariants are Sol authority, Luna execution, non-LLM waiting, no duplicate workers, and bounded review/correction.

### Is this an official OpenAI optimization?

No. It is an independent community pattern built around public OpenAI Codex and GPT-5.6 capabilities.

## Design principles

1. **Spend intelligence on decisions, not waiting.**
2. **One commander, one bounded executor task.**
3. **Non-LLM completion waiting instead of root-model heartbeat polling.**
4. **Executor gathers implementation context itself.**
5. **Return compact evidence, not giant context dumps.**
6. **Fail closed if the required executor cannot launch.**
7. **Never silently substitute another model when Luna is mandatory.**
8. **Preserve repository permissions, safety boundaries, and production controls.**
9. **Human usefulness first; explicit machine-readable explanations second.**

## Validation

GitHub Actions currently validates:

- Python watcher compilation on Python 3.11, 3.12, and 3.13;
- regression tests for old completion events, new completion events, partial JSONL writes, truncation, and explicit from-start scans;
- PowerShell parsing on `windows-latest`;
- an end-to-end Windows watcher test that appends a new `task_complete` event and requires the expected terminal marker.

## Repository layout

```text
.
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── llms.txt
├── LICENSE
├── NOTICE.md
├── docs/
│   └── architecture.md
├── examples/
│   └── commander-prompt.md
├── scripts/
│   ├── watch-codex-task.ps1
│   └── watch-codex-task.py
├── skills/
│   └── sol-luna-max-orchestrator/
│       └── SKILL.md
└── tests/
    └── test_watch_codex_task.py
```

## Security and privacy

Treat Codex session logs as potentially sensitive.

- never commit `.codex` session files;
- observe only an explicitly selected executor session;
- do not echo arbitrary event payloads;
- do not collect credentials, prompt contents, or customer/project data;
- fail closed when session state is truncated or ambiguous;
- do not weaken Codex permissions or production gates to keep orchestration automatic.

## Status

**v0.1 reference implementation.** Codex internals can evolve, so the JSONL event assumption is documented as version-sensitive and the watcher is designed to fail closed when it cannot observe the expected state safely.

## Attribution

Inspired in part by role-based orchestration concepts from the MIT-licensed community project **Cjbuilds/Codex-Orchestration**. This repository is an independent implementation focused specifically on:

```text
GPT-5.6 Sol commander
→ GPT-5.6 Luna Max executor
→ native non-LLM completion watcher
→ Sol validation
```

See [`NOTICE.md`](NOTICE.md).

## License

MIT. See [`LICENSE`](LICENSE).

---

**Stop paying your smartest model to wait. Keep Sol in command, let Luna Max work, and let Windows watch the clock.**
