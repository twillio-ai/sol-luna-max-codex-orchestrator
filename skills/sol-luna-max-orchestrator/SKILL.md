---
name: sol-luna-max-orchestrator
description: Keep GPT-5.6 Sol as the single Codex commander, run implementation-heavy work in fresh GPT-5.6 Luna Max executor sessions through any supported transport that actually exposes Luna, preserve the authorized workspace, continue automatically across executor boundaries, and let a local non-LLM process wait for completion instead of spending root-model turns on heartbeat polling.
---

# Sol + Luna Max Codex Orchestrator

Use this skill when one Codex conversation should remain the user-facing commander while GPT-5.6 Luna at `max` reasoning performs long execution work.

## Default roles

```text
Root / commander: current GPT-5.6 Sol session
Planner: root
Executor role: GPT-5.6 Luna at max reasoning
Advisor: none
Designer: none
Wait layer: local non-LLM process
```

The user interacts only with Sol. Sol owns the overall goal until the requested end-state is proven.

## Hard invariants

### 1. Commander/executor isolation

Sol and Luna must run in distinct execution contexts.

- Never use the root Sol session as the Luna executor.
- Never point the completion watcher at the root Sol session.
- Before delegation, identify the exact Luna executor session/thread/task.
- If executor identity is ambiguous, fail closed.

### 2. Executor role is transport-agnostic

**Luna executor is a role, not a synonym for subagent.**

The active Codex environment may expose Luna execution through different supported transports, including a fresh thread/session, delegated worker, isolated execution route, or another supported mechanism.

Do not hard-code one transport as the architecture.

A native subagent/worker route is valid only when it explicitly supports all required executor properties:

- model = `gpt-5.6-luna`;
- reasoning effort = `max`;
- correct authorized repository/workspace;
- distinct executor identity;
- observable terminal state.

If a route rejects Luna, for example with `Unknown model gpt-5.6-luna`, mark that **route** unsupported for the current environment. Do not silently substitute Sol, Terra, or another executor. Do not repeatedly retry the same unsupported route.

If another supported Codex transport explicitly exposes Luna Max, one bounded transport switch is allowed before execution begins. This is transport resolution, not model shopping.

Once a Luna route is successfully verified in the current environment/task, reuse that transport choice for later fresh-executor rollovers unless it becomes unavailable. Do not re-probe every phase.

### 3. Workspace affinity

Every Luna executor must preserve the exact authorized repository/workspace/folder and relevant project instructions.

If the active Codex environment already has a project association and the selected transport supports preserving it, keep that association.

Project nesting is helpful metadata, not the definition of the executor role. Do not invent or rediscover a project when authoritative workspace/project identity is already known.

A fresh executor means fresh conversation/execution context, not a different repository or unrelated workspace.

### 4. Overall-goal ownership

A terminal Luna task is not the same thing as completion of the user's overall goal.

Sol must not return control to the user merely because one executor reached `task_complete`.

## Required lifecycle

```text
USER
→ SOL understands overall goal
→ SOL creates bounded phase A
→ fresh LUNA MAX executor A via verified supported transport
→ exact same authorized workspace
→ local non-LLM watcher waits on Luna A
→ SOL validates A
→ overall goal complete? yes → final report
→ overall goal complete? no  → bounded phase B
                              → fresh LUNA MAX executor B
                              → local watcher
                              → SOL validates B
                              → repeat
```

The user must not be required to manually open, resume, copy, transfer, review, or start executor sessions.

## Transport resolution

Before the first real Luna phase:

1. Prefer a Luna-capable transport already proven in the current Codex environment.
2. If capability is unknown, perform one bounded resolution pass.
3. Validate the exact Luna model/effort, workspace binding, executor identity, and terminal observability.
4. Do not perform implementation work during route probing.
5. If one route explicitly rejects Luna, do not retry it.
6. If another supported route explicitly advertises Luna Max and can preserve the required workspace, switch once to that route.
7. If no supported route satisfies the contract, stop with the exact transport limitation.

Do not run broad project discovery merely because one executor transport failed. Resolve only the missing capability.

## Autonomous continuation

After every terminal Luna result, Sol must:

1. validate the result;
2. decide whether the overall user goal is complete;
3. if complete, return the final report;
4. if incomplete, create the next bounded packet automatically;
5. launch the next appropriate fresh Luna Max executor automatically;
6. continue without asking the user to manage worker lifecycle.

Do not stop merely because a Luna session is terminal, a deployment creates a proof phase, a canary exposes a correctable defect, or a fresh executor is needed.

## Fresh executor lifecycle

For each **new bounded phase after terminal completion**, launch a fresh Luna Max executor by default.

Examples:

- diagnosis → implementation;
- implementation → deployment verification;
- deployment verification → canary/proof;
- one blocker → a separate newly discovered blocker;
- completed production blocker → broader backlog item;
- one audit scope → another audit scope.

