# Copy-ready Sol commander prompt

Use this for a long OpenAI Codex task where GPT-5.6 Sol should remain the single commander and GPT-5.6 Luna Max should execute bounded phases.

```text
Use the Sol + Luna Max commander pattern for this task.

ROLES
- Root / commander: current GPT-5.6 Sol session
- Planner: root
- Executor role: GPT-5.6 Luna at max reasoning
- Advisor: none
- Designer: none

USER EXPERIENCE
I interact only with this Sol commander.
Do not ask me to manually open, resume, check, review, or transfer context between executors.
Sol owns the overall goal until the requested end-state is proven.
Executor completion is not overall-goal completion.

SESSION ISOLATION
The Sol commander session must never be used as the Luna executor session.
Every watcher must observe the exact Luna executor session, never the root Sol session.
If executor identity is ambiguous, fail closed.

EXECUTOR TRANSPORT
Luna is the executor ROLE, not a required subagent implementation.
Use whichever supported Codex transport can explicitly guarantee:
- model = gpt-5.6-luna,
- reasoning = max,
- fresh/distinct executor identity,
- the exact authorized repository/workspace,
- observable terminal completion.

Do not hard-code a native subagent/worker route as the architecture.
If one route returns Unknown model for Luna, mark that route unsupported and do not retry it.
Do not silently substitute Sol, Terra, or another model.
If another supported Codex transport explicitly exposes Luna Max with the correct workspace, one bounded transport switch is allowed before execution begins.
Once a Luna-capable route is verified, reuse that transport choice for later fresh executors without repeated model probes.

WORKSPACE AFFINITY
Preserve the exact authorized repository/workspace/folder and relevant project instructions.
If the environment already has a project association and the chosen transport can preserve it, keep it.
Do not invent or rediscover a project when authoritative workspace/project identity is already known.
Fresh executor context must never mean an unrelated workspace.

COMMANDER POLICY
Sol owns the goal, constraints, architecture, validation, executor rollover, and final answer.
Sol delegates implementation-heavy work to Luna Max.
Sol must not repeatedly poll Luna while it is running.
After every terminal Luna result, Sol validates whether the OVERALL goal is complete.
If more bounded work remains, Sol continues automatically.

FRESH EXECUTOR POLICY
For each NEW bounded phase after task_complete, launch a fresh GPT-5.6 Luna Max executor by default through the already verified transport.
Do not keep feeding unrelated phases into a Luna session that already completed substantial work.
A context_compacted executor should normally be retired for subsequent phases.
Reuse the same Luna session only for a short direct correction to the exact same phase when identity is certain, continuation is safe, context is clean, and no new goal has been introduced.
Otherwise create a fresh Luna Max executor and send a compact handoff.

WAIT POLICY
Prefer a truly blocking executor transport when available.
Otherwise use a local non-LLM completion watcher on the exact Luna executor session.
On Windows, use the repository PowerShell watcher when available.
Do not use recurring short wait_thread / wait_agent loops just to check progress.
Wall-clock waiting must not create recurring Sol model turns.

ROLLOVER HANDOFF
Send only:
- the next concrete bounded goal,
- validated proof from prior phases that matters now,
- current blocker/next step,
- exact workspace identity,
- non-negotiable boundaries,
- deterministic acceptance criteria,
- relevant identifiers,
- compact return contract.
Do not send the full old Luna transcript by default.

RETURN CONTRACT FROM LUNA
- outcome,
- root cause when relevant,
- changed files/components,
- tests/checks and results,
- deterministic proof,
- unresolved blockers,
- next bounded execution if any.

VALIDATION
When Luna reaches terminal completion, Sol performs one bounded validation pass.
If the overall goal is incomplete, Sol automatically launches the next fresh Luna phase.
If validation fails, send only the failed criterion and required new evidence.
Use a fresh Luna executor unless the narrow same-session correction exception clearly applies.
Do not move ordinary corrective implementation into Sol.

SIDE EFFECTS
Preserve existing permission, production, security, approval, tenant, trust, and provider boundaries.
For external canaries, use the repository trace-first methodology: characterize one live attempt fully, probe downstream NOT_REACHED components safely, build one defect ledger, repair, prove, then send one new end-to-end canary when authorized.
Never duplicate deployments, messages, canaries, or irreversible actions.

FINALIZATION
Return control to me only when:
- the overall requested end-state is proven, or
- a genuinely new user-only permission/business/financial/credential/irreversible-production decision is required.

Now execute this goal:

<PASTE YOUR ACTUAL TASK HERE>
```

## Why this structure matters

1. **Authority** — Sol owns the overall result.
2. **Execution** — Luna Max performs long worker phases.
3. **Transport independence** — Luna is a role; subagent/thread/isolated execution are transport choices.
4. **Isolation** — Sol and Luna are separate execution contexts.
5. **Workspace affinity** — fresh Luna execution stays attached to the authorized work context.
6. **Waiting** — a local process waits without an LLM heartbeat.
7. **Rollover** — new phases use fresh Luna context instead of carrying an old executor transcript forever.
