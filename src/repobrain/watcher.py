# src/repobrain/watcher.py
"""
RepoBrain Real-Time File Watcher Daemon
Continuously monitors the codebase for source changes, computes Git blob SHAs,
and incrementally synchronizes the in-memory and persistent AST stores.
"""

from __future__ import annotations
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("RepoBrain.Watcher")

SUPPORTED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx"}
IGNORED_DIRECTORIES = {
    "node_modules",
    "dist",
    "build",
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    ".repobrain",
    "scratch",
    ".next",
}


class RetrieverWatcher:
    """
    Lightweight, background daemon thread that tracks file mtimes and Git blob SHAs.
    Provides sub-millisecond, zero-cold-start AST cache synchronization.
    """

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        retriever: Optional[Any] = None,
        poll_interval_seconds: float = 0.5,
        on_change_callback: Optional[Callable[[List[str]], None]] = None,
    ) -> None:
        self.repo_root = (repo_root or Path.cwd()).resolve()
        self.poll_interval = poll_interval_seconds
        self.on_change_callback = on_change_callback

        if retriever is None:
            from repobrain.hybrid_retriever import HybridCodebaseRetriever
            self.retriever = HybridCodebaseRetriever(repo_root=self.repo_root)
        else:
            self.retriever = retriever

        self._mtime_cache: Dict[str, float] = {}
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._synced_events_count = 0
        self._last_synced_files: List[str] = []

        # Initial baseline scan
        self._scan_baseline()

    def _should_ignore(self, path: Path) -> bool:
        """Checks if a path should be ignored based on parent directory names."""
        for part in path.parts:
            if part in IGNORED_DIRECTORIES or part.startswith("."):
                if part != ".":
                    return True
        return False

    def _scan_baseline(self) -> None:
        """Populates the initial mtime cache without firing change events."""
        src_dir = self.repo_root / "src"
        scan_target = src_dir if src_dir.exists() else self.repo_root

        for p in scan_target.glob("**/*"):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS and not self._should_ignore(p):
                try:
                    rel = p.relative_to(self.repo_root).as_posix()
                    self._mtime_cache[rel] = p.stat().st_mtime
                except Exception:
                    pass

    def sync_once(self) -> List[str]:
        return self.poll_once()

    def poll_once(self) -> List[str]:
        """
        Single polling sweep: identifies modified, added, or deleted files,
        and triggers incremental Git blob SHA synchronization on the retriever.
        """
        modified_or_added: List[str] = []
        current_files: Set[str] = set()

        src_dir = self.repo_root / "src"
        scan_target = src_dir if src_dir.exists() else self.repo_root

        for p in scan_target.glob("**/*"):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS and not self._should_ignore(p):
                try:
                    rel = p.relative_to(self.repo_root).as_posix()
                    current_files.add(rel)
                    mtime = p.stat().st_mtime

                    # Check if file is new or modified
                    if rel not in self._mtime_cache or mtime > self._mtime_cache[rel]:
                        self._mtime_cache[rel] = mtime
                        # Incremental Git blob SHA sync
                        if self.retriever.sync_file_if_changed(p):
                            modified_or_added.append(rel)
                except Exception as e:
                    logger.debug("Error checking file %s: %e", p, e)

        # Check for deleted files
        deleted = set(self._mtime_cache.keys()) - current_files
        for del_rel in deleted:
            del self._mtime_cache[del_rel]
            full_del_path = self.repo_root / del_rel
            self.retriever.sync_file_if_changed(full_del_path)
            modified_or_added.append(del_rel)

        if modified_or_added:
            self._synced_events_count += len(modified_or_added)
            self._last_synced_files = modified_or_added
            logger.info("RetrieverWatcher synced %d file(s): %s", len(modified_or_added), modified_or_added)
            if self.on_change_callback:
                try:
                    self.on_change_callback(modified_or_added)
                except Exception as cb_err:
                    logger.error("Watcher callback error: %s", cb_err)

        return modified_or_added

    def _run_loop(self) -> None:
        """Main loop executed inside background daemon thread."""
        logger.info("RetrieverWatcher background daemon started (poll: %.2fs)", self.poll_interval)
        while not self._stop_event.is_set():
            try:
                self.poll_once()
            except Exception as e:
                logger.error("Watcher poll error: %s", e)
            self._stop_event.wait(self.poll_interval)
        logger.info("RetrieverWatcher background daemon stopped.")

    def start(self) -> None:
        """Starts the file watcher daemon in the background."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="RepoBrain-Watcher")
        self._thread.start()

    def stop(self) -> None:
        """Stops the file watcher daemon."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def is_running(self) -> bool:
        """Checks if the watcher thread is active."""
        return self._thread is not None and self._thread.is_alive()

    def stats(self) -> Dict[str, Any]:
        """Returns diagnostic status of the watcher."""
        return {
            "is_running": self.is_running(),
            "poll_interval_seconds": self.poll_interval,
            "tracked_files_count": len(self._mtime_cache),
            "total_synced_events": self._synced_events_count,
            "last_synced_files": self._last_synced_files,
            "repo_root": str(self.repo_root),
        }
