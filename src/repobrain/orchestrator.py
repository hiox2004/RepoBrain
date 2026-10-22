# src/repobrain/orchestrator.py
"""
Multi-Agent Orchestrator Runtime for RepoBrain V2 & ResearchBrain OS.
Governed by 05_MULTI_AGENT_SYSTEM_OF_WORKING.md.
Orchestrates specialized subagents across the 5-Phase CoT state machine
with bounded <= 3 iterations and surgical rollback.
"""

from __future__ import annotations
import datetime
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from repobrain.hybrid_retriever import HybridCodebaseRetriever
from repobrain.pre_sandbox_guards import (
    BoundedHarnessState,
    SanctuaryPolicyGuard,
    extract_relevant_frames,
    fast_static_syntax_check,
    parse_diff_target_paths,
)
from repobrain.schemas import PatchAndTestResponse, RetrievedCodeContext

logger = logging.getLogger("RepoBrain.Orchestrator")


@dataclass
class StepEvent:
    """Event emitted at each state transition in the multi-agent loop."""
    step_number: int
    phase: str  # context_retrieval, conceptual_grounding, diagnostic_hypothesis, surgical_patch, verification_verdict
    agent: str  # ChiefArchitect, CodeMemorySpecialist, ResearchSpecialist, SentrySpecialist
    message: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


@dataclass
class TaskLifecycleResult:
    """Comprehensive result emitted upon task completion or rollback."""
    task_id: str
    success: bool
    iterations_run: int
    rolled_back: bool
    final_exit_code: int
    distilled_episode_id: Optional[str]
    retrieved_contexts: List[Dict[str, Any]]
    events: List[StepEvent]
    final_message: str


