#!/usr/bin/env python3
"""Run Luna Max implementation/review/correction cycles without waking Sol.

The root Sol task launches this controller once. The controller synchronously runs
fresh `codex exec` processes for implementation and independent review, repeating
correction/re-review when necessary. It returns only after PASS or a terminal
blocker/error, so no root-model heartbeat or intermediate routing turn is needed.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable


DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_REASONING_EFFORT = "max"
DEFAULT_MAX_CYCLES = 3

EXIT_PASS = 0
EXIT_BLOCKED = 20
EXIT_EXHAUSTED = 21
EXIT_TRANSPORT_ERROR = 22
EXIT_INVALID_INPUT = 23

VALID_VERDICTS = {"PASS", "FAIL", "BLOCKED", "UNKNOWN"}

EXECUTOR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": ["DONE", "BLOCKED", "FAILED"]},
        "summary": {"type": "string"},
        "changed_files": {"type": "array", "items": {"type": "string"}},
        "checks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "status": {"type": "string", "enum": ["PASS", "FAIL", "BLOCKED", "NOT_RUN"]},
                    "evidence": {"type": "string"},
                },
                "required": ["name", "status", "evidence"],
                "additionalProperties": False,
            },
        },
        "blockers": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["outcome", "summary", "changed_files", "checks", "blockers"],
    "additionalProperties": False,
}

REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL", "BLOCKED", "UNKNOWN"]},
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion": {"type": "string"},
                    "status": {"type": "string", "enum": ["PASS", "FAIL", "BLOCKED", "UNKNOWN"]},
                    "evidence": {"type": "string"},
                },
                "required": ["criterion", "status", "evidence"],
                "additionalProperties": False,
            },
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
                    "location": {"type": "string"},
                    "issue": {"type": "string"},
                },
                "required": ["severity", "location", "issue"],
                "additionalProperties": False,
            },
        },
        "required_correction": {"type": "string"},
    },
    "required": ["verdict", "criteria", "findings", "required_correction"],
    "additionalProperties": False,
}


class ControllerError(RuntimeError):
    pass


Runner = Callable[[str, str, pathlib.Path, dict[str, Any]], dict[str, Any]]


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def load_packet(path: str) -> dict[str, Any]:
    raw = sys.stdin.read() if path == "-" else pathlib.Path(path).read_text(encoding="utf-8")
    try:
        packet = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ControllerError(f"invalid packet JSON: {exc}") from exc

    if not isinstance(packet, dict):
        raise ControllerError("packet must be a JSON object")

    goal = packet.get("goal")
    criteria = packet.get("acceptance_criteria")
    if not isinstance(goal, str) or not goal.strip():
        raise ControllerError("packet.goal must be a non-empty string")
    if not isinstance(criteria, list) or not criteria or not all(isinstance(x, str) and x.strip() for x in criteria):
        raise ControllerError("packet.acceptance_criteria must be a non-empty array of strings")

    constraints = packet.get("constraints", [])
    if not isinstance(constraints, list) or not all(isinstance(x, str) for x in constraints):
        raise ControllerError("packet.constraints must be an array of strings")

    context = packet.get("context", "")
    if not isinstance(context, str):
        raise ControllerError("packet.context must be a string when supplied")

    return {
        "goal": goal.strip(),
        "acceptance_criteria": [x.strip() for x in criteria],
        "constraints": constraints,
        "context": context.strip(),
    }


def resolve_codex_binary(value: str) -> str:
    candidate = pathlib.Path(value)
    if candidate.is_absolute() or candidate.parent != pathlib.Path("."):
        if not candidate.exists():
            raise ControllerError(f"Codex binary not found: {value}")
        return str(candidate.resolve())
    resolved = shutil.which(value)
    if not resolved:
        raise ControllerError(f"Codex binary not found on PATH: {value}")
    return resolved


def build_codex_command(
    codex_bin: str,
    workspace: pathlib.Path,
    model: str,
    reasoning_effort: str,
    sandbox: str,
    schema_path: pathlib.Path,
    output_path: pathlib.Path,
) -> list[str]:
    # Every invocation is a fresh non-interactive Luna process. Multi-agent tools
    # are disabled inside the worker so the controller owns all fan-out/cost.
    return [
        codex_bin,
        "exec",
        "--ephemeral",
        "--cd",
        str(workspace),
        "--model",
        model,
        "--sandbox",
        sandbox,
        "--config",
        f'model_reasoning_effort="{reasoning_effort}"',
        "--config",
        "agents.enabled=false",
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(output_path),
        "-",
    ]


def make_codex_runner(
    *,
    codex_bin: str,
    workspace: pathlib.Path,
    model: str,
    reasoning_effort: str,
    executor_sandbox: str,
    reviewer_sandbox: str,
    temp_dir: pathlib.Path,
) -> Runner:
    counter = 0

    def run(role: str, prompt: str, _workspace: pathlib.Path, schema: dict[str, Any]) -> dict[str, Any]:
        nonlocal counter
        counter += 1
        if _workspace != workspace:
            raise ControllerError("worker workspace changed unexpectedly")

        schema_path = temp_dir / f"{counter:02d}-{role}-schema.json"
        output_path = temp_dir / f"{counter:02d}-{role}-result.json"
        schema_path.write_text(_json_text(schema), encoding="utf-8")

        sandbox = reviewer_sandbox if role == "reviewer" else executor_sandbox
        command = build_codex_command(
            codex_bin=codex_bin,
            workspace=workspace,
            model=model,
            reasoning_effort=reasoning_effort,
            sandbox=sandbox,
            schema_path=schema_path,
            output_path=output_path,
        )

        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(workspace),
            check=False,
        )
        if completed.returncode != 0:
            tail = completed.stderr[-4000:].strip()
            raise ControllerError(
                f"{role} Luna transport failed with exit {completed.returncode}: {tail or 'no stderr'}"
            )
        if not output_path.exists():
            raise ControllerError(f"{role} Luna returned no structured final output")

        try:
            result = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ControllerError(f"{role} Luna returned invalid JSON: {exc}") from exc
        if not isinstance(result, dict):
            raise ControllerError(f"{role} Luna final output must be a JSON object")
        return result

    return run


def executor_prompt(packet: dict[str, Any], correction: dict[str, Any] | None = None) -> str:
    correction_section = ""
    if correction is not None:
        correction_section = f"""
