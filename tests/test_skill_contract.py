import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = (ROOT / "skills" / "sol-luna-max-orchestrator" / "SKILL.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


class SkillContractTests(unittest.TestCase):
    def test_executor_self_report_is_not_success(self):
        self.assertIn("Executor completion is not success", SKILL)
        self.assertIn("executor claim", SKILL)
        self.assertIn("must not repeat or paraphrase an executor's success claim", SKILL)

    def test_independent_fresh_luna_review_is_mandatory(self):
        self.assertIn("Mandatory independent Luna review gate", SKILL)
        self.assertIn("different fresh Luna Max reviewer", SKILL)
        self.assertIn("Never let the correction executor certify its own fix", SKILL)

    def test_no_success_before_pass(self):
        self.assertIn("No premature celebration", SKILL)
        self.assertIn("reviewer verdict is `PASS`", SKILL)
        self.assertIn("Never convert `UNKNOWN` into success", SKILL)

    def test_failed_review_continues_automatically(self):
        self.assertIn("Automatic correction loop", SKILL)
        self.assertIn("launch a fresh Luna Max correction executor automatically", SKILL)
        self.assertIn("launch another **fresh** Luna Max reviewer", SKILL)

    def test_root_does_not_heartbeat_poll(self):
        self.assertIn("No root-model heartbeat polling", SKILL)
        self.assertIn("Sol should wake only when semantic judgment is required, not on a timer", SKILL)
        self.assertIn("This is a routing wake, not a deep-review turn", SKILL)

    def test_user_never_manages_workers(self):
        self.assertIn("The user never orchestrates workers", SKILL)
        self.assertIn("Worker lifecycle is internal", SKILL)
        self.assertIn("The user should never have to manually say", README)

    def test_readme_matches_review_gate(self):
        self.assertIn("Luna executor says done ≠ done", README)
        self.assertIn("Mandatory independent review gate", README)
        self.assertIn("different fresh Luna Max reviewer", README)


if __name__ == "__main__":
    unittest.main()
