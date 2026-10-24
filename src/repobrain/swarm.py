# src/repobrain/swarm.py
"""
RepoBrain Multi-Agent Local Swarm Mesh (LangGraph Native)
Coordinates specialized local subagents (Architect, Coder, Tester, Supervisor)
over a shared AST Codebase Memory, Static Blast Radius, and Episodic Memory blackboard.
Bounded by a <= 3 iteration ceiling with non-destructive surgical byte rollback.
"""

from __future__ import annotations
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, TypedDict
from uuid import uuid4

from repobrain.hybrid_retriever import HybridCodebaseRetriever
from repobrain.pre_sandbox_guards import (
    BoundedHarnessState,
    SanctuaryPolicyGuard,
    extract_relevant_frames,
    fast_static_syntax_check,
    parse_diff_target_paths,
)
from repobrain.server import _run_test_runner

logger = logging.getLogger("RepoBrain.Swarm")

# Attempt LangGraph import for native StateGraph compilation
try:
    from langgraph.graph import StateGraph, START, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    START = "__start__"
    END = "__end__"


def apply_unified_diff_to_repo(repo_root: Path, patch_str: str) -> Tuple[bool, Optional[str]]:
    """
    Applies unified diff via git apply, with fallback to direct line replacement
    for scratch/test environments that are not initialized git worktrees.
    """
    proc = subprocess.run(
        ["git", "apply", "-"],
        input=patch_str.encode("utf-8"),
        capture_output=True,
        cwd=repo_root,
    )
    if proc.returncode == 0:
        return True, None

    # Fallback to direct hunk application
    try:
        lines = patch_str.splitlines()
        target_file = None
        for line in lines:
            if line.startswith("+++ b/"):
                target_file = line[6:].strip()
                break
            elif line.startswith("+++ "):
                target_file = line[4:].strip().lstrip("b/")
                break

        if not target_file:
            return False, f"git apply failed: {proc.stderr.decode('utf-8', errors='replace')}"

        full_target = (repo_root / target_file).resolve()
        if not full_target.exists():
            return False, f"Target file does not exist: {target_file}"

        old_lines = []
        new_lines = []
        for line in lines:
            if line.startswith("-") and not line.startswith("---"):
                old_lines.append(line[1:])
            elif line.startswith("+") and not line.startswith("+++"):
                new_lines.append(line[1:])

        content = full_target.read_text(encoding="utf-8")
        # Normalize CRLF for matching
        crlf = "\r\n" in content
        content_norm = content.replace("\r\n", "\n")
        old_block = "\n".join(old_lines)
        new_block = "\n".join(new_lines)

        if old_block in content_norm:
            content_norm = content_norm.replace(old_block, new_block, 1)
            if crlf:
                content_norm = content_norm.replace("\n", "\r\n")
            full_target.write_text(content_norm, encoding="utf-8")
            return True, None

        return False, f"git apply failed and hunk not matched: {proc.stderr.decode('utf-8', errors='replace')}"
    except Exception as e:
        return False, str(e)


class SwarmState(TypedDict):
    """Shared state graph passed between specialized swarm workers."""
    task_id: str
    task_description: str
    target_file: Optional[str]
    test_path: Optional[str]
    iteration: int
    max_iterations: int
    current_worker: Literal["architect", "coder", "tester", "supervisor", "FINISH"]

    # Cognitive blackboard
    retrieved_contexts: List[Dict[str, Any]]
    blast_radius: Optional[Dict[str, Any]]
    recommended_blueprints: List[Dict[str, Any]]
    subtasks: List[str]

    # Execution blackboard
    proposed_diff: Optional[str]
    syntax_valid: bool
    test_exit_code: int
    test_output: str
    filtered_traceback: Optional[str]
    error_signature: Optional[str]

    # Outcomes
    success: bool
    rolled_back: bool
    distilled_episode_id: Optional[str]
    summary: str


