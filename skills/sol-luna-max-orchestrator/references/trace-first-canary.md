# Trace-first canary methodology

Use this reference when a bounded live canary crosses multiple integration layers such as browser input, inbound transport, intent classification, tool planning, internal receipts, approval, resume, outbound persistence, provider submission, provider receipts, and final user-visible delivery.

## Goal

A live canary should maximize diagnostic information per external side effect.

Do not repair the first observed defect while the same canary is still being characterized. First freeze the attempt, correlate its identifiers, and build a complete evidence map. Then repair from that map.

The method is:

```text
ONE live canary
→ freeze/correlate attempt
→ trace every layer
→ mark PASS / FAIL / BLOCKED / NOT_REACHED / UNKNOWN
→ side-effect-free probes for downstream NOT_REACHED layers
→ defect ledger
→ bounded repair batch
→ deterministic proof
→ deploy/parity
→ ONE new end-to-end canary
```

## Before sending the canary

Record a bounded pre-state snapshot and define one correlation identity for the attempt. Capture only identifiers needed to follow the request safely.

Define the expected chain explicitly, for example:

```text
browser/user request
→ inbound message
→ intent/classifier
→ tool plan
→ search/read tool
→ trusted internal receipt
→ approval if required
→ resume/dispatcher
→ send tool
→ outbound row
→ provider submission
→ provider receipt/event
→ visible delivered artifact
```

For each layer define what evidence would prove PASS before the canary starts.

## During the live canary

Send exactly the bounded external action authorized by the user.

Do not send retries while the attempt is unresolved.

Follow the same attempt to terminal or reconciled state using its correlation identifiers. If an expected approval is part of the real production contract and the user's original authorization covers it, use only the authoritative approval path; do not bypass it with direct database state edits.

Do not begin source-code repair in the middle of the trace unless continuing the current attempt would create an unsafe or irreversible effect.

## Evidence matrix

Every expected layer receives exactly one status:

- `PASS`: the live canary produced the expected real evidence at this layer.
- `FAIL`: the live canary reached this layer and produced a concrete incorrect terminal result.
- `BLOCKED`: the layer was reached but correctly stopped by an explicit policy/approval/permission boundary.
- `NOT_REACHED`: an earlier layer prevented this canary from reaching the layer.
- `UNKNOWN`: evidence is insufficient or conflicting; do not infer success.

Never convert `NOT_REACHED` into `PASS` merely because a component works in isolation.

## Downstream probing after a failed live canary

If the live canary fails before later layers, inspect those later layers without sending another external request when safe.

Use rollback-only, synthetic, owner-scoped, dry-run, mocked-provider, or other side-effect-free component probes already allowed by the repository.

Record those results separately as `COMPONENT_PASS` / `COMPONENT_FAIL`; they do not upgrade the original live canary's `NOT_REACHED` status.

Examples:

- if tool planning fails, exercise the send tool with a trusted synthetic receipt inside rollback-only state;
- if outbound enqueue fails, validate provider serialization without submitting to the provider;
- if provider submission is not reached, inspect the adapter and receipt contract using the repository's deterministic harness;
- if browser delivery is not reached, verify browser/session readiness without sending a second message.

The purpose is to discover latent downstream defects in the same diagnostic cycle.

## Defect ledger

After the trace and component probes, produce one bounded defect ledger:

```text
Layer | Live status | Component status | Evidence | Root cause | Fix required
```

Group defects that can be corrected safely in one bounded implementation phase. Do not create one external canary per defect.

## Repair phase

Start a fresh Luna Max executor for the repair phase unless the narrow same-thread correction exception in the main skill applies.

For each confirmed defect:

1. identify the exact violated contract;
2. apply the smallest correct change;
3. add regression coverage;
4. prove the changed layer deterministically without external side effects;
5. run targeted validation plus repository-required checks;
6. commit/push/deploy through the established path;
7. verify source/release/runtime parity.

Do not weaken trust, approval, tenant, receipt, or provider boundaries to make a canary pass.

## New live proof

Only after the repair batch is deterministically proven and deployed should Sol authorize one new end-to-end canary when the user's original authorization covers it.

The new canary must be a fresh correlated attempt and must prove the complete chain. If it fails, repeat the trace-first cycle. Do not blindly resend.

## Reporting

The commander should keep an internal evidence ledger during the workflow and return compactly at the end:

- final live chain statuses and identifiers;
- all confirmed defects discovered in the cycle;
- fixes and regression proof;
- deployment/parity state;
- final external proof result;
- any genuinely unresolved boundary.

This method optimizes for fewer external retries and more information per canary, not for pretending one failed attempt reached downstream layers that it did not reach.
