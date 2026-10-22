# tests/test_bounded_harness.py
"""
Test Suite for Slice 3: Bounded Execution Harness, Sanctuary Guard, and Surgical Rollback.
Compatible with both pytest and python -m unittest.
"""

import sys
import unittest
from pathlib import Path

# Ensure src is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.pre_sandbox_guards import (
    BoundedHarnessState,
    SanctuaryPolicyGuard,
    extract_relevant_frames,
    fast_static_syntax_check,
    parse_diff_target_paths,
)


class TestBoundedHarness(unittest.TestCase):
    def setUp(self):
        self.test_root = Path("test_scratch_harness").resolve()
        self.test_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil
        if self.test_root.exists():
            shutil.rmtree(self.test_root)

    def test_sanctuary_policy_blocks_protected_files(self):
        guard = SanctuaryPolicyGuard(self.test_root)

        # Block lockfiles and sensitive files
        valid, err = guard.validate_paths(["uv.lock"])
        self.assertFalse(valid)
        self.assertIn("Sanctuary policy violation", err)

        valid, err = guard.validate_paths([".env"])
        self.assertFalse(valid)

        valid, err = guard.validate_paths(["pyproject.toml"])
        self.assertFalse(valid)

        # Allow normal application code
        valid, err = guard.validate_paths(["src/billing/ledger.py"])
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_sanctuary_policy_blocks_path_traversal(self):
        guard = SanctuaryPolicyGuard(self.test_root)
        valid, err = guard.validate_paths(["../../etc/passwd"])
        self.assertFalse(valid)
        self.assertIn("Path traversal attempt blocked", err)

    def test_sanctuary_protects_test_assertions_at_iteration_zero(self):
        guard = SanctuaryPolicyGuard(self.test_root)
        malicious_patch = """--- a/tests/test_ledger.py
+++ b/tests/test_ledger.py
@@ -10,1 +10,1 @@
-    assert result == Decimal('120.00')
+    pass"""
        valid, err = guard.validate_test_assertion_safety(malicious_patch, iteration=0)
        self.assertFalse(valid)
        self.assertIn("Cannot delete or weaken test assertions", err)

    def test_traceback_frame_filtering(self):
        raw_traceback = """Traceback (most recent call last):
  File "/root/env/lib/python3.10/site-packages/_pytest/runner.py", line 341, in from_call
    result = call.run()
  File "src/billing/ledger.py", line 21, in settleInvoiceById
    return req.subtotal * (Decimal("1.00") - self.tax_rate)
  File "/root/env/lib/python3.10/site-packages/fastapi/routing.py", line 12, in handle
    raise RouteError()
AssertionError: Decimal('120.0000') != Decimal('120.00')
"""
        filtered = extract_relevant_frames(raw_traceback)
        self.assertNotIn("site-packages/", filtered)
        self.assertIn("src/billing/ledger.py", filtered)
        self.assertIn("AssertionError: Decimal('120.0000') != Decimal('120.00')", filtered)

    def test_surgical_byte_rollback_preserves_unrelated_files(self):
        # Guardrail #7: Surgical rollback on Attempt 3
        harness = BoundedHarnessState(self.test_root)
        task_id = "task-surgical-test"

        # 1. Create an unrelated dirty file
        unrelated_file = self.test_root / "developer_notes.txt"
        unrelated_content = b"CRITICAL UNCOMMITTED LOCAL NOTES DO NOT DELETE"
        unrelated_file.write_bytes(unrelated_content)

        # 2. Create the target file
        target_file = self.test_root / "src" / "service.py"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        original_bytes = b"def original_fn():\n    return 42\n"
        target_file.write_bytes(original_bytes)

        # 3. Snapshot before mutation
        harness.snapshot_files_if_needed(task_id, ["src/service.py"])
        checkpoint = harness.get_or_create(task_id)

        # Attempt 1 mutation
        checkpoint.iteration = 1
        target_file.write_bytes(original_bytes + b"# Attempt 1 edit\n")

        # Attempt 2 mutation
        checkpoint.iteration = 2
        target_file.write_bytes(original_bytes + b"# Attempt 2 edit\n")

        # Attempt 3 mutation breaks file
        checkpoint.iteration = 3
        target_file.write_bytes(b"SYNTAX ERROR BROKEN BUILD")

        # 4. Trigger surgical rollback
        restored = harness.rollback_surgically(task_id)
        self.assertIn("src/service.py", restored)

        # 5. Verify target file was restored to exact pre-task bytes
        self.assertEqual(target_file.read_bytes(), original_bytes)

        # 6. Verify unrelated dirty file was 100% untouched
        self.assertTrue(unrelated_file.exists())
        self.assertEqual(unrelated_file.read_bytes(), unrelated_content)


if __name__ == "__main__":
    unittest.main()