INDEPENDENT REVIEW FAILURE TO CORRECT
{_json_text(correction)}

Correct only what is required to satisfy the failed/unknown criteria. Re-inspect the workspace yourself; do not assume the reviewer suggested the right implementation.
"""

    return f"""You are the implementation worker in a Sol→Luna orchestration cycle.
You are GPT-5.6 Luna and must execute this bounded task in the current authorized workspace.
Do not spawn subagents or ask the user to manage another session.
Inspect the repository/workspace yourself. Implement, test, and verify the requested work within the existing permission boundaries.
Do not claim success without concrete checks. Return only the structured result required by the output schema.

GOAL
{packet['goal']}

ACCEPTANCE CRITERIA
{_json_text(packet['acceptance_criteria'])}

NON-NEGOTIABLE CONSTRAINTS
{_json_text(packet['constraints'])}

OPTIONAL CONTEXT
{packet['context'] or '(none)'}
{correction_section}
"""


def reviewer_prompt(packet: dict[str, Any], executor_result: dict[str, Any]) -> str:
    return f"""You are the mandatory INDEPENDENT reviewer in a Sol→Luna orchestration cycle.
You are a fresh GPT-5.6 Luna context, distinct from the implementation worker.
Independently inspect the resulting authorized workspace/state. Do NOT trust the executor summary as proof.
Do not edit implementation code. Use safe deterministic verification available in the current sandbox.
Copy every acceptance criterion EXACTLY into your criteria array and provide evidence for each one.
Return PASS only when every criterion is independently proven and no unresolved high/critical issue remains.
If evidence is insufficient, return UNKNOWN. If a real external/user-only prerequisite blocks proof, return BLOCKED. If work is wrong or incomplete, return FAIL.
Return only the structured result required by the output schema.

OVERALL GOAL
{packet['goal']}

ACCEPTANCE CRITERIA
{_json_text(packet['acceptance_criteria'])}

NON-NEGOTIABLE CONSTRAINTS
{_json_text(packet['constraints'])}

