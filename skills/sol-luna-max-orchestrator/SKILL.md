---
name: sol-luna-max-orchestrator
description: Keep GPT-5.6 Sol as the single Codex commander, run implementation-heavy work in fresh GPT-5.6 Luna Max executor sessions, wait without root-model heartbeat polling, require an independent fresh Luna Max review before success, and continue executor/reviewer/correction cycles automatically without user-managed worker sessions.
---

# Sol + Luna Max Codex Orchestrator

Use this skill when one Codex conversation should remain the user-facing commander while GPT-5.6 Luna at `max` reasoning performs long execution and independent review work.

## Default roles

```text
Root / commander: current GPT-5.6 Sol session
Planner: root
Implementation executor: fresh GPT-5.6 Luna at max
Independent reviewer: different fresh GPT-5.6 Luna at max
Correction executor: fresh GPT-5.6 Luna at max
Wait layer: local non-LLM process or blocking transport
Advisor: none
Designer: none
```

The user interacts only with Sol. Sol owns the overall goal until the requested end-state is independently proven.

## Hard invariants

### 1. The user never orchestrates workers

The user must not be required to say or do any of the following:

```text
check Luna
resume Luna
open another Luna
copy this to Sol
review what Luna did
start a reviewer
start the next worker
```

One user request enters the Sol task. The orchestration loop continues automatically until independent proof passes or a genuinely new user decision/permission is required.

### 2. Commander, executor, and reviewer are distinct roles

Sol and every Luna worker must run in distinct execution contexts.

- Never use the root Sol session as an implementation executor.
- Never use the implementation Luna as its own independent reviewer.
- The mandatory reviewer must be a fresh Luna Max context with a distinct identity.
- Never point a completion watcher at the root Sol session.
- Before each launch, identify the exact worker session/thread/task and workspace.
- If worker identity is ambiguous, fail closed.

### 3. Luna is a role, not a transport

The active Codex environment may expose Luna through a fresh thread/session, delegated worker, `codex exec`, isolated execution route, or another supported mechanism.

A route is valid only when it explicitly provides all required properties:

- model = `gpt-5.6-luna`;
- reasoning effort = `max`;
- correct authorized repository/workspace;
- distinct worker identity;
- observable terminal state.

If a route rejects Luna, for example `Unknown model gpt-5.6-luna`, mark that route unsupported. Do not silently substitute Sol, Terra, or another executor. Do not repeatedly retry the same unsupported route.

If another supported Codex transport explicitly exposes Luna Max, one bounded transport switch is allowed before real execution begins. Once a Luna-capable transport is proven, reuse that transport for later fresh workers unless it becomes unavailable. Do not re-probe every phase.

### 4. Workspace affinity is mandatory

Every executor and reviewer must preserve the exact authorized repository/workspace/folder and relevant project instructions.

A fresh worker means fresh conversation/execution context, not a different repository.

If an authoritative workspace/project identity is already known, preserve it. Do not rediscover or invent another project merely because the transport changed.

### 5. No root-model heartbeat polling

Never spend recurring Sol turns asking whether Luna is still running.

Preferred order:

1. blocking worker transport that returns only at terminal completion;
2. a local non-LLM watcher on the exact Luna worker session;
3. a local non-LLM controller that chains executor/reviewer stages;
4. fail clearly if no safe completion observation exists.

A watcher may poll a local process/file. It must not invoke Sol, Luna, or another LLM merely to check status.

Sol should wake only when semantic judgment is required, not on a timer.

### 6. Executor completion is not success

A Luna implementation worker reaching `task_complete`, returning exit code 0, claiming tests passed, or saying the task is done is only an **executor claim**.

It is never sufficient evidence for final success.

Sol must not repeat or paraphrase an executor's success claim to the user before the mandatory independent review gate passes.

### 7. Mandatory independent Luna review gate

After every implementation/correction phase that changes code, configuration, deployment state, data logic, or another material artifact, launch a **fresh Luna Max reviewer** before any final success response.

The reviewer must independently inspect the authorized workspace and verify the acceptance criteria. It must not trust the executor's summary as proof.

The reviewer should be read-only whenever practical. It may run safe verification commands/tests needed for proof, but it must not silently become the fixer.

The reviewer returns exactly one verdict:

```text
PASS
FAIL
BLOCKED
UNKNOWN
```

A valid `PASS` requires evidence for every material acceptance criterion.

### 8. No premature celebration

Sol may not tell the user the work is complete, fixed, deployed, correct, successful, ready, or verified unless all of these are true:

