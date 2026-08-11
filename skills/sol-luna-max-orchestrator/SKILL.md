---
name: sol-luna-max-orchestrator
description: Keep the current GPT-5.6 Sol Codex task as commander, delegate implementation-heavy work to GPT-5.6 Luna at max reasoning, and avoid repeated LLM heartbeat waits by using blocking execution or a local non-LLM completion watcher.
---

# Sol + Luna Max Codex Orchestrator

Use this skill when the user wants a single Codex commander task where GPT-5.6 Sol stays responsible for planning and review while GPT-5.6 Luna Max performs long execution work.

## Core contract

The user interacts with **one commander task**.

Default roles:

```text
Root / commander: current GPT-5.6 Sol task
Planner: root
Executor: GPT-5.6 Luna at max reasoning
Advisor: none
Designer: none
Wait layer: local non-LLM process
```

The root remains the final authority for the goal, constraints, permissions, architecture, acceptance criteria, review, correction decisions, and final user-facing answer.

Do not ask the user to manually open Luna, move results between sessions, check whether the executor is finished, or start a reviewer task.

## Required control flow

```text
USER
→ SOL bounds the work
→ LUNA MAX executes
→ non-LLM process waits for terminal completion
→ SOL validates
→ accepted: final answer
→ rejected: bounded correction to LUNA MAX
→ non-LLM wait
→ SOL validates again
```

Sol may wake early only for a genuine decision blocker, terminal executor failure, required permission boundary, or a transport limitation that cannot be handled without root judgment.

Ordinary progress is not a reason to wake Sol.

## Commander responsibilities

Sol should:

1. understand the user's current goal;
2. preserve already-known evidence instead of restarting architecture discovery;
3. define one bounded executor packet;
4. delegate implementation-heavy work;
5. remain idle while the executor is running;
6. validate the compact terminal handoff;
7. send a bounded correction if a concrete acceptance criterion failed;
8. give the user the final result.

Sol should not perform implementation work that the configured Luna executor can perform safely.

## Executor responsibilities

Luna Max should perform the long worker path, including as relevant:

- repository investigation;
- code changes;
- database/query diagnosis;
- targeted tests;
- deterministic reproduction;
- browser/test-environment work already authorized by the user;
- CI/debugging work;
- corrective implementation after review.

Luna should inspect the authorized workspace itself. Do not force Sol to gather and retransmit large repository context first.

## Bounded delegation packet

Send only what Luna needs:

```text
GOAL
<one concrete outcome>

KNOWN EVIDENCE
<only facts that materially constrain the task>

NON-NEGOTIABLE CONSTRAINTS
<architecture, safety, production and permission boundaries>

ACCEPTANCE CRITERIA
<deterministic proof required before success>

RETURN CONTRACT
- outcome
- root cause when relevant
- changed files/components
- checks and results
- proof
- unresolved blockers
```

Do not duplicate full logs, full diffs, or large file contents unless a specific validation question requires them.

## Luna route

When the user explicitly requires GPT-5.6 Luna at max reasoning, the route is mandatory.

- Use the currently supported Codex transport that can actually run `gpt-5.6-luna` at `max`.
- Do not hard-code `agents.spawn_agent` if that namespace does not expose Luna in the active Codex build.
- Do not silently substitute Terra, Sol, or another executor.
- If Luna cannot launch, report the exact route/transport failure and stop unnecessary retry exploration.
- Do not burn quota repeatedly probing the same unavailable route.

A one-time tiny real Luna route verification is allowed when route callability is genuinely unknown. Once one real Luna execution succeeds in the current commander task, do not verify it again.

## No duplicate executors

For one bounded work item, keep one active Luna executor.

Before creating another worker, determine whether an existing executor can be safely continued or reused. Never duplicate a task that can mutate production, send external messages, create releases, or perform another irreversible action.

Do not let Luna spawn descendant agents for ordinary implementation work unless the user explicitly asks for parallel multi-agent execution and the commander has bounded the side effects.

## Waiting policy: no expensive heartbeat

