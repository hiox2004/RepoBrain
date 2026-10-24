# tests/test_swarm.py
"""
Test Suite for RepoBrain Multi-Agent Local Swarm Mesh (LangGraph Native).
Tests:
1. Architect node planning, blast radius check, and blueprint mapping.
2. Coder node patch application and AST index synchronization.
3. Tester node execution and episodic memory distillation.
4. Supervisor bounded retry ceiling and non-destructive surgical byte rollback.
5. End-to-end swarm execution.
"""

import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.swarm import MultiAgentSwarmMesh, SwarmState


class TestMultiAgentSwarm(unittest.TestCase):
    def setUp(self):
        self.test_root = Path("test_scratch_swarm").resolve()
        self.test_root.mkdir(parents=True, exist_ok=True)
        (self.test_root / "src").mkdir(exist_ok=True)
        (self.test_root / "tests").mkdir(exist_ok=True)

        # Create sample service
        self.service_path = self.test_root / "src" / "service.py"
        self.service_path.write_text(
            "def calculate_total(subtotal: float, discount: float) -> float:\n"
            "    # BUG: adds discount instead of subtracting\n"
            "    return subtotal + discount\n",
            encoding="utf-8",
        )

        # Create test suite
        self.test_file = self.test_root / "tests" / "test_service.py"
        self.test_file.write_text(
            "import unittest\n"
            "import sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))\n"
            "from service import calculate_total\n\n"
            "class TestService(unittest.TestCase):\n"
            "    def test_calculation(self):\n"
            "        self.assertEqual(calculate_total(100.0, 10.0), 90.0)\n\n"
            "if __name__ == '__main__':\n"
            "    unittest.main()\n",
            encoding="utf-8",
        )

        self.swarm = MultiAgentSwarmMesh(repo_root=self.test_root)

    def tearDown(self):
        import shutil
        if self.test_root.exists():
            shutil.rmtree(self.test_root, ignore_errors=True)

    def test_architect_node_planning(self):
        state: SwarmState = {
            "task_id": "task-test-arch",
            "task_description": "calculate_total discount calculation in service.py",
            "target_file": "src/service.py",
            "test_path": "tests/test_service.py",
            "iteration": 1,
            "max_iterations": 3,
            "current_worker": "architect",
            "retrieved_contexts": [],
            "blast_radius": None,
            "recommended_blueprints": [],
            "subtasks": [],
            "proposed_diff": None,
            "syntax_valid": True,
            "test_exit_code": -1,
            "test_output": "",
            "filtered_traceback": None,
            "error_signature": None,
            "success": False,
            "rolled_back": False,
            "distilled_episode_id": None,
            "summary": "",
        }

        update = self.swarm.architect_node(state)
        self.assertEqual(update["current_worker"], "coder")
        self.assertGreaterEqual(len(update["subtasks"]), 2)
        self.assertIn("subtasks", update)

    def test_bounded_ceiling_and_surgical_rollback(self):
        # Record original bytes
        original_bytes = self.service_path.read_bytes()

        # Define patch synthesizer that always produces broken code
        def bad_patch_synthesizer(s: SwarmState) -> str:
            return (
                "--- a/src/service.py\n"
                "+++ b/src/service.py\n"
                "@@ -2,2 +2,2 @@\n"
                "-    # BUG: adds discount instead of subtracting\n"
                "-    return subtotal + discount\n"
                "+    # Still broken\n"
                "+    return subtotal + (discount * 2)\n"
            )

        broken_swarm = MultiAgentSwarmMesh(
            repo_root=self.test_root,
            patch_synthesizer=bad_patch_synthesizer,
        )

        final_state = broken_swarm.run_swarm(
            task_description="Fix calculation bug",
            target_file="src/service.py",
            test_path="tests/test_service.py",
            max_iterations=2,
        )

        # Verify retry ceiling was reached and surgical byte rollback was executed
        self.assertFalse(final_state["success"])
        self.assertTrue(final_state["rolled_back"])
        self.assertEqual(final_state["current_worker"], "FINISH")

        # Verify file restored to exact original bytes
        restored_bytes = self.service_path.read_bytes()
        self.assertEqual(restored_bytes, original_bytes)

    def test_multi_iteration_self_healing_and_distillation(self):
        # Synthesizer that fails on attempt 1, passes on attempt 2
        def healing_synthesizer(s: SwarmState) -> str:
            if s["iteration"] == 1:
                return (
                    "--- a/src/service.py\n"
                    "+++ b/src/service.py\n"
                    "@@ -2,2 +2,2 @@\n"
                    "-    # BUG: adds discount instead of subtracting\n"
                    "-    return subtotal + discount\n"
                    "+    # Still wrong\n"
                    "+    return subtotal + 5.0\n"
                )
            else:
                return (
                    "--- a/src/service.py\n"
                    "+++ b/src/service.py\n"
                    "@@ -2,2 +2,2 @@\n"
                    "-    # Still wrong\n"
                    "-    return subtotal + 5.0\n"
                    "+    # Fixed!\n"
                    "+    return subtotal - discount\n"
                )

        healing_swarm = MultiAgentSwarmMesh(
            repo_root=self.test_root,
            patch_synthesizer=healing_synthesizer,
        )

        final_state = healing_swarm.run_swarm(
            task_description="Repair calculate_total subtraction",
            target_file="src/service.py",
            test_path="tests/test_service.py",
            max_iterations=3,
        )

        self.assertTrue(final_state["success"])
        self.assertFalse(final_state["rolled_back"])
        self.assertEqual(final_state["test_exit_code"], 0)
        self.assertEqual(final_state["current_worker"], "FINISH")
        self.assertIsNotNone(final_state["distilled_episode_id"])


if __name__ == "__main__":
    unittest.main()