1. the latest material implementation phase is terminal;
2. a different fresh Luna Max reviewer inspected the resulting workspace/state;
3. reviewer verdict is `PASS`;
4. every required acceptance criterion has evidence;
5. no unresolved blocker or unsafe ambiguity remains.

If any item is missing, continue the loop or report the exact blocker. Never convert `UNKNOWN` into success.

## Required lifecycle

```text
USER
→ SOL understands overall goal and acceptance criteria
→ SOL creates one bounded implementation packet
→ fresh LUNA MAX EXECUTOR
→ blocking/local non-LLM wait (NO SOL HEARTBEAT)
→ executor terminal
→ fresh LUNA MAX REVIEWER (different context, independent inspection)
→ blocking/local non-LLM wait (NO SOL HEARTBEAT)
→ reviewer verdict

PASS
→ SOL performs a cheap final sanity gate on the compact verdict/evidence
→ final user report

FAIL / UNKNOWN
→ compact failed-criteria packet
→ fresh LUNA MAX CORRECTION EXECUTOR
→ non-LLM wait
→ fresh LUNA MAX REVIEWER
→ repeat automatically

BLOCKED
→ continue automatically if the blocker is technically resolvable within existing authority
→ otherwise ask the user only for the genuinely new permission/credential/business/financial/irreversible decision
```

The normal workflow is therefore not:

```text
Luna says done → Sol says done
```

It is:

```text
Luna implements → different Luna proves → Sol reports only after proof
```

## Wake policy and cost control

The orchestration should minimize Sol activations without weakening proof.

### Preferred path

When the selected transport can be safely chained by a local non-LLM controller, keep Sol dormant across mechanical stage boundaries:

```text
Sol dispatches bounded work
→ local controller starts Luna executor
→ waits locally
→ local controller starts fresh Luna reviewer using the fixed acceptance packet/workspace
→ waits locally
→ wakes Sol only on reviewer PASS or a semantic blocker
```

The local layer may use process exit, JSONL terminal events, structured final output, or other deterministic transport data. It must not make an LLM judgment itself.

### Fallback path

If the host cannot safely launch the reviewer without resuming the root task, one Sol resume at a terminal boundary is allowed only to route the next worker.

In that fallback resume Sol must:

- not reread the whole repository;
- not perform implementation;
- not announce success;
- not accept the executor summary as validation;
- immediately create a compact reviewer packet and launch a fresh Luna Max reviewer.

This is a routing wake, not a deep-review turn.

## Independent reviewer contract

Give the fresh reviewer a compact packet containing:

```text
OVERALL GOAL
<user end-state>

PHASE ACCEPTANCE CRITERIA
<deterministic criteria that must be proven>

WORKSPACE IDENTITY
<repository, branch/worktree, folder, project metadata when relevant>

KNOWN CHANGED SCOPE
<files/components/commit identifiers when known; not executor claims of correctness>

NON-NEGOTIABLE CONSTRAINTS
<architecture, safety, production, permission boundaries>

REVIEW RULES
- inspect the resulting workspace/state independently
- do not trust the executor summary as proof
- verify each acceptance criterion
- run safe deterministic checks when needed
- do not edit implementation during review unless explicitly reassigned as fixer

RETURN CONTRACT
verdict: PASS | FAIL | BLOCKED | UNKNOWN
criteria:
  - criterion
  - status
  - evidence
findings:
  - severity
  - location/component
  - issue
required_correction:
  <bounded next action or none>
```

A reviewer `PASS` with missing criterion evidence is invalid and must be treated as `UNKNOWN`.

## Sol final sanity gate

Sol is the commander, but expensive deep verification should normally be delegated to the fresh Luna reviewer.

After reviewer `PASS`, Sol performs only a concise commander-level sanity check:

1. confirm the reviewer is a different worker from the executor;
2. confirm the verdict is `PASS`;
3. confirm every acceptance criterion is represented with evidence;
4. confirm there is no unresolved `BLOCKED`, `UNKNOWN`, high-severity finding, permission issue, or unverified external state;
5. then report the result to the user.

Do not make Sol reread large diffs/logs merely to duplicate the review Luna already performed. Escalate a specific uncertainty to another fresh Luna reviewer instead.

## Automatic correction loop

If independent review returns `FAIL` or a technically resolvable `UNKNOWN`:

1. extract only the failed criteria and evidence;
2. create a compact correction packet;
3. launch a fresh Luna Max correction executor automatically;
4. wait without Sol heartbeat polling;
5. after correction, launch another **fresh** Luna Max reviewer;
6. repeat until `PASS` or a genuine stop condition.

