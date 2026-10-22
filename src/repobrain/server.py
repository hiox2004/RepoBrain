# src/repobrain/server.py
"""
RepoBrain V2 FastMCP Server & Bounded Execution Harness
Governed strictly by 00_FOUNDING_ARCHITECTURE.md (Pillars 1-5, Guardrails #7 & #8).
Exposes the 5 Core FastMCP Tools over stdio JSON-RPC.
"""

from __future__ import annotations
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Guardrail #8: Force all logging and progress bars strictly to sys.stderr
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("RepoBrain")

from repobrain.hybrid_retriever import HybridCodebaseRetriever
from repobrain.pre_sandbox_guards import (
    BoundedHarnessState,
    SanctuaryPolicyGuard,
    extract_relevant_frames,
    fast_static_syntax_check,
    parse_diff_target_paths,
)
from repobrain.schemas import PatchAndTestResponse

# Fallback FastMCP decorator if fastmcp package is not installed
try:
    from fastmcp import FastMCP  # type: ignore
except ImportError:
    class FastMCP:
        def __init__(self, name: str) -> None:
            self.name = name
            self.tools: Dict[str, Callable[..., Any]] = {}

        def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
                self.tools[fn.__name__] = fn
                return fn
            return decorator

        def run(self, transport: str = "stdio") -> None:
            logger.info("FastMCP '%s' running on %s", self.name, transport)

mcp = FastMCP("RepoBrain")

# Locate repository root from environment or current working directory
REPO_ROOT = Path(os.environ.get("REPOBRAIN_REPO_ROOT", ".")).resolve()
sanctuary_guard = SanctuaryPolicyGuard(REPO_ROOT)
harness_state = BoundedHarnessState(REPO_ROOT)
retriever = HybridCodebaseRetriever(repo_root=REPO_ROOT)


@mcp.tool()
def search_codebase(query: str, top_k: int = 5, include_episodes: bool = True) -> List[Dict[str, Any]]:
    """
    Layer 1 & Layer 2: Search codebase using Two-Stage Hybrid RRF (k=60) + Cross-Encoder reranking.
    Injects matching Layer 2 past episodic bug fixes alongside structural AST contexts.
    """
    results = retriever.search(query=query, top_k=top_k, include_episodes=include_episodes)
    return [res.model_dump() for res in results]


@mcp.tool()
def research_technology(query: str, domain: str = "general_tech") -> Dict[str, Any]:
    """
    Layer 3: Conceptual ResearchBrain 5-Phase Bounded Corrective RAG (CRAG).
    Evaluates local RFCs and ADRs. If confidence >= 0.75, spends 0 external tokens.
    """
    brief = retriever.research_brain.research_technology(query=query, domain=domain)
    return brief.model_dump()


@mcp.tool()
def search_templates(query: str, stack_domain: str = "all") -> List[Dict[str, Any]]:
    """
    Layer 4: GitHub Template Stockroom Dual Advisory.
    Retrieves verified starter blueprints and advises idiomatic scaffolding patterns.
    """
    blueprints = retriever.template_stockroom.search_templates(query=query, stack_domain=stack_domain)
    return [bp.model_dump() for bp in blueprints]


