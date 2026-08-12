import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_luna_cycle.py"
SPEC = importlib.util.spec_from_file_location("run_luna_cycle", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class LunaCycleTests(unittest.TestCase):
    def setUp(self):
        self.packet = {
            "goal": "Implement the requested change",
            "acceptance_criteria": ["tests pass", "behavior is correct"],
            "constraints": ["do not change unrelated code"],
            "context": "",
        }
        self.workspace = pathlib.Path("/tmp/example-workspace")

    def test_codex_command_forces_luna_max_and_disables_descendants(self):
        command = MODULE.build_codex_command(
            codex_bin="codex",
            workspace=self.workspace,
            model="gpt-5.6-luna",
            reasoning_effort="max",
            sandbox="workspace-write",
            schema_path=pathlib.Path("schema.json"),
            output_path=pathlib.Path("result.json"),
        )
        self.assertEqual(command[:2], ["codex", "exec"])
        self.assertIn("--ephemeral", command)
        self.assertIn("gpt-5.6-luna", command)
        self.assertIn('model_reasoning_effort="max"', command)
        self.assertIn("agents.enabled=false", command)
        self.assertIn("--output-schema", command)
        self.assertIn("--output-last-message", command)

    def test_pass_requires_complete_exact_criterion_evidence(self):
        incomplete = {
            "verdict": "PASS",
            "criteria": [
                {"criterion": "tests pass", "status": "PASS", "evidence": "pytest passed"},
            ],
            "findings": [],
            "required_correction": "",
        }
        normalized = MODULE.normalize_review(incomplete, self.packet["acceptance_criteria"])
        self.assertEqual(normalized["verdict"], "UNKNOWN")
        self.assertTrue(any(f["location"] == "review-contract" for f in normalized["findings"]))

    def test_high_finding_invalidates_pass(self):
        review = {
            "verdict": "PASS",
            "criteria": [
                {"criterion": "tests pass", "status": "PASS", "evidence": "ok"},
                {"criterion": "behavior is correct", "status": "PASS", "evidence": "ok"},
            ],
            "findings": [
                {"severity": "high", "location": "app.py", "issue": "race condition"},
            ],
            "required_correction": "",
        }
        normalized = MODULE.normalize_review(review, self.packet["acceptance_criteria"])
        self.assertEqual(normalized["verdict"], "UNKNOWN")

    def test_fail_automatically_runs_fresh_correction_and_reviewer(self):
        calls = []
        responses = iter([
            {
                "outcome": "DONE",
                "summary": "implemented",
                "changed_files": ["a.py"],
                "checks": [],
                "blockers": [],
            },
            {
                "verdict": "FAIL",
                "criteria": [
                    {"criterion": "tests pass", "status": "FAIL", "evidence": "one failed"},
                    {"criterion": "behavior is correct", "status": "PASS", "evidence": "inspection"},
                ],
                "findings": [
                    {"severity": "high", "location": "a.py", "issue": "test failure"},
                ],
                "required_correction": "fix failing test behavior",
            },
            {
                "outcome": "DONE",
                "summary": "corrected",
                "changed_files": ["a.py"],
                "checks": [],
                "blockers": [],
            },
            {
                "verdict": "PASS",
                "criteria": [
                    {"criterion": "tests pass", "status": "PASS", "evidence": "all passed"},
                    {"criterion": "behavior is correct", "status": "PASS", "evidence": "verified"},
                ],
                "findings": [],
                "required_correction": "",
            },
        ])

        def runner(role, prompt, workspace, schema):
            calls.append((role, prompt, workspace, schema))
            return next(responses)

        result = MODULE.orchestrate(self.packet, self.workspace, runner, max_cycles=3)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["cycles"], 2)
        self.assertEqual([call[0] for call in calls], ["executor", "reviewer", "correction", "reviewer"])
        self.assertNotIn("sol", [call[0] for call in calls])
        self.assertIsNot(calls[1], calls[3])

    def test_blocked_review_returns_only_after_independent_review(self):
        calls = []
        responses = iter([
            {
                "outcome": "BLOCKED",
                "summary": "credential missing",
                "changed_files": [],
                "checks": [],
                "blockers": ["credential required"],
            },
            {
                "verdict": "BLOCKED",
                "criteria": [
                    {"criterion": "tests pass", "status": "BLOCKED", "evidence": "credential required"},
                    {"criterion": "behavior is correct", "status": "UNKNOWN", "evidence": "cannot reach service"},
                ],
                "findings": [],
                "required_correction": "obtain credential",
            },
        ])

        def runner(role, prompt, workspace, schema):
            calls.append(role)
            return next(responses)

        result = MODULE.orchestrate(self.packet, self.workspace, runner, max_cycles=3)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(calls, ["executor", "reviewer"])

    def test_exhaustion_has_bounded_cost(self):
        calls = []

        def runner(role, prompt, workspace, schema):
            calls.append(role)
            if role == "reviewer":
                return {
                    "verdict": "FAIL",
                    "criteria": [
                        {"criterion": "tests pass", "status": "FAIL", "evidence": "still failing"},
                        {"criterion": "behavior is correct", "status": "FAIL", "evidence": "still wrong"},
                    ],
                    "findings": [],
                    "required_correction": "try bounded correction",
                }
            return {
                "outcome": "DONE",
                "summary": "attempted",
                "changed_files": ["a.py"],
                "checks": [],
                "blockers": [],
            }

        result = MODULE.orchestrate(self.packet, self.workspace, runner, max_cycles=2)
        self.assertEqual(result["status"], "EXHAUSTED")
        self.assertEqual(calls, ["executor", "reviewer", "correction", "reviewer"])


if __name__ == "__main__":
    unittest.main()
