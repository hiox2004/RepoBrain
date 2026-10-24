# tests/test_cli.py
"""
Test Suite for RepoBrain Unified CLI.
Tests all CLI subcommands: index, search, research, templates, episodes, verify.
Compatible with pytest and python -m unittest.
"""

import sys
import unittest
from pathlib import Path
from io import StringIO
from unittest.mock import patch

# Ensure src is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.cli import main


class TestRepoBrainCLI(unittest.TestCase):
    def test_cli_help(self):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                with patch("sys.argv", ["repobrain", "--help"]):
                    main()
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("RepoBrain V2 & ResearchBrain OS", fake_out.getvalue())

    def test_cli_templates(self):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("sys.argv", ["repobrain", "templates", "fastapi"]):
                main()
            output = fake_out.getvalue()
            self.assertIn("Searching Template Stockroom", output)
            self.assertIn("tiangolo/full-stack-fastapi-template", output)

    def test_cli_research(self):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("sys.argv", ["repobrain", "research", "FastAPI"]):
                main()
            output = fake_out.getvalue()
            self.assertIn("Executing ResearchBrain 5-Phase CRAG", output)
            self.assertIn("Confidence:", output)

    def test_cli_index_and_search(self):
        test_dir = Path("test_scratch_cli").resolve()
        test_dir.mkdir(parents=True, exist_ok=True)
        sample_file = test_dir / "calculator.py"
        sample_file.write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")

        try:
            # 1. Index
            with patch("sys.stdout", new=StringIO()) as fake_out:
                with patch("sys.argv", ["repobrain", "index", str(test_dir)]):
                    main()
                self.assertIn("Successfully indexed", fake_out.getvalue())

            # 2. Search
            with patch("sys.stdout", new=StringIO()) as fake_out:
                with patch("sys.argv", ["repobrain", "search", "add", "--repo", str(test_dir)]):
                    main()
                self.assertIn("add", fake_out.getvalue())
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir, ignore_errors=True)



    def test_cli_blast_radius(self):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("sys.argv", ["repobrain", "blast-radius", "compute_git_blob_sha"]):
                main()
            output = fake_out.getvalue()
            self.assertIn("Analyzing blast radius for symbol:", output)
            self.assertIn("compute_git_blob_sha", output)
            self.assertIn("Risk Level:", output)

    def test_cli_benchmark(self):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("sys.argv", ["repobrain", "benchmark"]):
                main()
            output = fake_out.getvalue()
            self.assertIn("benchmark_summary", output)
            self.assertIn("average_token_reduction_pct", output)

    def test_cli_watch_once(self):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("sys.argv", ["repobrain", "watch", "--once"]):
                main()
            output = fake_out.getvalue()
            self.assertIn("Starting RepoBrain File Watcher daemon", output)
            self.assertIn("Sync completed", output)

    def test_cli_heal_clean(self):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("sys.argv", ["repobrain", "heal", "tests/test_ast_chunker.py"]):
                main()
            output = fake_out.getvalue()
            self.assertIn("Autonomous CI Self-Healing initiated", output)
            self.assertIn("Healing Verdict: PASS", output)

    def test_cli_swarm(self):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("sys.argv", ["repobrain", "swarm", "Check AST parser", "--test-path", "tests/test_ast_chunker.py"]):
                main()
            output = fake_out.getvalue()
            self.assertIn("Launching RepoBrain Multi-Agent Swarm", output)
            self.assertIn("Swarm Status: SUCCESS", output)

if __name__ == "__main__":
    unittest.main()
