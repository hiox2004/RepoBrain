# src/repobrain/episodic_memory.py
"""
Layer 2: Self-Correcting Episodic Diagnostic Memory
Governed strictly by 00_FOUNDING_ARCHITECTURE.md Pillar 2.
Distills fail-to-pass test transitions and injects immunization records into search queries.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from repobrain.schemas import EpisodicBugRecord


class EpisodicMemoryStore:
    """
    Episodic Diagnostic Bug Cache.
    Maintains proven fail-to-pass resolutions to shield the agent from repeating bugs.
    """

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.storage_path = storage_path
        self._episodes: Dict[UUID, EpisodicBugRecord] = {}
        if self.storage_path and self.storage_path.exists():
            self._load()

    def record_episode(
        self,
        error_signature: str,
        target_symbol: str,
        file_path: str,
        root_cause_summary: str,
        resolution_diff: str,
    ) -> EpisodicBugRecord:
        """
        Distills a verified fix when tests transition from fail (Attempt 1/2) to pass (Attempt 2/3).
        Enforces <= 40-word constraint on root_cause_summary.
        """
        words = root_cause_summary.strip().split()
        if len(words) > 40:
            compact_summary = " ".join(words[:40]) + "..."
        else:
            compact_summary = " ".join(words)

        episode = EpisodicBugRecord(
            episode_id=uuid4(),
            error_signature=error_signature.strip(),
            target_symbol=target_symbol.strip(),
            file_path=file_path.strip(),
            root_cause_summary=compact_summary,
            resolution_diff=resolution_diff.strip(),
        )
        self._episodes[episode.episode_id] = episode
        if self.storage_path:
            self._save()
        return episode

    def find_matching_episodes(
        self,
        symbol_name: Optional[str] = None,
        file_path: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 3,
    ) -> List[EpisodicBugRecord]:
        """
        Retrieves matching episodes for a symbol, file, or search query.
        """
        matches: List[EpisodicBugRecord] = []
        for ep in self._episodes.values():
            score = 0
            if symbol_name and (symbol_name in ep.target_symbol or ep.target_symbol in symbol_name):
                score += 3
            if file_path and (file_path in ep.file_path or ep.file_path in file_path):
                score += 2
            if query:
                q_lower = query.lower()
                if ep.target_symbol.lower() in q_lower or ep.error_signature.lower() in q_lower:
                    score += 2
                elif any(term in ep.root_cause_summary.lower() for term in q_lower.split() if len(term) > 3):
                    score += 1
            if score > 0:
                matches.append(ep)

        return matches[:limit]

    def all_episodes(self) -> List[EpisodicBugRecord]:
        return list(self._episodes.values())

    def clear(self) -> None:
        self._episodes.clear()
        if self.storage_path and self.storage_path.exists():
            self.storage_path.unlink()

    def _save(self) -> None:
        if not self.storage_path:
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = [ep.model_dump() for ep in self._episodes.values()]
        self.storage_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def _load(self) -> None:
        if not self.storage_path or not self.storage_path.exists():
            return
        try:
            content = self.storage_path.read_text(encoding="utf-8")
            data = json.loads(content)
            for item in data:
                ep = EpisodicBugRecord(**item)
                self._episodes[ep.episode_id] = ep
        except Exception:
            pass

