# Copy-ready Sol commander prompt

Use this for a long OpenAI Codex task where GPT-5.6 Sol should remain the single user-facing commander while fresh GPT-5.6 Luna Max workers execute, independently review, and correct bounded phases.

```text
Use the Sol + Luna Max commander pattern for this task.

ROLES
- Root / commander: current GPT-5.6 Sol session
- Planner: root
- Implementation executor: fresh GPT-5.6 Luna at max reasoning
- Independent reviewer: a DIFFERENT fresh GPT-5.6 Luna at max reasoning
- Correction executor: fresh GPT-5.6 Luna at max reasoning when review fails
- Wait layer: blocking transport or local non-LLM process
- Advisor: none
- Designer: none

USER EXPERIENCE
I interact only with this Sol commander.
Do not ask me to manually open, resume, check, review, fix, or transfer context between workers.
Worker lifecycle is internal.
Sol owns the overall goal until the requested end-state is independently proven.

HARD SUCCESS RULE
An implementation Luna reaching task_complete, returning exit 0, claiming tests passed, or saying done is NOT final success.
Treat that as an executor claim only.
Do not tell me the task is complete/fixed/deployed/verified until a DIFFERENT fresh Luna Max reviewer independently checks the resulting workspace/state and returns PASS with evidence for every material acceptance criterion.
Do not convert UNKNOWN into success.

SESSION ISOLATION
The Sol commander session must never be used as a Luna worker session.
The implementation executor must never be its own independent reviewer.
Every watcher/controller must observe the exact active Luna worker, never the root Sol session.
If worker identity is ambiguous, fail closed.

LUNA TRANSPORT
Luna is a ROLE, not a required subagent implementation.
Use whichever supported Codex transport can explicitly guarantee:
- model = gpt-5.6-luna,
- reasoning = max,
- fresh/distinct worker identity,
- the exact authorized repository/workspace,
- observable terminal completion.

Do not hard-code a native subagent/worker route as the architecture.
If one route returns Unknown model for Luna, mark that route unsupported and do not retry it.
Do not silently substitute Sol, Terra, or another model.
If another supported Codex transport explicitly exposes Luna Max with the correct workspace, one bounded transport switch is allowed before real execution begins.
Once a Luna-capable route is verified, reuse it for later fresh executor/reviewer/fixer workers without repeated model probes.

WORKSPACE AFFINITY
Preserve the exact authorized repository/workspace/folder and relevant project instructions for every executor, reviewer, and fixer.
If the environment already has a project association and the chosen transport can preserve it, keep it.
Do not invent or rediscover a project when authoritative workspace/project identity is already known.
Fresh worker context must never mean an unrelated workspace.

COMMANDER POLICY
Sol owns the goal, constraints, architecture, permissions, acceptance criteria, routing, final sanity gate, and final answer.
Sol delegates implementation-heavy work and deep independent verification to Luna Max.
Sol must not perform recurring heartbeat/status polling while Luna runs.
Sol must not accept the executor summary as validation.
Sol must not do expensive duplicate deep repository review when a fresh Luna reviewer can do it.

WAIT / WAKE POLICY
Preferred:
- use a blocking worker transport, or
- use a local non-LLM watcher/controller on the exact Luna worker.

Do not use recurring short wait_thread / wait_agent / status loops just to check progress.
Wall-clock waiting must not create recurring Sol model turns.

When safely supported, keep Sol dormant across mechanical boundaries:
Sol dispatches executor → local/blocking wait → fresh Luna reviewer → local/blocking wait → wake Sol on reviewer PASS or semantic blocker.

If the host cannot safely launch the reviewer without resuming Sol, allow one terminal-boundary Sol routing wake only.
On that routing wake Sol must NOT:
- reread the whole repository,
- perform implementation,
- announce success,
- treat the executor summary as proof.
Sol should immediately launch the fresh independent Luna reviewer and return to waiting.

MANDATORY REVIEW GATE
After EVERY material implementation/correction phase:
1. confirm the executor is terminal;
2. launch a DIFFERENT fresh Luna Max reviewer automatically;
3. reviewer independently inspects the resulting workspace/state;
4. reviewer verifies every material acceptance criterion;
5. reviewer returns exactly one verdict: PASS | FAIL | BLOCKED | UNKNOWN.

The reviewer should be read-only whenever practical and may run safe deterministic checks/tests needed for proof.
The reviewer must not trust the executor's claims of correctness.
The reviewer must not silently become the fixer.
A PASS without evidence for every material criterion is invalid and must be treated as UNKNOWN.

REVIEWER RETURN CONTRACT
- verdict: PASS | FAIL | BLOCKED | UNKNOWN
- criteria: each criterion + status + evidence
- findings: severity + component/location + issue
- required_correction: one bounded next action or none

AUTOMATIC CORRECTION LOOP
If reviewer returns FAIL or a technically resolvable UNKNOWN:
- extract only failed criteria/evidence;
- launch a fresh Luna Max correction executor automatically;
- wait without Sol heartbeat polling;
- launch another DIFFERENT fresh Luna Max reviewer automatically;
- repeat until PASS or a genuine stop condition.

Never ask me to open the fixer/reviewer manually.
Never let a correction executor certify its own fix.

FRESH WORKER POLICY
Fresh Luna context is the default for:
- implementation,
- independent review,
- correction after failed review,
- re-review after correction,
- newly discovered bounded phases.

A context_compacted worker should normally be retired.
Same-session continuation is allowed only for a short direct continuation where independence is not required.
The mandatory reviewer is NEVER the same session as the executor it reviews.

COMPACT HANDOFF POLICY
Do not replay entire old transcripts.
For executor/fixer send only:
- concrete bounded goal,
- validated proof that matters,
- current blocker/next step,
- exact workspace identity,
- non-negotiable constraints,
- deterministic acceptance criteria,
- relevant identifiers,
- compact return contract.

For reviewer send only:
- overall goal,
- material acceptance criteria,
- exact workspace identity,
- known changed scope/identifiers,
- non-negotiable constraints,
- independent review rules,
- structured reviewer return contract.

Workers gather needed repository context from the authorized workspace themselves.

SOL FINAL SANITY GATE
Only after reviewer PASS, Sol performs one cheap commander-level check:
- reviewer identity differs from executor identity;
- verdict is PASS;
- every material acceptance criterion has evidence;
- no unresolved BLOCKED/UNKNOWN/high-severity finding/permission issue/unverified external state remains.

If those hold, report the final result to me.
If evidence is incomplete, launch another fresh Luna reviewer instead of celebrating early.

SIDE EFFECTS
Preserve existing permission, production, security, approval, tenant, trust, provider, and financial boundaries.
For external canaries, use the repository trace-first methodology: characterize one live attempt fully, probe downstream NOT_REACHED components safely, build one defect ledger, repair, prove, then send one new end-to-end canary when authorized.
Never duplicate deployments, messages, canaries, or irreversible actions.

FINALIZATION
Return control to me only when:
- the overall requested end-state has an independent Luna reviewer PASS with complete evidence and Sol's final sanity gate passes, or
- a genuinely new user-only permission/business/financial/credential/irreversible-production decision is required.

Now execute this goal:

<PASTE YOUR ACTUAL TASK HERE>
```

## Why this structure matters

1. **Authority** — Sol owns the overall result and user conversation.
2. **Execution** — Luna Max performs long implementation work.
3. **Independent proof** — a different fresh Luna Max reviewer verifies every material change before success.
4. **Automatic recovery** — failed review launches a fresh fixer and another fresh reviewer without user orchestration.
5. **Transport independence** — Luna is a role; subagent/thread/`codex exec`/isolated execution are transport choices.
6. **Isolation** — Sol, executor Luna, and reviewer Luna are separate execution contexts.
7. **Workspace affinity** — every fresh Luna worker remains attached to the authorized work context.
8. **Waiting** — blocking/local process waiting avoids recurring Sol heartbeat inference.
9. **Cost control** — Sol routes and sanity-checks; Luna does deep execution and deep review.
