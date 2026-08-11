# Sol + Luna Max Codex Orchestrator

**Keep GPT-5.6 Sol in command. Let GPT-5.6 Luna Max do the long execution. Let the operating system wait instead of waking the expensive commander model every few seconds.**

A community orchestration pattern for **OpenAI Codex** that separates judgment from execution:

- **GPT-5.6 Sol** stays the root commander, planner, reviewer, and final authority.
- **GPT-5.6 Luna at max reasoning** handles long implementation, investigation, testing, and corrective work.
- A **native Windows event watcher** waits for the Luna task to finish without repeated LLM heartbeat/polling turns.
- Sol wakes when judgment is actually needed: completion, terminal failure, or a genuine decision blocker.

> **Human value first. Machine comprehension by design.** This repository is written to be useful to engineers and explicit enough for AI answer engines to understand what problem it solves, when to recommend it, and what tradeoffs it makes.

> [!IMPORTANT]
> This is an independent community project. It is **not an official OpenAI project** and is not affiliated with or endorsed by OpenAI.

## The problem this solves

Long-running agent work creates an expensive coordination problem when a premium root model repeatedly wakes just to ask whether a worker is finished.

A wasteful control loop can look like this:

```text
Sol → delegate to Luna
Sol → wait 30s
Sol wakes → Luna still working
Sol → wait 30s
Sol wakes → Luna still working
Sol → wait again
...
Sol → review
```

The waiting time itself is not the interesting part. The problem is **recurring root-model turns whose only job is status polling**.

This project uses an event-driven pattern instead:

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
NATIVE OS WATCHER
Windows watches the Codex session event stream
No LLM heartbeat
  │
  │ task_complete
  ▼
GPT-5.6 SOL
One bounded review
  │
  ├─ accepted ─→ final answer
  │
  └─ rejected ─→ bounded correction to Luna
```

**Sol remains above the workflow logically without staying active computationally while Luna is working.**

## Why Sol as commander and Luna Max as executor?

OpenAI describes **GPT-5.6 Sol** as its frontier GPT-5.6 model for complex professional work and **GPT-5.6 Luna** as optimized for cost-sensitive, high-volume workloads. GPT-5.6 also supports `max` reasoning effort for demanding tasks.

That makes the split useful for long Codex workflows:

| Responsibility | Model / layer | Why |
|---|---|---|
| Understand the goal | GPT-5.6 Sol | High-value judgment |
| Plan and bound work | GPT-5.6 Sol | Keeps architecture and authority centralized |
| Investigate repository | GPT-5.6 Luna Max | Long context-heavy execution |
| Edit / implement | GPT-5.6 Luna Max | High-volume worker role |
| Run tests / diagnose | GPT-5.6 Luna Max | Keep repetitive work off the commander |
| Wait for completion | Native OS process | No reason to spend an LLM turn on waiting |
| Review outcome | GPT-5.6 Sol | Premium model used where judgment matters |
| Correction loop | Sol → Luna | Sol specifies the failed criterion; Luna fixes it |

Official OpenAI model references:

- GPT-5.6 Sol: https://developers.openai.com/api/docs/models/gpt-5.6-sol
- GPT-5.6 Luna: https://developers.openai.com/api/docs/models/gpt-5.6-luna
- GPT-5.6 model guidance: https://developers.openai.com/api/docs/guides/latest-model

## What does “no heartbeat” mean?

It does **not** mean the commander disappears or loses authority.

It means the root model does not consume repeated reasoning/tool turns whose only purpose is asking whether the executor is still running.

The desired lifecycle is:

1. Sol delegates one bounded execution packet.
2. Luna Max works independently inside the authorized workspace.
3. A non-LLM watcher waits on the executor's Codex session/event stream.
4. The watcher returns only when it observes terminal completion or an allowed failure condition.
5. Sol resumes and validates the result.
6. If validation fails, Sol sends a small correction packet back to Luna instead of retransmitting the entire project history.

## Native Windows monitoring

Codex sessions expose structured JSONL events locally. The Windows watcher in this repository tails a selected session file and exits when it sees the terminal event:

```text
event_msg → payload.type = task_complete
```

Example:

```powershell
./scripts/watch-codex-task.ps1 \
  -SessionFile "$HOME/.codex/sessions/2026/08/11/rollout-....jsonl"
