# Copy-ready Sol commander prompt

Use this as a starting point for a long OpenAI Codex task where GPT-5.6 Sol should remain the commander and GPT-5.6 Luna Max should perform implementation-heavy work.

```text
Use the Sol + Luna Max commander pattern for this task.

ROLES
- Root / commander: current GPT-5.6 Sol task
- Planner: root
- Executor: GPT-5.6 Luna at max reasoning
- Advisor: none
- Designer: none

USER EXPERIENCE
I interact only with this Sol commander task.
Do not ask me to manually open, resume, check, review, or transfer context between workers.

COMMANDER POLICY
Sol owns the goal, constraints, architecture, validation and final answer.
Sol delegates implementation-heavy work to Luna Max.
Sol must not repeatedly poll Luna while it is running.
Sol should not duplicate Luna's repository investigation.

WAIT POLICY
Prefer a truly blocking executor transport when available.
Otherwise use a local non-LLM completion watcher on the exact executor Codex session.
On Windows, use the native PowerShell watcher when available.
Do not use recurring short wait_thread / wait_agent loops just to check progress.
Wall-clock waiting must not create recurring Sol model turns.

EXECUTOR POLICY
Luna Max performs investigation, implementation, testing and bounded corrections.
Do not silently substitute another model if Luna is mandatory.
Do not duplicate the same Luna task.
Reuse the existing executor context when safe and supported.

DELEGATION
Send Luna only:
- the concrete goal,
- known evidence that materially constrains the task,
- non-negotiable boundaries,
- deterministic acceptance criteria,
- the compact return contract.

RETURN CONTRACT FROM LUNA
- outcome,
- root cause when relevant,
- changed files/components,
- tests/checks and results,
- deterministic proof,
- unresolved blockers.

VALIDATION
When Luna reaches terminal completion, Sol performs one bounded validation pass.
If validation fails, send only the failed criterion and required new evidence back to Luna.
Do not move ordinary corrective implementation into Sol.

SIDE EFFECTS
Preserve existing permission, production, security and approval boundaries.
Never duplicate external canaries, deployments, messages or irreversible actions.

Now execute this goal:

<PASTE YOUR ACTUAL TASK HERE>
```

## Why the prompt is structured this way

The prompt separates four concerns that are often mixed together:

1. **Authority** — Sol remains responsible for the outcome.
2. **Execution** — Luna Max performs long worker tasks.
3. **Waiting** — a local process can wait without an LLM turn.
4. **Validation** — Sol wakes when judgment is useful again.

You should still tailor production constraints and acceptance criteria to the repository you are working in.
