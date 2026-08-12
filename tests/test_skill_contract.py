import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = (ROOT / "skills" / "sol-luna-max-orchestrator" / "SKILL.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
COMMANDER = (ROOT / "examples" / "commander-prompt.md").read_text(encoding="utf-8")
LLMS = (ROOT / "llms.txt").read_text(encoding="utf-8")
CONTROLLER = (ROOT / "scripts" / "run_luna_cycle.py").read_text(encoding="utf-8")


class SkillContractTests(unittest.TestCase):
    def test_executor_self_report_is_not_success(self):
        self.assertIn("Executor completion is only a claim", SKILL)
        self.assertIn("Sol must never announce success from the executor report alone", SKILL)
        self.assertIn("Luna executor says done ≠ done", README)

    def test_independent_fresh_luna_review_is_mandatory(self):
        self.assertIn("Mandatory independent review gate", SKILL)
        self.assertIn("different fresh Luna", SKILL.lower())
        self.assertIn("Never let the executor certify its own work", SKILL)
        self.assertIn("Never let the fixer certify its own correction", SKILL)

    def test_no_success_before_pass(self):
        self.assertIn("Sol cannot celebrate early", SKILL)
        self.assertIn("only after the controller returns `PASS`", SKILL)
        self.assertIn("downgrade an internally inconsistent `PASS` to `UNKNOWN`", SKILL)

    def test_zero_intermediate_sol_wake_is_hard_contract(self):
        self.assertIn("There is **no root-model routing wake fallback**", SKILL)
        self.assertIn("Sol never wakes between Luna stages", SKILL)
        self.assertIn("No Sol turn occurs at steps 2–7", SKILL)
        self.assertIn("There is no fallback Sol routing wake", COMMANDER)
        self.assertIn("Zero Sol routing wakes between Luna stages", README)
        self.assertIn("There is no intermediate Sol routing-wake fallback", LLMS)

    def test_heartbeat_polling_is_forbidden(self):
        self.assertIn("No heartbeat polling by any LLM", SKILL)
        self.assertIn("Never use recurring `wait_thread`, `wait_agent`", SKILL)
        self.assertIn("Zero recurring Sol heartbeat turns", README)

    def test_failed_review_continues_automatically_without_sol(self):
        self.assertIn("Automatic correction loop", SKILL)
        self.assertIn("The user is never asked to manage that loop", SKILL)
        self.assertIn("Sol is never awakened to route that loop", SKILL)
        self.assertIn("Never wake Sol to route this loop", COMMANDER)

    def test_user_never_manages_workers(self):
        self.assertIn("User never orchestrates workers", SKILL)
        self.assertIn("Worker lifecycle is internal", SKILL)
        self.assertIn("Do not ask me to manually open, resume, check, review, fix", COMMANDER)

    def test_controller_is_required_and_cost_bounded(self):
        self.assertIn("scripts/run_luna_cycle.py", SKILL)
        self.assertIn("bounded default cycle limit", SKILL.lower())
        self.assertIn("DEFAULT_MAX_CYCLES = 3", CONTROLLER)
        self.assertIn("agents.enabled=false", CONTROLLER)
        self.assertIn('DEFAULT_MODEL = "gpt-5.6-luna"', CONTROLLER)
        self.assertIn('DEFAULT_REASONING_EFFORT = "max"', CONTROLLER)

    def test_copy_ready_prompt_cannot_restore_old_behavior(self):
        self.assertIn("ZERO-WAKE RULE", COMMANDER)
        self.assertIn("HARD SUCCESS RULE", COMMANDER)
        self.assertIn("DIFFERENT fresh Luna Max reviewer", COMMANDER)
        self.assertIn("AUTOMATIC CORRECTION LOOP", COMMANDER)
        self.assertIn("Never let a correction executor certify its own fix", COMMANDER)
        self.assertNotIn("one terminal-boundary Sol routing wake only", COMMANDER)


if __name__ == "__main__":
    unittest.main()
