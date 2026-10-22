# tests/test_orchestrator.py
"""
Test Suite for Multi-Agent Orchestrator Runtime.
Validates the 5-Phase CoT state machine, bounded retries, episodic distillation, and surgical rollback.
Compatible with pytest and python -m unittest.
"""

import sys
import unittest
from pathlib import Path

# Ensure src is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.orchestrator import MultiAgentOrchestrator, StepEvent


class TestMultiAgentOrchestrator(unittest.TestCase):
    def setUp(self):
        self.test_root = Path("test_scratch_orch").resolve()
        self.test_root.mkdir(parents=True, exist_ok=True)

        # Create target file
        self.target_file = self.test_root / "src" / "billing" / "ledger.py"
        self.target_file.parent.mkdir(parents=True, exist_ok=True)
        self.original_code = "def settle(): return 100\n"
        self.target_file.write_text(self.original_code, encoding="utf-8")

        self.orchestrator = MultiAgentOrchestrator(repo_root=self.test_root)

    def tearDown(self):
        import shutil
        if self.test_root.exists():
            shutil.rmtree(self.test_root)

    def test_first_iteration_success(self):
        recorded_events = []
        self.orchestrator.subscribe(lambda ev: recorded_events.append(ev))

        # Synthetic test runner script that always passes
        test_script = self.test_root / "test_dummy.py"
        test_script.write_text("import sys; sys.exit(0)\n", encoding="utf-8")

        def patch_gen(iteration, goal, contexts, last_err):
            return """--- a/src/billing/ledger.py\n+++ b/src/billing/ledger.py\n@@ -1 +1 @@\n-def settle(): return 100\n+def settle(): return 120"""

        result = self.orchestrator.execute_task(
            task_id="task-first-try",
            goal_description="Fix settle return value",
            search_query="settle",
            target_file="src/billing/ledger.py",
            test_path=str(test_script),
            patch_synthesizer=patch_gen,
            max_iterations=3,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.iterations_run, 1)
        self.assertFalse(result.rolled_back)
        self.assertGreater(len(recorded_events), 3)

    def test_multi_iteration_self_healing_and_distillation(self):
        test_script = self.test_root / "test_healing.py"
        # Script fails on attempt 1, passes on attempt 2
        counter_file = self.test_root / "attempt.counter"
        counter_file.write_text("0", encoding="utf-8")

        test_code = """
import sys
from pathlib import Path
c_file = Path("attempt.counter")
val = int(c_file.read_text().strip()) + 1
c_file.write_text(str(val))
if val == 1:
    print("AssertionError: 100 != 120", file=sys.stderr)
    sys.exit(1)
else:
    sys.exit(0)
"""
        test_script.write_text(test_code, encoding="utf-8")

        def patch_gen(iteration, goal, contexts, last_err):
            if iteration == 1:
                return "--- a/src/billing/ledger.py\n+++ b/src/billing/ledger.py\n@@ -1 +1 @@\n-def settle(): return 100\n+def settle(): return 110"
            else:
                return "--- a/src/billing/ledger.py\n+++ b/src/billing/ledger.py\n@@ -1 +1 @@\n-def settle(): return 110\n+def settle(): return 120"

        # Change cwd to test_root for the test script
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(str(self.test_root))
            result = self.orchestrator.execute_task(
                task_id="task-self-heal",
                goal_description="Self healing test",
                search_query="settle",
                target_file="src/billing/ledger.py",
                test_path=str(test_script.relative_to(self.test_root)),
                patch_synthesizer=patch_gen,
                max_iterations=3,
            )
        finally:
            os.chdir(old_cwd)

        self.assertTrue(result.success)
        self.assertEqual(result.iterations_run, 2)
        # Verify episodic distillation occurred!
        self.assertIsNotNone(result.distilled_episode_id)

    def test_sanctuary_policy_guard_blocks_env(self):
        def patch_gen(iteration, goal, contexts, last_err):
            return "--- a/.env\n+++ b/.env\n@@ -1 +1 @@\n-KEY=VAL\n+KEY=HACK"

        result = self.orchestrator.execute_task(
            task_id="task-sanctuary",
            goal_description="Hack env file",
            search_query="env",
            target_file=".env",
            test_path="dummy.py",
            patch_synthesizer=patch_gen,
            max_iterations=3,
        )

        self.assertFalse(result.success)
        self.assertIn("Sanctuary policy violation", result.final_message)


if __name__ == "__main__":
    unittest.main()

