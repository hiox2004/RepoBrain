# tests/test_watcher.py
"""
Test Suite for RepoBrain Real-Time File Watcher Daemon.
Verifies mtime tracking, incremental Git blob SHA synchronization, and start/stop controls.
"""

import sys
import time
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.watcher import RetrieverWatcher
from repobrain.hybrid_retriever import HybridCodebaseRetriever


class TestRetrieverWatcher(unittest.TestCase):
    def setUp(self):
        self.test_root = Path("test_scratch_watcher").resolve()
        self.test_root.mkdir(parents=True, exist_ok=True)
        self.src_dir = self.test_root / "src"
        self.src_dir.mkdir(parents=True, exist_ok=True)

        self.retriever = HybridCodebaseRetriever(repo_root=self.test_root)
        self.watcher = RetrieverWatcher(
            repo_root=self.test_root,
            retriever=self.retriever,
            poll_interval_seconds=0.1,
        )

    def tearDown(self):
        self.watcher.stop()
        import shutil
        if self.test_root.exists():
            shutil.rmtree(self.test_root, ignore_errors=True)

    def test_watcher_detects_new_and_modified_files(self):
        # 1. Create a new file
        f1 = self.src_dir / "service.py"
        f1.write_text("def process_payment(amount: int):\n    return amount * 10\n", encoding="utf-8")

        synced = self.watcher.poll_once()
        self.assertIn("src/service.py", synced)
        self.assertIn("src/service.py", self.retriever.parents_db)

        # 2. Modify the file
        time.sleep(0.05)
        f1.write_text("def process_payment(amount: int):\n    return amount * 20\n", encoding="utf-8")
        synced_mod = self.watcher.poll_once()
        self.assertIn("src/service.py", synced_mod)

        # 3. No changes on immediate second poll
        synced_noop = self.watcher.poll_once()
        self.assertEqual(len(synced_noop), 0)

    def test_watcher_daemon_background_thread(self):
        self.assertFalse(self.watcher.is_running())
        self.watcher.start()
        self.assertTrue(self.watcher.is_running())

        stats = self.watcher.stats()
        self.assertTrue(stats["is_running"])
        self.assertGreaterEqual(stats["poll_interval_seconds"], 0.05)

        self.watcher.stop()
        self.assertFalse(self.watcher.is_running())


if __name__ == "__main__":
    unittest.main()