@mcp.tool()
def apply_git_patch(patch_str: str, test_path: str, task_id: str) -> Dict[str, Any]:
    """
    Pillar 5: Bounded execution harness with sanctuary checks, git apply --check pre-validation,
    in-memory byte snapshots, static syntax pre-gate, test execution, and surgical rollback on Attempt 3.
    """
    checkpoint = harness_state.get_or_create(task_id)
    target_paths = parse_diff_target_paths(patch_str)

    # 1. Sanctuary check for protected globs & path traversal
    valid, err_msg = sanctuary_guard.validate_paths(target_paths)
    if not valid:
        return PatchAndTestResponse(
            task_id=task_id,
            iteration=checkpoint.iteration,
            patch_applied=False,
            static_check_passed=False,
            tests_passed=False,
            exit_code=1,
            rolled_back=False,
            filtered_traceback=f"SanctuaryPolicyError: {err_msg}",
            reindexed_files=[],
            recorded_episode_id=None,
        ).model_dump()

    # 2. Check assertion safety on iteration 0
    safe_assertions, assertion_err = sanctuary_guard.validate_test_assertion_safety(patch_str, checkpoint.iteration)
    if not safe_assertions:
        return PatchAndTestResponse(
            task_id=task_id,
            iteration=checkpoint.iteration,
            patch_applied=False,
            static_check_passed=False,
            tests_passed=False,
            exit_code=1,
            rolled_back=False,
            filtered_traceback=f"SanctuaryPolicyError: {assertion_err}",
            reindexed_files=[],
            recorded_episode_id=None,
        ).model_dump()

    # 3. Pre-validate diff with git apply --check (does NOT increment iteration count)
    check_proc = subprocess.run(
        ["git", "apply", "--check", "-"],
        input=patch_str.encode("utf-8"),
        capture_output=True,
        cwd=REPO_ROOT,
    )
    if check_proc.returncode != 0:
        err = check_proc.stderr.decode("utf-8", errors="replace")
        return PatchAndTestResponse(
            task_id=task_id,
            iteration=checkpoint.iteration,
            patch_applied=False,
            static_check_passed=True,
            tests_passed=False,
            exit_code=check_proc.returncode,
            rolled_back=False,
            filtered_traceback=f"PatchCheckError: git apply --check rejected patch:\n{err}",
            reindexed_files=[],
            recorded_episode_id=None,
        ).model_dump()

    # Pre-check passed: now increment iteration towards <= 3 ceiling
    checkpoint.iteration += 1

    # 4. Snapshot exact pre-task file bytes before mutating disk (Guardrail #7)
    harness_state.snapshot_files_if_needed(task_id, target_paths)

    # 5. Apply patch to disk
    apply_proc = subprocess.run(
        ["git", "apply", "-"],
        input=patch_str.encode("utf-8"),
        capture_output=True,
        cwd=REPO_ROOT,
    )
    if apply_proc.returncode != 0:
        return PatchAndTestResponse(
            task_id=task_id,
            iteration=checkpoint.iteration,
            patch_applied=False,
            static_check_passed=True,
            tests_passed=False,
            exit_code=apply_proc.returncode,
            filtered_traceback=apply_proc.stderr.decode("utf-8", errors="replace"),
            reindexed_files=[],
            rolled_back=False,
        ).model_dump()

    # 6. Re-index touched files immediately (Guardrail #6)
    reindexed: List[str] = []
    for rel_path in target_paths:
        full_p = REPO_ROOT / rel_path
        if retriever.sync_file_if_changed(full_p):
            reindexed.append(rel_path)

    # 7. Fast 150ms static syntax pre-gate
    static_ok, static_err = fast_static_syntax_check(REPO_ROOT, target_paths)
    if not static_ok:
        return PatchAndTestResponse(
            task_id=task_id,
            iteration=checkpoint.iteration,
            patch_applied=True,
            static_check_passed=False,
            tests_passed=False,
            exit_code=1,
            rolled_back=False,
            filtered_traceback=static_err,
            reindexed_files=reindexed,
            recorded_episode_id=None,
        ).model_dump()

    # 8. Run test suite
    test_result = _run_test_runner(test_path)
    filtered_tb = extract_relevant_frames(test_result["raw_output"])

    tests_passed = (test_result["exit_code"] == 0)
    rolled_back = False
    recorded_episode_id: Optional[str] = None

    if not tests_passed:
        checkpoint.prior_failures.append(filtered_tb)
        # Check bounded iteration ceiling == 3
        if checkpoint.iteration >= 3:
            # Reached hard ceiling: surgically restore pre-task bytes (Guardrail #7)
            restored = harness_state.rollback_surgically(task_id)
            rolled_back = True
            for r_file in restored:
                retriever.sync_file_if_changed(REPO_ROOT / r_file)
    else:
        # If iteration > 1 transitioned from failure to exit_code == 0: distill Layer 2 episode
        if checkpoint.iteration > 1 and checkpoint.prior_failures:
            first_fail = checkpoint.prior_failures[0]
            err_sig = first_fail.splitlines()[-1] if first_fail.splitlines() else "TestFailure"
            ep = retriever.episodic_store.record_episode(
                error_signature=err_sig,
                target_symbol=target_paths[0] if target_paths else "unknown",
                file_path=target_paths[0] if target_paths else "",
                root_cause_summary="Resolution validated by BoundedHarnessState test suite pass",
                resolution_diff=patch_str,
            )
            recorded_episode_id = str(ep.episode_id)

    return PatchAndTestResponse(
        task_id=task_id,
        iteration=checkpoint.iteration,
        patch_applied=True,
        static_check_passed=True,
        tests_passed=tests_passed,
        exit_code=test_result["exit_code"],
        rolled_back=rolled_back,
        filtered_traceback=filtered_tb,
        reindexed_files=reindexed,
        recorded_episode_id=recorded_episode_id,
    ).model_dump()


def _run_test_runner(test_path: str, repo_root: Optional[Path] = None) -> Dict[str, Any]:
    """Runs pytest/unittest with sanitized flags and -- before paths."""
    root = (repo_root or REPO_ROOT).resolve()
    if test_path.startswith("-"):
        return {"exit_code": 1, "raw_output": f"SecurityError: flags not permitted in test_path: {test_path}"}

    # First try pytest if installed
    try:
        cmd = ["pytest", "-q", "--", test_path]
        proc = subprocess.run(cmd, capture_output=True, cwd=root, text=True)
        return {"exit_code": proc.returncode, "raw_output": proc.stdout + "\n" + proc.stderr}
    except FileNotFoundError:
        pass

    # Fallback to python test script execution
    try:
        cmd = [sys.executable, test_path]
        proc = subprocess.run(cmd, capture_output=True, cwd=root, text=True)
        return {"exit_code": proc.returncode, "raw_output": proc.stdout + "\n" + proc.stderr}
    except Exception as e:
        return {"exit_code": 1, "raw_output": f"TestRunnerError: {e}"}


@mcp.tool()
def run_test_suite(test_path: str, task_id: str) -> Dict[str, Any]:
    """Run test suite for a given task and strip non-local third-party stack frames."""
    res = _run_test_runner(test_path)
    filtered = extract_relevant_frames(res["raw_output"])
    return {
        "task_id": task_id,
        "exit_code": res["exit_code"],
        "filtered_traceback": filtered,
        "tests_passed": res["exit_code"] == 0,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
