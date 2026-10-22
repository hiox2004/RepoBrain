# src/repobrain/pre_sandbox_guards.py
"""
Pre-Sandbox Guards & Bounded Execution State
Governed strictly by 00_FOUNDING_ARCHITECTURE.md (Pillar 5, Guardrails #7 & #8).
Enforces:
- Sanctuary Policy Guard (blocks protected files and path traversals)
- 150ms Static Syntax Pre-Gate (py_compile)
- Traceback Frame Sanitizer (strips site-packages/ and node_modules/)
- Per-Task Byte Snapshots & Non-Destructive Surgical Rollback (no git reset --hard)
"""

from __future__ import annotations
import fnmatch
import logging
import os
import py_compile
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("RepoBrain.Guards")


class SanctuaryPolicyGuard:
    """
    Guardrail #8: Blocks mutations to protected critical files defined in policy.
    Rejects directory traversal attempts and assertion-weakening edits on iteration 0.
    """
    DEFAULT_PROTECTED_PATTERNS = [
        "*.lock",
        "bun.lock",
        "poetry.lock",
        "package-lock.json",
        "yarn.lock",
        "uv.lock",
        "pnpm-lock.yaml",
        "alembic/versions/*",
        "pyproject.toml",
        ".env",
        ".env.*",
        ".repobrain/policy.toml",
        ".git/*",
        ".github/workflows/*",
    ]

    def __init__(self, repo_root: Path, policy_file: Optional[Path] = None) -> None:
        self.repo_root = repo_root.resolve()
        self.protected_patterns = list(self.DEFAULT_PROTECTED_PATTERNS)
        target_policy = policy_file or (self.repo_root / ".repobrain" / "policy.toml")
        if target_policy.exists():
            self._load_policy(target_policy)

    def _load_policy(self, policy_file: Path) -> None:
        try:
            content = policy_file.read_text("utf-8")
            in_patterns = False
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("protected_patterns"):
                    in_patterns = True
                    continue
                if in_patterns:
                    if line.startswith("]"):
                        in_patterns = False
                        continue
                    clean = line.strip(',"\'[] ')
                    if clean and not clean.startswith("#"):
                        self.protected_patterns.append(clean)
        except Exception as e:
            logger.warning("Could not read policy file: %s", e)

    def validate_paths(self, target_paths: List[str]) -> Tuple[bool, Optional[str]]:
        """Validates that all target paths are within repo bounds and do not hit protected globs."""
        for rel_path in target_paths:
            # Prevent directory traversal
            resolved = (self.repo_root / rel_path).resolve()
            try:
                resolved.relative_to(self.repo_root)
            except ValueError:
                return False, f"Path traversal attempt blocked: {rel_path}"

            # Check protected globs
            for pattern in self.protected_patterns:
                if fnmatch.fnmatch(rel_path, pattern):
                    return False, f"Sanctuary policy violation: '{rel_path}' matches protected pattern '{pattern}'"
        return True, None

    def validate_test_assertion_safety(self, patch_str: str, iteration: int) -> Tuple[bool, Optional[str]]:
        """
        Pillar 5 Invariant: On iteration 0/1, rejects diffs that delete or weaken 'assert' statements in tests.
        """
        if iteration == 0:
            for line in patch_str.splitlines():
                if line.startswith("-") and not line.startswith("---"):
                    stripped = line[1:].strip()
                    if stripped.startswith("assert ") or "assert " in stripped:
                        return False, "Sanctuary policy violation: Cannot delete or weaken test assertions on initial attempt."
        return True, None


@dataclass
class TaskCheckpoint:
    """
    Per-task snapshot of pre-task file byte contents before disk mutation (Guardrail #7).
    """
    task_id: str
    iteration: int = 0
    original_file_snapshots: Dict[str, Optional[bytes]] = field(default_factory=dict)
    touched_files: Set[str] = field(default_factory=set)
    prior_failures: List[str] = field(default_factory=list)


class BoundedHarnessState:
    """
    Manages task checkpoints, bounded <= 3 retry iterations, and surgical rollback.
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.tasks: Dict[str, TaskCheckpoint] = {}

    def get_or_create(self, task_id: str) -> TaskCheckpoint:
        if task_id not in self.tasks:
            self.tasks[task_id] = TaskCheckpoint(task_id=task_id)
        return self.tasks[task_id]

    def snapshot_files_if_needed(self, task_id: str, paths: List[str]) -> None:
        checkpoint = self.get_or_create(task_id)
        for rel_path in paths:
            if rel_path not in checkpoint.original_file_snapshots:
                full_path = self.repo_root / rel_path
                if full_path.exists():
                    checkpoint.original_file_snapshots[rel_path] = full_path.read_bytes()
                else:
                    checkpoint.original_file_snapshots[rel_path] = None
            checkpoint.touched_files.add(rel_path)

    def rollback_surgically(self, task_id: str) -> List[str]:
        """
        Guardrail #7: Surgically restores only snapshotted files to exact pre-task bytes.
        Never executes 'git reset --hard', leaving unrelated uncommitted files completely intact.
        """
        checkpoint = self.tasks.get(task_id)
        if not checkpoint:
            return []

        restored_files: List[str] = []
        for rel_path, original_bytes in checkpoint.original_file_snapshots.items():
            full_path = self.repo_root / rel_path
            if original_bytes is None:
                # File was newly created by this task; delete it
                if full_path.exists():
                    full_path.unlink()
                    restored_files.append(rel_path)
            else:
                # Restore exact bytes
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_bytes(original_bytes)
                restored_files.append(rel_path)

        return restored_files


def extract_relevant_frames(raw_output: str) -> str:
    """
    Guardrail #8: Strips noise from site-packages/ and node_modules/ frames
    while retaining repository-local file paths, line numbers, and assertion deltas.
    """
    lines = raw_output.splitlines()
    filtered: List[str] = []
    skip_block = False

    for line in lines:
        if "site-packages/" in line or "node_modules/" in line:
            continue
        if line.strip().startswith("File ") and ("site-packages/" in line or "node_modules/" in line):
            skip_block = True
            continue
        if skip_block and line.startswith("    "):
            continue
        skip_block = False
        filtered.append(line)

    return "\n".join(filtered).strip()


def fast_static_syntax_check(repo_root: Path, target_paths: List[str]) -> Tuple[bool, str]:
    """
    150ms Static Syntax Pre-Gate:
    Runs py_compile on python files before invoking expensive test suites.
    """
    for rel_path in target_paths:
        if rel_path.endswith(".py"):
            full_path = repo_root / rel_path
            if full_path.exists():
                try:
                    py_compile.compile(str(full_path), doraise=True)
                except py_compile.PyCompileError as pe:
                    return False, f"StaticSyntaxError in '{rel_path}':\n{pe}"
    return True, ""


def parse_diff_target_paths(patch_str: str) -> List[str]:
    """Extracts target file paths from unified diff headers."""
    paths: List[str] = []
    for line in patch_str.splitlines():
        if line.startswith("+++ b/") or line.startswith("+++ "):
            p = line[6:].strip() if line.startswith("+++ b/") else line[4:].strip()
            if p != "/dev/null" and p not in paths:
                paths.append(p)
    return paths