EXECUTOR-DECLARED SCOPE (CONTEXT ONLY; NOT PROOF)
{_json_text(executor_result)}
"""


def normalize_review(review: dict[str, Any], expected_criteria: list[str]) -> dict[str, Any]:
    normalized = dict(review)
    verdict = normalized.get("verdict")
    criteria = normalized.get("criteria")
    findings = normalized.get("findings")

    if verdict not in VALID_VERDICTS or not isinstance(criteria, list) or not isinstance(findings, list):
        raise ControllerError("reviewer output does not match the required semantic contract")

    seen: dict[str, dict[str, Any]] = {}
    for item in criteria:
        if isinstance(item, dict) and isinstance(item.get("criterion"), str):
            seen[item["criterion"]] = item

    contract_problems: list[str] = []
    for criterion in expected_criteria:
        item = seen.get(criterion)
        if item is None:
            contract_problems.append(f"missing criterion evidence: {criterion}")
        elif item.get("status") != "PASS" and verdict == "PASS":
            contract_problems.append(f"PASS verdict conflicts with criterion status: {criterion}")
        elif not isinstance(item.get("evidence"), str) or not item.get("evidence", "").strip():
            contract_problems.append(f"empty criterion evidence: {criterion}")

    extras = [key for key in seen if key not in expected_criteria]
    if extras:
        contract_problems.append(f"reviewer changed acceptance criteria: {extras}")

    severe = [
        f for f in findings
        if isinstance(f, dict) and f.get("severity") in {"critical", "high"}
    ]
    if verdict == "PASS" and severe:
        contract_problems.append("PASS verdict conflicts with unresolved high/critical findings")

    if contract_problems:
        normalized["verdict"] = "UNKNOWN"
        normalized["findings"] = list(findings) + [
            {"severity": "high", "location": "review-contract", "issue": problem}
            for problem in contract_problems
        ]
        normalized["required_correction"] = (
            normalized.get("required_correction") or "Repeat independent review with complete criterion evidence."
        )

    return normalized


def orchestrate(
    packet: dict[str, Any],
    workspace: pathlib.Path,
    runner: Runner,
    max_cycles: int,
) -> dict[str, Any]:
    if max_cycles < 1:
        raise ControllerError("max_cycles must be >= 1")

    history: list[dict[str, Any]] = []
    correction: dict[str, Any] | None = None

    for cycle in range(1, max_cycles + 1):
        role = "executor" if cycle == 1 else "correction"
        execution = runner(role, executor_prompt(packet, correction), workspace, EXECUTOR_SCHEMA)
        review_raw = runner("reviewer", reviewer_prompt(packet, execution), workspace, REVIEW_SCHEMA)
        review = normalize_review(review_raw, packet["acceptance_criteria"])

        history.append({
            "cycle": cycle,
            "execution": execution,
            "review": review,
        })

        verdict = review["verdict"]
        if verdict == "PASS":
            return {
                "status": "PASS",
                "cycles": cycle,
                "review": review,
                "last_execution": execution,
            }
        if verdict == "BLOCKED":
            return {
                "status": "BLOCKED",
                "cycles": cycle,
                "review": review,
                "last_execution": execution,
            }

        correction = {
            "verdict": verdict,
            "criteria": review.get("criteria", []),
            "findings": review.get("findings", []),
            "required_correction": review.get("required_correction", ""),
        }

    return {
        "status": "EXHAUSTED",
        "cycles": max_cycles,
        "review": history[-1]["review"],
        "last_execution": history[-1]["execution"],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, help="JSON packet path, or - to read JSON from stdin")
    parser.add_argument("--workspace", required=True, help="Authorized Git repository/workspace")
    parser.add_argument("--codex-bin", default="codex", help="Codex CLI executable/path")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--reasoning-effort", default=DEFAULT_REASONING_EFFORT)
    parser.add_argument("--max-cycles", type=int, default=DEFAULT_MAX_CYCLES)
    parser.add_argument(
        "--executor-sandbox",
        choices=["workspace-write", "danger-full-access"],
        default="workspace-write",
    )
    parser.add_argument(
        "--reviewer-sandbox",
        choices=["read-only", "workspace-write"],
        default="read-only",
    )
    parser.add_argument("--result-file", help="Optional path for compact terminal JSON result")
    return parser.parse_args(argv)


def emit_result(result: dict[str, Any], result_file: str | None = None) -> None:
    text = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    if result_file:
        pathlib.Path(result_file).write_text(text + "\n", encoding="utf-8")
    print(text)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        packet = load_packet(args.packet)
        workspace = pathlib.Path(args.workspace).resolve()
        if not workspace.is_dir() or not (workspace / ".git").exists():
            raise ControllerError(f"workspace is not a Git repository root: {workspace}")
        codex_bin = resolve_codex_binary(args.codex_bin)

        with tempfile.TemporaryDirectory(prefix="sol-luna-cycle-") as tmp:
            runner = make_codex_runner(
                codex_bin=codex_bin,
                workspace=workspace,
                model=args.model,
                reasoning_effort=args.reasoning_effort,
                executor_sandbox=args.executor_sandbox,
                reviewer_sandbox=args.reviewer_sandbox,
                temp_dir=pathlib.Path(tmp),
            )
            result = orchestrate(packet, workspace, runner, args.max_cycles)

        emit_result(result, args.result_file)
        if result["status"] == "PASS":
            return EXIT_PASS
        if result["status"] == "BLOCKED":
            return EXIT_BLOCKED
        return EXIT_EXHAUSTED
    except ControllerError as exc:
        emit_result({"status": "TRANSPORT_ERROR", "error": str(exc)}, args.result_file)
        return EXIT_TRANSPORT_ERROR
    except (OSError, ValueError) as exc:
        emit_result({"status": "INVALID_INPUT", "error": str(exc)}, args.result_file)
        return EXIT_INVALID_INPUT


if __name__ == "__main__":
    raise SystemExit(main())