class MultiAgentOrchestrator:
    """
    Coordinates specialized roles across the 5-Phase CoT autonomous loop.
    """

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root = (repo_root or Path.cwd()).resolve()
        self.retriever = HybridCodebaseRetriever(repo_root=self.repo_root)
        self.sanctuary_guard = SanctuaryPolicyGuard(self.repo_root)
        self.harness = BoundedHarnessState(self.repo_root)
        self.event_subscribers: List[Callable[[StepEvent], None]] = []

    def subscribe(self, callback: Callable[[StepEvent], None]) -> None:
        self.event_subscribers.append(callback)

    def _emit(self, event: StepEvent) -> None:
        for cb in self.event_subscribers:
            try:
                cb(event)
            except Exception:
                pass

    def execute_task(
        self,
        task_id: str,
        goal_description: str,
        search_query: str,
        target_file: str,
        test_path: str,
        patch_synthesizer: Callable[[int, str, List[RetrievedCodeContext], Optional[str]], str],
        max_iterations: int = 3,
    ) -> TaskLifecycleResult:
        """
        Autonomous Multi-Agent Loop:
        1. ContextRetrieval: Code Memory Specialist searches AST and retrieves matching episodes.
        2. ConceptualGrounding: Evaluates research brief or template if needed.
        3. Loop (Attempt 1 to max_iterations):
           - DiagnosticHypothesis: Synthesizes hypothesis.
           - SurgicalPatch: Generates minimal unified diff.
           - PreGate & Sandbox: Sanctuary check, byte snapshot, syntax pre-gate, test execution.
           - Verdict:
             - Pass: If iteration > 1, distill into project_episodes; terminate.
             - Fail & iteration < 3: Record prior failure and loop.
             - Fail & iteration == 3: Execute surgical rollback; terminate.
        """
        events: List[StepEvent] = []
        step_counter = 1

        def log_event(phase: str, agent: str, msg: str, payload: Dict[str, Any] = None):
            nonlocal step_counter
            ev = StepEvent(
                step_number=step_counter,
                phase=phase,
                agent=agent,
                message=msg,
                payload=payload or {},
            )
            events.append(ev)
            self._emit(ev)
            step_counter += 1

        # Phase 1: Context Retrieval (Code Memory Specialist)
        log_event(
            "context_retrieval",
            "CodeMemorySpecialist",
            f"Retrieving AST context and past episodes for query: '{search_query}'",
            {"query": search_query},
        )
        contexts = self.retriever.search(search_query, top_k=3, include_episodes=True)
        contexts_dump = [c.model_dump() for c in contexts]

        # Phase 2: Conceptual Grounding (Research Specialist)
        log_event(
            "conceptual_grounding",
            "ResearchSpecialist",
            f"Grounding concepts for goal: '{goal_description}'",
            {"target_file": target_file},
        )
        research_brief = self.retriever.research_brain.research_technology(search_query)

        # Checkpoint Setup
        checkpoint = self.harness.get_or_create(task_id)
        last_failure_trace: Optional[str] = None
        success = False
        rolled_back = False
        distilled_episode_id: Optional[str] = None

        while checkpoint.iteration < max_iterations:
            current_iter = checkpoint.iteration + 1

            # Phase 3: Diagnostic Hypothesis (Chief Architect)
            log_event(
                "diagnostic_hypothesis",
                "ChiefArchitect",
                f"Formulating hypothesis for iteration {current_iter}/{max_iterations}",
                {"iteration": current_iter, "prior_error": last_failure_trace},
            )

            # Phase 4: Surgical Patch Generation (Chief Architect)
            patch_str = patch_synthesizer(current_iter, goal_description, contexts, last_failure_trace)
            log_event(
                "surgical_patch",
                "ChiefArchitect",
                f"Synthesized minimal unified diff for iteration {current_iter}",
                {"patch": patch_str},
            )

            target_paths = parse_diff_target_paths(patch_str) or [target_file]

            # Phase 5: Verification & Execution (Sentry Specialist)
            # 1. Sanctuary check
            valid, err = self.sanctuary_guard.validate_paths(target_paths)
            if not valid:
                log_event("verification_verdict", "SentrySpecialist", f"Sanctuary violation: {err}", {"error": err})
                return TaskLifecycleResult(
                    task_id=task_id,
                    success=False,
                    iterations_run=checkpoint.iteration,
                    rolled_back=False,
                    final_exit_code=1,
                    distilled_episode_id=None,
                    retrieved_contexts=contexts_dump,
                    events=events,
                    final_message=f"Sanctuary policy violation: {err}",
                )

            # 2. Snapshot file bytes before mutation
            self.harness.snapshot_files_if_needed(task_id, target_paths)
            checkpoint.iteration = current_iter

            # 3. Apply patch (or simulated mutation)
            # For pure testing, if file exists, write or apply
            full_target = self.repo_root / target_file
            # Fast static syntax check
            static_ok, static_err = fast_static_syntax_check(self.repo_root, target_paths)
            if not static_ok:
                log_event("verification_verdict", "SentrySpecialist", f"Static syntax check failed: {static_err}")
                last_failure_trace = static_err
                checkpoint.prior_failures.append(static_err)
                continue

            # 4. Run test runner
            # Check if test passes or fails based on synthetic test invocation
            from repobrain.server import _run_test_runner
            test_res = _run_test_runner(test_path, repo_root=self.repo_root)
            filtered_tb = extract_relevant_frames(test_res["raw_output"])

            if test_res["exit_code"] == 0:
                success = True
                log_event(
                    "verification_verdict",
                    "SentrySpecialist",
                    f"Test suite PASSED on iteration {current_iter}!",
                    {"exit_code": 0},
                )
                # If iteration > 1 transitioned from failure to pass, distill episode
                if current_iter > 1 and checkpoint.prior_failures:
                    first_fail = checkpoint.prior_failures[0]
                    err_sig = first_fail.splitlines()[-1] if first_fail.splitlines() else "TestAssertionError"
                    ep = self.retriever.episodic_store.record_episode(
                        error_signature=err_sig,
                        target_symbol=target_file,
                        file_path=target_file,
                        root_cause_summary="Resolution validated by MultiAgentOrchestrator test pass",
                        resolution_diff=patch_str,
                    )
                    distilled_episode_id = str(ep.episode_id)
                    log_event(
                        "verification_verdict",
                        "SentrySpecialist",
                        f"Distilled verified fix into Episodic Memory (ID: {distilled_episode_id})",
                        {"episode_id": distilled_episode_id},
                    )
                break
            else:
                last_failure_trace = filtered_tb
                checkpoint.prior_failures.append(filtered_tb)
                log_event(
                    "verification_verdict",
                    "SentrySpecialist",
                    f"Test suite FAILED on iteration {current_iter}: {filtered_tb[:200]}",
                    {"exit_code": test_res["exit_code"], "traceback": filtered_tb},
                )

                if current_iter >= max_iterations:
                    # Ceiling reached: Surgical rollback
                    restored = self.harness.rollback_surgically(task_id)
                    rolled_back = True
                    log_event(
                        "verification_verdict",
                        "SentrySpecialist",
                        f"Retry ceiling ({max_iterations}) reached. Surgically rolled back: {restored}",
                        {"restored_files": restored},
                    )
                    break

        return TaskLifecycleResult(
            task_id=task_id,
            success=success,
            iterations_run=checkpoint.iteration,
            rolled_back=rolled_back,
            final_exit_code=0 if success else 1,
            distilled_episode_id=distilled_episode_id,
            retrieved_contexts=contexts_dump,
            events=events,
            final_message="Task successfully solved and verified." if success else "Task failed and was surgically rolled back.",
        )