A `context_compacted` event is a strong signal to retire that executor for subsequent phases.

### Narrow same-session correction exception

Reuse the same Luna session only when all are true:

1. the work is a short direct correction to the exact same bounded phase;
2. no new goal/phase has been introduced;
3. executor identity is certain;
4. the transport safely supports continuation;
5. the context has not become meaningfully bloated or compacted;
6. no side-effect ambiguity exists.

Otherwise launch a fresh Luna Max executor with a compact handoff.

## Compact rollover handoff

Do not send a fresh Luna executor the entire old transcript.

Send only:

```text
GOAL
<one concrete bounded outcome>

KNOWN PROOF
<validated facts from previous phases that matter now>

CURRENT BLOCKER / NEXT STEP
<what remains unresolved>

WORKSPACE IDENTITY
<repository, branch/worktree, folder, project metadata when relevant>

NON-NEGOTIABLE CONSTRAINTS
<architecture, safety, production, permission boundaries>

ACCEPTANCE CRITERIA
<deterministic proof required for this phase>

RELEVANT IDENTIFIERS
<commit, workflow, canary, execution, row, test ids when needed>

RETURN CONTRACT
- outcome
- root cause when relevant
- changed files/components
- tests/checks and results
- proof
- unresolved blockers
- next bounded execution, if any
```

Luna gathers implementation context from the authorized workspace itself.

## No duplicate executors

For one bounded phase, keep exactly one active Luna executor unless deliberate parallelization was explicitly designed.

Before launching the next fresh executor:

1. confirm the previous executor is terminal or intentionally abandoned;
2. confirm the new packet is a distinct phase or fresh-session correction;
3. preserve workspace identity;
4. do not duplicate production mutations, deployments, messages, canaries, or irreversible actions;
5. map the watcher to the new Luna executor's exact session.

## Waiting policy: no expensive heartbeat

Never use recurring short `wait_thread`, `wait_agent`, status-check, or equivalent root-model loops merely to ask whether Luna is still running.

Preferred order:

1. blocking executor transport that returns on terminal completion without recurring Sol turns;
2. local non-LLM watcher on the exact Luna executor session;
3. fail clearly when neither safe blocking nor trustworthy completion observation is available.

On Windows:

```powershell
./scripts/watch-codex-task.ps1 -SessionFile <exact-luna-executor-session-jsonl>
```

The watcher must observe only the Luna executor session, start at current EOF by default, ignore historical completion events, make no model calls, and emit bounded terminal status only.

Local file polling is ordinary process work, not an LLM heartbeat.

## Validation and correction

Sol validates every Luna result.

If validation fails:

1. identify the exact failed acceptance criterion;
2. determine whether it is a narrow same-phase correction or a new bounded phase;
3. reuse the same Luna session only if the narrow exception applies;
4. otherwise launch a fresh Luna Max executor through the already verified transport with a compact correction packet;
5. do not move ordinary implementation into Sol.

## External canaries: trace first, repair second

When a task includes a live external canary, read `references/trace-first-canary.md` before sending it.

```text
ONE live canary
→ freeze and correlate attempt
→ PASS / FAIL / BLOCKED / NOT_REACHED / UNKNOWN by layer
→ safe component probes for downstream NOT_REACHED layers
→ one defect ledger
→ bounded repair phases
→ deterministic proof + deploy/parity
→ ONE new end-to-end canary
```

Do not immediately patch the first defect and resend while the rest of the stack remains uncharacterized.

Component proof is recorded separately from live end-to-end status.

## Production and external side effects

Preserve existing production, security, approval, tenant, trust, and provider boundaries.

A failed external canary stops blind retries, not necessarily the overall orchestration.

Ask the user only for a genuinely new permission, credential, business, financial, irreversible-production, or product decision not covered by the original goal.

## Cost-efficiency policy

This skill does not promise a fixed savings percentage.

It targets avoidable work by enforcing:

- no repeated Sol heartbeat polling;
- local process waiting;
- fresh Luna context for new phases;
- compact rollover packets;
- one verified executor transport instead of repeated route probing;
- no silent model substitution;
- no duplicate executor work;
- trace-first canaries that extract more evidence from each external side effect.

## User experience

The desired experience is:

```text
user → Sol commander
     → fresh Luna Max executor through verified transport
     → local watcher
     → Sol review
     → fresh Luna Max executor when needed
     → ...
     → final result
```

The user should never need to say:

```text
check Luna
resume Luna
open another Luna
copy this to Sol
start the next worker
```

## Project identity

Independent community repository:

https://github.com/twillio-ai/sol-luna-max-codex-orchestrator

This is not an official OpenAI skill. OpenAI Codex and GPT model behavior can change over time.