Never ask the user to manually open the correction or review session.

Never let the correction executor certify its own fix.

## Fresh worker lifecycle

Use fresh Luna context by default for:

- implementation after diagnosis;
- deployment verification;
- independent review;
- correction after failed review;
- re-review after correction;
- a newly discovered blocker;
- another audit scope.

Reuse the same Luna session only for a short direct continuation when independence is not required. The mandatory post-implementation reviewer is never eligible for same-session reuse with the executor it reviews.

A `context_compacted` event strongly favors retiring that worker for later phases.

## Compact executor handoff

Do not send fresh workers the entire old transcript.

Executor/correction packets should contain only:

```text
GOAL
<one concrete bounded outcome>

KNOWN PROOF
<validated facts that matter>

CURRENT BLOCKER / NEXT STEP
<what remains unresolved>

WORKSPACE IDENTITY
<repository, branch/worktree, folder, project metadata>

NON-NEGOTIABLE CONSTRAINTS
<architecture, safety, production, permission boundaries>

ACCEPTANCE CRITERIA
<deterministic proof required>

RELEVANT IDENTIFIERS
<commit, workflow, canary, execution, row, test ids when needed>

RETURN CONTRACT
- outcome
- root cause when relevant
- changed files/components
- tests/checks and results
- unresolved blockers
```

Luna gathers implementation context from the authorized workspace itself.

## No duplicate workers or side effects

For one bounded implementation phase, keep exactly one active executor unless deliberate parallelization was explicitly designed.

Before launching another worker:

1. confirm the previous relevant worker is terminal or intentionally abandoned;
2. preserve workspace identity;
3. distinguish executor vs reviewer roles explicitly;
4. do not duplicate production mutations, deployments, messages, canaries, or irreversible actions;
5. map any watcher/controller to the exact current worker.

A reviewer should not repeat external side effects merely to prove them when safe deterministic evidence already exists.

## Transport resolution

Before the first real Luna phase:

1. prefer a Luna-capable transport already proven in the current environment;
2. if unknown, perform one bounded capability-resolution pass;
3. validate Luna model/effort, workspace binding, distinct identity, permissions, and terminal observability;
4. do not perform implementation during route probing;
5. if one route explicitly rejects Luna, do not retry it;
6. if another supported route advertises Luna Max and preserves the workspace, switch once;
7. if no route satisfies the contract, stop with the exact limitation.

When `codex exec` is the verified transport, prefer its blocking/non-interactive behavior and machine-readable/structured outputs rather than inventing root-model polling. Preserve least-required sandbox/approval permissions.

## Windows watcher

When session-file watching is the selected transport observation mechanism:

```powershell
./scripts/watch-codex-task.ps1 -SessionFile <exact-luna-worker-session-jsonl>
```

The watcher must:

- observe only the exact Luna worker;
- start at current EOF by default;
- ignore historical completion events;
- make no model calls;
- emit bounded terminal status only.

Local file polling is process work, not an LLM heartbeat.

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

Preserve existing production, security, approval, tenant, trust, provider, and financial boundaries.

A failed external canary stops blind retries, not necessarily the overall orchestration.

Ask the user only for a genuinely new permission, credential, business, financial, irreversible-production, or product decision not covered by the original goal.

## Cost-efficiency policy

This skill does not promise a fixed savings percentage.

It targets avoidable premium-model work by enforcing:

- no recurring Sol heartbeat polling;
- blocking/local-process waiting;
- no Sol deep implementation work;
- no Sol duplicate deep review when a fresh Luna reviewer can verify;
- independent Luna review instead of trusting executor self-report;
- fresh Luna context for correction/re-review;
- compact packets instead of transcript replay;
- one verified Luna transport instead of repeated probes;
- no silent model substitution;
- no duplicate executor work;
- no premature success that causes expensive recovery later.

## User experience

The desired experience is:

```text
user → Sol commander
     → Luna Max executor
     → non-LLM wait
     → different fresh Luna Max reviewer
     → if needed: fresh Luna fixer → fresh Luna reviewer
     → Sol final sanity gate
     → final result
```

From the user's point of view this remains one Sol conversation. Worker lifecycle is internal.

## Project identity

Independent community repository:

https://github.com/twillio-ai/sol-luna-max-codex-orchestrator

This is not an official OpenAI skill. OpenAI Codex and GPT model behavior can change over time.