class MultiAgentSwarmMesh:
    """
    Coordinates multi-agent autonomous swarms with RepoBrain as the shared cognitive substrate.
    """

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        retriever: Optional[HybridCodebaseRetriever] = None,
        patch_synthesizer: Optional[Callable[[SwarmState], Optional[str]]] = None,
    ) -> None:
        self.repo_root = (repo_root or Path.cwd()).resolve()
        self.retriever = retriever or HybridCodebaseRetriever(repo_root=self.repo_root)
        self.sanctuary_guard = SanctuaryPolicyGuard(repo_root=self.repo_root)
        self.harness_state = BoundedHarnessState(repo_root=self.repo_root)
        self.patch_synthesizer = patch_synthesizer

        # Compile LangGraph app if available
        self._graph_app = self._build_langgraph() if HAS_LANGGRAPH else None

    # --- Node 1: Architect Agent ---
    def architect_node(self, state: SwarmState) -> Dict[str, Any]:
        """
        Gathers codebase intelligence:
        - Retrieves relevant AST symbols via Two-Stage Hybrid RRF.
        - Computes blast radius on target file/symbol to map callers.
        - Checks TemplateStockroom for verified starter patterns.
        - Formulates a structured subtask execution plan.
        """
        logger.info("[Swarm.Architect] Analyzing task: '%s'", state["task_description"])

        # 1. Hybrid Search
        results = self.retriever.search(state["task_description"], top_k=3, include_episodes=True)
        retrieved_contexts = [
            {
                "symbol_name": r.symbol_name,
                "file_path": r.file_path,
                "node_kind": r.node_kind,
                "lines": f"{r.start_line}-{r.end_line}",
                "rrf_score": r.rrf_score,
            }
            for r in results
        ]

        # 2. Blast Radius Calculation
        blast_radius = None
        target_file = state.get("target_file")
        if target_file and (self.repo_root / target_file).exists():
            stem_symbol = Path(target_file).stem
            blast_radius = self.retriever.compute_blast_radius(stem_symbol, file_path=target_file)
        elif results:
            blast_radius = self.retriever.compute_blast_radius(results[0].symbol_name, file_path=results[0].file_path)

        # 3. Template Stockroom Search
        blueprints = self.retriever.template_stockroom.search_templates(state["task_description"])
        blueprint_summaries = [
            {
                "symbol_name": bp.symbol_name,
                "domain": bp.stack_domain,
                "description": bp.description,
            }
            for bp in blueprints[:2]
        ]

        # 4. Formulate Subtasks
        subtasks = [
            f"1. Context Grounding: Inspect AST for {results[0].symbol_name if results else 'target'}",
            f"2. Blast Radius Validation: Callers ({blast_radius.get('callers_count', 0) if blast_radius else 0})",
            "3. Code Modification: Apply targeted surgical diff",
            "4. Multi-Runner Test Verification",
        ]

        return {
            "retrieved_contexts": retrieved_contexts,
            "blast_radius": blast_radius,
            "recommended_blueprints": blueprint_summaries,
            "subtasks": subtasks,
            "current_worker": "coder",
            "summary": f"Architect plan created. {len(retrieved_contexts)} symbols and {len(blueprint_summaries)} blueprints mapped.",
        }

    # --- Node 2: Coder Agent ---
    def coder_node(self, state: SwarmState) -> Dict[str, Any]:
        """
        Synthesizes, validates, and applies surgical code changes:
        - Validates target paths against SanctuaryPolicy.
        - Takes in-memory byte snapshots of target files before any mutation.
        - Runs fast pre-sandbox syntax gate (py_compile / tsc).
        - Applies diff and re-indexes AST cache for modified files.
        """
        logger.info("[Swarm.Coder] Executing iteration %d for task '%s'", state["iteration"], state["task_id"])

        # Determine target file
        target_file = state.get("target_file")
        if not target_file and state.get("retrieved_contexts"):
            target_file = state["retrieved_contexts"][0]["file_path"]

        # Synthesize patch if callback provided
        diff = state.get("proposed_diff")
        if self.patch_synthesizer:
            synthesized = self.patch_synthesizer(state)
            if synthesized:
                diff = synthesized

        if not diff or not target_file:
            return {
                "syntax_valid": True,
                "current_worker": "tester",
                "summary": "No patch synthesized; proceeding directly to test evaluation.",
            }

        # Sanctuary Policy check
        try:
            valid, err = self.sanctuary_guard.validate_paths([target_file])
            if not valid:
                return {
                    "syntax_valid": False,
                    "current_worker": "FINISH",
                    "success": False,
                    "summary": f"SanctuaryPolicy violation: {err}",
                }
        except Exception as e:
            return {
                "syntax_valid": False,
                "current_worker": "FINISH",
                "success": False,
                "summary": f"SanctuaryPolicy violation: {e}",
            }

        abs_target = (self.repo_root / target_file).resolve()

        # Snapshot original bytes via BoundedHarnessState
        self.harness_state.snapshot_files_if_needed(state["task_id"], [target_file])

        # Attempt to apply diff
        applied, apply_err = apply_unified_diff_to_repo(self.repo_root, diff)
        if not applied:
            logger.warning("[Swarm.Coder] Patch application failed: %s", apply_err)
            return {
                "syntax_valid": False,
                "current_worker": "supervisor",
                "summary": f"Patch application failed: {apply_err}",
            }

        # Fast static syntax check
        is_valid, err_msg = fast_static_syntax_check(self.repo_root, [target_file])
        if not is_valid:
            logger.warning("[Swarm.Coder] Static syntax check failed: %s", err_msg)
            return {
                "syntax_valid": False,
                "current_worker": "supervisor",
                "filtered_traceback": err_msg,
                "summary": f"Syntax check failed: {err_msg}",
            }

        # Re-index modified file into AST memory
        self.retriever.sync_file_if_changed(abs_target)

        return {
            "syntax_valid": True,
            "proposed_diff": diff,
            "target_file": target_file,
            "current_worker": "tester",
            "summary": f"Surgically applied patch to {target_file} and synced AST index.",
        }

    # --- Node 3: Tester Agent ---
    def tester_node(self, state: SwarmState) -> Dict[str, Any]:
        """
        Executes test suite and performs verification:
        - Executes multi-runner test harness.
        - On Pass: If previous iteration failed, distills fail-to-pass lesson into episodic memory.
        - On Fail: Extracts filtered traceback and checks episodic memory for post-mortems.
        """
        test_path = state.get("test_path")
        if not test_path:
            logger.info("[Swarm.Tester] No test suite specified; marking task verified.")
            return {
                "test_exit_code": 0,
                "test_output": "No test suite specified. Static checks passed.",
                "success": True,
                "current_worker": "FINISH",
                "summary": "Task verified cleanly (no test suite provided).",
            }

        logger.info("[Swarm.Tester] Executing test suite '%s'...", test_path)
        run_res = _run_test_runner(test_path, repo_root=self.repo_root)
        exit_code = run_res["exit_code"]
        raw_output = run_res.get("raw_output", run_res.get("output", ""))

        if exit_code == 0:
            logger.info("[Swarm.Tester] Tests passed cleanly on iteration %d!", state["iteration"])
            distilled_id = None
            if state["iteration"] > 1 and state.get("proposed_diff"):
                # Transition from failure to pass: record in episodic memory
                target_sym = state.get("target_file", "unknown")
                distilled_id = self.retriever.record_episodic_fix(
                    target_symbol=target_sym,
                    file_path=state.get("target_file", ""),
                    error_signature=state.get("error_signature", "Test failure"),
                    root_cause_summary=f"Swarm self-healed on iteration {state['iteration']}",
                    resolution_diff=state.get("proposed_diff", ""),
                )

            return {
                "test_exit_code": 0,
                "test_output": raw_output,
                "filtered_traceback": None,
                "success": True,
                "distilled_episode_id": distilled_id,
                "current_worker": "FINISH",
                "summary": f"Test suite '{test_path}' passed cleanly (Exit: 0).",
            }
        else:
            filtered_tb = extract_relevant_frames(raw_output)
            err_sig = raw_output.splitlines()[-1] if raw_output.splitlines() else "Test failure"
            logger.warning("[Swarm.Tester] Test failed (Exit: %d): %s", exit_code, err_sig)

            # Query episodic memory for past matching bug fixes
            past_episodes = self.retriever.episodic_store.find_matching_episodes(
                file_path=state.get("target_file", ""),
                query=err_sig,
                limit=1,
            )
            ep_advisory = f"Found past episodic lesson: {past_episodes[0].root_cause_summary}" if past_episodes else "No past post-mortem recorded."

            return {
                "test_exit_code": exit_code,
                "test_output": raw_output,
                "filtered_traceback": filtered_tb,
                "error_signature": err_sig,
                "current_worker": "supervisor",
                "summary": f"Test failed (Exit: {exit_code}): {err_sig}. {ep_advisory}",
            }

    # --- Node 4: Supervisor Agent ---
    def supervisor_node(self, state: SwarmState) -> Dict[str, Any]:
        """
        Coordinates the swarm lifecycle and enforces the bounded 3-retry ceiling:
        - If success: routes to FINISH.
        - If iteration limit reached without success: executes in-memory surgical byte rollback.
        - If retries remain: increments iteration and routes back to coder.
        """
        if state.get("success"):
            return {"current_worker": "FINISH", "summary": "Swarm successfully completed all objectives."}

        current_iter = state["iteration"]
        max_iter = state["max_iterations"]

        if current_iter >= max_iter or not state.get("syntax_valid", True):
            # Ceiling reached: execute non-destructive surgical byte rollback
            logger.warning("[Swarm.Supervisor] Reached retry ceiling (%d/%d). Rolling back touched files...", current_iter, max_iter)
            restored = self.harness_state.rollback_surgically(state["task_id"])
            for r_file in restored:
                abs_p = (self.repo_root / r_file).resolve()
                self.retriever.sync_file_if_changed(abs_p)
                logger.info("[Swarm.Supervisor] Surgically restored: %s", r_file)

            return {
                "rolled_back": True,
                "success": False,
                "current_worker": "FINISH",
                "summary": f"Retry ceiling reached ({current_iter}/{max_iter}). Non-destructive surgical rollback executed ({len(restored)} files restored).",
            }
        else:
            next_iter = current_iter + 1
            logger.info("[Swarm.Supervisor] Routing swarm back to Coder for attempt %d/%d...", next_iter, max_iter)
            return {
                "iteration": next_iter,
                "current_worker": "coder",
                "summary": f"Supervisor routed swarm for retry attempt {next_iter}/{max_iter}.",
            }

    # --- Routing helper ---
    @staticmethod
    def route_worker(state: SwarmState) -> str:
        return state["current_worker"]

    # --- LangGraph Builder ---
    def _build_langgraph(self) -> Any:
        workflow = StateGraph(SwarmState)
        workflow.add_node("architect", self.architect_node)
        workflow.add_node("coder", self.coder_node)
        workflow.add_node("tester", self.tester_node)
        workflow.add_node("supervisor", self.supervisor_node)

        workflow.add_edge(START, "architect")
        workflow.add_edge("architect", "coder")
        workflow.add_edge("coder", "tester")
        workflow.add_edge("tester", "supervisor")

        workflow.add_conditional_edges(
            "supervisor",
            self.route_worker,
            {
                "coder": "coder",
                "architect": "architect",
                "FINISH": END,
            },
        )
        return workflow.compile()

    # --- Main Swarm Execution Entrypoint ---
    def run_swarm(
        self,
        task_description: str,
        target_file: Optional[str] = None,
        test_path: Optional[str] = None,
        max_iterations: int = 3,
    ) -> SwarmState:
        """
        Runs the full multi-agent swarm mesh to completion using LangGraph StateGraph,
        falling back to the deterministic sequential engine if LangGraph is unavailable.
        """
        initial_state: SwarmState = {
            "task_id": f"swarm-{uuid4().hex[:8]}",
            "task_description": task_description,
            "target_file": target_file,
            "test_path": test_path,
            "iteration": 1,
            "max_iterations": max_iterations,
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
            "summary": "Swarm initialized.",
        }

        # If LangGraph StateGraph is compiled, invoke it directly
        if self._graph_app is not None:
            logger.info("[Swarm] Executing via native LangGraph StateGraph runtime...")
            try:
                final_state = self._graph_app.invoke(initial_state)
                return final_state
            except Exception as e:
                logger.warning("[Swarm] LangGraph invoke encountered error: %s. Falling back to deterministic engine.", e)

        # Fallback deterministic state-machine loop
        logger.info("[Swarm] Executing via deterministic multi-agent state-machine loop...")
        state = dict(initial_state)
        while state["current_worker"] != "FINISH":
            worker = state["current_worker"]
            if worker == "architect":
                update = self.architect_node(state)  # type: ignore
            elif worker == "coder":
                update = self.coder_node(state)  # type: ignore
            elif worker == "tester":
                update = self.tester_node(state)  # type: ignore
            elif worker == "supervisor":
                update = self.supervisor_node(state)  # type: ignore
            else:
                break
            state.update(update)

        return state  # type: ignore