Never use recurring short `wait_thread`, `wait_agent`, status-check, or equivalent root-model loops merely to see whether Luna is still running.

Preferred waiting order:

1. **Blocking transport:** if the executor call can block until terminal completion without recurring root turns, use it.
2. **Local event watcher:** when an executor Codex session file is available, start the repository's native watcher and let the local process wait for `task_complete`.
3. **Fail clearly:** if neither a blocking transport nor a trustworthy terminal event can be observed, report the transport limitation instead of inventing completion.

For Windows, prefer:

```powershell
./scripts/watch-codex-task.ps1 -SessionFile <exact-executor-session-jsonl>
```

The watcher must start at the current EOF by default. Reused Codex sessions can contain earlier `task_complete` records, so scanning historical completion events is unsafe for a new wait.

The watcher is not an agent. It must not call a model, make architectural decisions, modify the session, or print arbitrary session payloads.

A long local wait is acceptable. Wall-clock waiting must not itself cause recurring Sol turns.

## Root wake-up events

Wake Sol when one of these is true:

- Luna reaches terminal completion;
- Luna reaches a terminal failure;
- Luna exposes a real decision blocker that requires commander judgment;
- a permission/approval boundary requires the user or root;
- the trusted wait transport itself fails or becomes ambiguous.

Do not wake Sol for:

- “still running”;
- elapsed time alone;
- ordinary progress messages;
- repeated status checks;
- local watcher keepalive.

## Executor return contract

Prefer a compact terminal handoff:

```text
Outcome: PASS | BLOCKED | FAIL
Root cause: <bounded explanation>
Changed: <files/components>
Checks: <test/check → result>
Proof: <acceptance evidence>
Blockers: <none or exact blocker>
```

Sol should inspect additional context only where needed to validate a material claim.

## Validation and correction

Sol must review the executor's result; delegation does not mean automatic acceptance.

If the result fails validation:

- identify the exact failed acceptance criterion;
- send that bounded correction back to the existing Luna context when safe;
- do not retransmit the entire original task unless the executor lost required context;
- do not take over implementation in Sol merely because one correction is needed.

Example:

```text
Validation failed: the rollback proof bypassed the real enqueue function.
Correct only this criterion. Exercise the production-equivalent function inside a
rollback-only transaction, return the targeted test result and bounded evidence,
and do not send an external canary.
```

## Production and external side effects

Preserve the user's existing production gates and ordering.

Do not use orchestration convenience as a reason to:

- weaken validation;
- bypass trusted receipts;
- skip deterministic proof;
- send duplicate external canaries;
- bypass OAuth, access, or approval boundaries;
- silently change architecture;
- broaden the task beyond the current blocker.

If the executor can perform an already-authorized test/browser action safely, do not hand that routine coordination back to the user.

## Cost-efficiency policy

This skill does not promise a fixed cost reduction.

It minimizes avoidable root-model work by enforcing these behaviors:

- Sol does not repeatedly poll Luna;
- Sol does not duplicate Luna's repository investigation;
- Luna returns compact evidence;
- corrections contain only failed criteria and new evidence;
- passive waiting is local process work;
- mandatory Luna failures do not trigger model-shopping retries.

The measurable target is **fewer unnecessary root-model turns**, not a marketing percentage.

## User experience

The user should experience the workflow as one conversation:

```text
user → Sol commander → work happens → Sol final report
```

The user should not need to say:

```text
check Luna
resume Luna
open another Luna
copy this to Sol
review Luna
start the next worker
```

If the orchestration layer requires those manual steps for ordinary execution, it has failed this skill's UX contract.

## Final report

When the requested work is complete, Sol should report only the information that helps the user understand what happened:

- outcome;
- root cause when relevant;
- smallest correct fix;
- tests/proof;
- production/deployment result when relevant;
- remaining next action if any.

Do not expose internal orchestration chatter unless the user asks for it.

## Project identity

This skill belongs to the independent community repository:

https://github.com/twillio-ai/sol-luna-max-codex-orchestrator

It is not an official OpenAI skill. OpenAI Codex and GPT-5.6 model behavior remain controlled by OpenAI and can change over time.
