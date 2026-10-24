# src/repobrain/ci_heal.py
"""
RepoBrain Autonomous CI & Test Self-Healing Engine
Diagnoses test failures in CI / local dev, computes blast radius,
retrieves episodic memory post-mortems, applies bounded surgical patches,
and generates formatted GitHub Actions PR review summaries.
"""

from __future__ import annotations
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from repobrain.hybrid_retriever import HybridCodebaseRetriever
from repobrain.orchestrator import MultiAgentOrchestrator, TaskLifecycleResult
from repobrain.pre_sandbox_guards import extract_relevant_frames
from repobrain.server import _run_test_runner

logger = logging.getLogger("RepoBrain.CIHeal")


class CIHealingOrchestrator:
    """
    Coordinates headless self-healing of failing test suites in CI environments.
    """

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root = (repo_root or Path.cwd()).resolve()
        self.orchestrator = MultiAgentOrchestrator(repo_root=self.repo_root)
        self.retriever = self.orchestrator.retriever

    def diagnose_and_heal(
        self,
        test_path: str,
        target_file: Optional[str] = None,
        patch_synthesizer: Optional[Callable[[int, str, List[Any], Optional[str]], str]] = None,
        max_iterations: int = 3,
    ) -> Dict[str, Any]:
        """
        Executes the autonomous healing lifecycle:
        1. Executes target test suite to capture raw output and exit code.
        2. If passed, returns early with Clean verdict.
        3. Extracts filtered local traceback (stripped of third-party frames).
        4. Identifies failing symbol and computes blast radius across the repository.
        5. Queries Layer 2 episodic memory for past post-mortems matching the symbol/signature.
        6. Runs bounded 5-Phase CoT self-healing loop (up to max_iterations <= 3).
        7. Returns structured verdict and GitHub PR Markdown comment.
        """
        logger.info("Executing CI test run for '%s'...", test_path)
        initial_run = _run_test_runner(test_path, repo_root=self.repo_root)

        if initial_run["exit_code"] == 0:
            return {
                "status": "PASS",
                "healed": False,
                "message": f"Test suite '{test_path}' passed cleanly on first run. No healing required.",
                "exit_code": 0,
                "iterations_run": 0,
                "github_markdown": self._render_github_clean_markdown(test_path),
            }

        filtered_tb = extract_relevant_frames(initial_run["raw_output"])
        err_lines = filtered_tb.splitlines()
        error_signature = err_lines[-1] if err_lines else "TestFailure"

        # Auto-detect target file if not provided
        detected_target = target_file
        if not detected_target:
            for line in err_lines:
                if 'File "' in line:
                    parts = line.split('File "')
                    if len(parts) > 1:
                        f_candidate = parts[1].split('"')[0]
                        if not f_candidate.startswith("tests") and (self.repo_root / f_candidate).exists():
                            detected_target = f_candidate
                            break
        detected_target = detected_target or "unknown"

        # Compute Blast Radius on suspected symbol/file
        symbol_guess = Path(detected_target).stem if detected_target != "unknown" else "CoreModule"
        blast_radius = self.retriever.compute_blast_radius(symbol_guess, file_path=detected_target)

        # Check Episodic Memory for matching lessons
        matching_episodes = self.retriever.episodic_store.find_matching_episodes(
            symbol_name=symbol_guess, query=error_signature
        )

        task_id = f"ci-heal-{int(time.time())}"

        # If custom patch_synthesizer provided, execute orchestrator self-healing
        if patch_synthesizer:
            task_result: TaskLifecycleResult = self.orchestrator.execute_task(
                task_id=task_id,
                goal_description=f"Auto-heal failing test {test_path}: {error_signature}",
                search_query=f"{symbol_guess} {error_signature}",
                target_file=detected_target,
                test_path=test_path,
                patch_synthesizer=patch_synthesizer,
                max_iterations=max_iterations,
            )
            healed = task_result.success
            iterations_run = task_result.iterations_run
            distilled_episode_id = task_result.distilled_episode_id
        else:
            # Advisory mode without LLM synthesizer
            healed = False
            iterations_run = 1
            distilled_episode_id = None

        markdown_report = self._render_github_pr_markdown(
            test_path=test_path,
            target_file=detected_target,
            error_signature=error_signature,
            filtered_tb=filtered_tb,
            blast_radius=blast_radius,
            matching_episodes=matching_episodes,
            healed=healed,
            iterations_run=iterations_run,
            distilled_episode_id=distilled_episode_id,
        )

        return {
            "status": "HEALED" if healed else "FAILED",
            "healed": healed,
            "test_path": test_path,
            "target_file": detected_target,
            "error_signature": error_signature,
            "filtered_traceback": filtered_tb,
            "blast_radius": blast_radius,
            "matching_episodes_count": len(matching_episodes),
            "iterations_run": iterations_run,
            "distilled_episode_id": distilled_episode_id,
            "github_markdown": markdown_report,
        }

    def _render_github_clean_markdown(self, test_path: str) -> str:
        return f"""### 🤖 RepoBrain CI Health Check
- **Status:** `PASSED`
- **Target Suite:** `{test_path}`
- **Verdict:** All test assertions verified. Zero regressions detected.
"""

    def _render_github_pr_markdown(
        self,
        test_path: str,
        target_file: str,
        error_signature: str,
        filtered_tb: str,
        blast_radius: Dict[str, Any],
        matching_episodes: List[Any],
        healed: bool,
        iterations_run: int,
        distilled_episode_id: Optional[str],
    ) -> str:
        status_badge = "🟩 HEALED IN CI" if healed else "🟥 UNRESOLVED (3-ATTEMPT CEILING REACHED)"
        risk_level = blast_radius.get("risk_level", "LOW")
        callers = blast_radius.get("callers_count", 0)

        episodes_md = ""
        if matching_episodes:
            episodes_md = "\n#### 🧠 Historical Episodic Fixes Injected:\n"
            for ep in matching_episodes[:2]:
                episodes_md += f"- **Lesson:** {ep.root_cause_summary}\n"

        return f"""### 🤖 RepoBrain Autonomous CI Self-Healing Report

**Verdict:** `{status_badge}`  
- **Test Suite:** `{test_path}`  
- **Target File:** `{target_file}`  
- **Error Signature:** `{error_signature}`  
- **Blast Radius:** `{risk_level}` ({callers} downstream caller(s) flagged)  
- **Iterations Run:** `{iterations_run} / 3`  
{f"- **Distilled Episode:** `{distilled_episode_id}`" if distilled_episode_id else ""}

#### 🔍 Filtered Traceback:
```text
{filtered_tb[:1200]}
```
{episodes_md}
---
*Generated by RepoBrain FastMCP Autonomous CI Harness*
"""


def run_ci_heal(
    test_path: str,
    repo_root: Optional[Path] = None,
    output_markdown_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """CLI entrypoint for executing CI self-healing."""
    healer = CIHealingOrchestrator(repo_root=repo_root)
    result = healer.diagnose_and_heal(test_path=test_path)

    if output_markdown_file:
        p = Path(output_markdown_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(result["github_markdown"], encoding="utf-8")
        logger.info("Wrote GitHub PR report to: %s", p)

    return result
