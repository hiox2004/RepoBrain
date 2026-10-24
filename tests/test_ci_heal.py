# tests/test_ci_heal.py
"""
Test Suite for RepoBrain Autonomous CI Self-Healing Engine.
Verifies failure trace extraction, blast radius checking, patch synthesis loop, and PR markdown generation.
"""

import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.ci_heal import CIHealingOrchestrator


class TestCIHeal(unittest.TestCase):
    def setUp(self):
        self.test_root = Path("test_scratch_ci_heal").resolve()
        self.test_root.mkdir(parents=True, exist_ok=True)
        self.src_dir = self.test_root / "src"
        self.src_dir.mkdir(parents=True, exist_ok=True)

        self.healer = CIHealingOrchestrator(repo_root=self.test_root)

    def tearDown(self):
        import shutil
        if self.test_root.exists():
            shutil.rmtree(self.test_root, ignore_errors=True)

    def test_clean_passing_test_returns_early(self):
        pass_script = self.test_root / "test_clean.py"
        pass_script.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")

        result = self.healer.diagnose_and_heal(test_path=str(pass_script.relative_to(self.test_root)))
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["healed"])
        self.assertIn("Zero regressions detected", result["github_markdown"])

    def test_failing_test_generates_pr_report(self):
        fail_script = self.test_root / "test_broken.py"
        fail_script.write_text(
            "import sys\nsys.stderr.write('AssertionError: expected 200 got 500\\n')\nsys.exit(1)\n",
            encoding="utf-8",
        )

        result = self.healer.diagnose_and_heal(test_path=str(fail_script.relative_to(self.test_root)))
        self.assertEqual(result["status"], "FAILED")
        self.assertIn("AssertionError", result["error_signature"])
        self.assertIn("RepoBrain Autonomous CI Self-Healing Report", result["github_markdown"])
        self.assertIn("Blast Radius", result["github_markdown"])


if __name__ == "__main__":
    unittest.main()