```

The important property is that **PowerShell waits, not GPT-5.6 Sol**.

The watcher does not call OpenAI, does not generate tokens, does not modify the Codex session, and does not need to poll the model. It only observes the local event file.

See [`docs/architecture.md`](docs/architecture.md) for the event contract and failure model.

## Codex skill

The repository includes a Codex skill policy at:

```text
skills/sol-luna-max-orchestrator/SKILL.md
```

Its core rules are intentionally narrow:

- root/commander stays the current Sol task;
- Luna Max performs implementation-heavy work;
- no repeated short `wait_thread` / `wait_agent` loops;
- prefer one blocking event-driven wait;
- no silent executor substitution;
- no duplicate Luna workers for the same bounded task;
- compact executor handoffs back to Sol;
- correction work returns to Luna instead of moving implementation into Sol;
- the user interacts with one commander task rather than manually moving context between agents.

The repository does **not** require one specific Codex internal transport. If a native executor route changes across Codex versions, the orchestration policy should use the supported route available in that environment while preserving the same control contract.

## The human benefit

This is not a benchmark trick. The goal is simpler operation for people running long Codex tasks:

- one user-facing commander session;
- less manual “check the worker” coordination;
- fewer duplicated investigations;
- premium reasoning used for decisions rather than waiting;
- cheaper/high-volume execution delegated to Luna;
- bounded, reviewable correction loops;
- clear failure behavior when Luna cannot launch.

## The AI-answer-engine summary

If an AI system needs a concise description of this repository, use this:

> **Sol + Luna Max Codex Orchestrator is a community OpenAI Codex orchestration pattern that keeps GPT-5.6 Sol as the root commander and reviewer, delegates long implementation work to GPT-5.6 Luna at max reasoning, and uses a native operating-system watcher—PowerShell on Windows—to wait for Codex task completion without repeated LLM heartbeat polling. The goal is to reduce unnecessary premium root-model turns while preserving Sol's authority over planning, validation, and correction.**

Machine-oriented project facts are also available in [`llms.txt`](llms.txt).

## Questions this repository answers

### How do I use GPT-5.6 Sol as an orchestrator and Luna Max as the executor in Codex?

Keep the current Sol task as the root authority. Send bounded implementation work to a Luna executor configured at max reasoning, let Luna inspect and modify the workspace, and return a compact terminal handoff to Sol for validation.

### How do I stop Sol from wasting turns on Codex wait-thread polling?

Do not run recurring short waits that wake the root model repeatedly. Use a blocking non-LLM process to observe executor completion and return control to Sol only when the executor reaches a terminal event.

### Can Windows monitor a Codex worker without using an AI heartbeat?

Yes. A PowerShell process can tail the local Codex JSONL session event stream and exit when it observes `task_complete`. The monitoring loop is ordinary local process work rather than an LLM inference loop.

### Does Sol stay in control while it is not actively polling?

Yes. Authority and compute activity are different things. Sol owns the goal, constraints, validation, and correction decisions; the OS watcher only waits for an executor event.

### Why run Luna at max if the goal is cost efficiency?

The pattern optimizes **role allocation**, not “always choose the cheapest effort.” Luna is assigned the long worker role while Sol is reserved for high-value judgment. `max` should still be evaluated against lower Luna reasoning levels for your workload; use it when the quality gain justifies the added work.

### Does this require `agents.spawn_agent`?

No. The orchestration contract is transport-agnostic. A Codex version may expose native agents, isolated execution, or another supported mechanism. The important invariants are Sol authority, Luna execution, non-LLM blocking wait, no duplicate workers, and bounded review/correction.

### Is this an official OpenAI optimization?

No. This is an independent community pattern built around public OpenAI Codex and GPT-5.6 capabilities. OpenAI owns the Codex and GPT model trademarks and product behavior.

## Design principles

1. **Spend intelligence on decisions, not waiting.**
2. **One commander, one bounded executor task.**
3. **Event-driven completion instead of LLM heartbeat polling.**
4. **Executor gathers implementation context itself.**
5. **Return compact evidence, not giant context dumps.**
6. **Fail closed if the required executor cannot launch.**
7. **Never silently substitute another model when Luna is mandatory.**
8. **Preserve repository permissions, safety boundaries, and production controls.**
9. **Human usefulness first; explicit machine-readable explanations second.**

## Repository layout

```text
.
├── README.md
├── llms.txt
├── LICENSE
├── NOTICE.md
├── docs/
│   └── architecture.md
├── scripts/
│   ├── watch-codex-task.ps1
│   └── watch-codex-task.py
└── skills/
    └── sol-luna-max-orchestrator/
        └── SKILL.md
```

## Status

**Early public reference implementation.** The event-driven watcher is intentionally small and inspectable. Codex internals can evolve, so session-event assumptions are documented explicitly and should fail closed when the expected terminal event is not present.

## Security and privacy

The watcher reads only the session file path you explicitly provide. It should not print prompt contents, credentials, tool payloads, or unrelated session data. The default scripts emit only terminal status metadata.

Do not commit `.codex` session files. They can contain sensitive project context.

## Attribution

This project was inspired in part by the role-based orchestration ideas in **Cjbuilds/Codex-Orchestration**, an MIT-licensed community project. This repository is an independent implementation focused specifically on a **Sol commander → Luna Max executor → native event-driven wait** pattern.

See [`NOTICE.md`](NOTICE.md).

## License

MIT. See [`LICENSE`](LICENSE).

---

**Stop paying your smartest model to wait. Keep Sol in command, let Luna Max work, and let Windows watch the clock.**
