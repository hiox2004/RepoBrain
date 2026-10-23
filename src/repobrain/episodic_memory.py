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

    def promote_recurring_to_adrs(self, repo_root: Path, min_count: int = 3) -> List[Path]:
        """
        Tier 2 Self-Learning Compounding Loop:
        Clusters episodes by error signature / root cause keywords.
        When an issue recurs >= min_count times, auto-synthesizes an Architectural Decision Record
        into .repobrain/kb/adrs/ and returns list of created ADR paths.
        """
        import re
        import datetime
        from collections import defaultdict

        clusters: Dict[str, List[EpisodicBugRecord]] = defaultdict(list)
        for ep in self._episodes.values():
            # Strip numbers and punctuation to cluster identical logical errors
            clean_sig = re.sub(r"[\d\'\"]+", "", ep.error_signature.splitlines()[-1] if ep.error_signature else "")
            sig_tokens = [t.lower() for t in re.findall(r"[a-zA-Z_]+", clean_sig) if len(t) > 2 and t.lower() not in ("traceback", "file", "line")]
            cause_tokens = [t.lower() for t in re.findall(r"[a-zA-Z_]+", ep.root_cause_summary) if len(t) > 3]
            combined = sig_tokens[:2] + cause_tokens[:2]
            cluster_key = "_".join(combined) if combined else "generic_regression"
            clusters[cluster_key].append(ep)

        promoted_paths: List[Path] = []
        adrs_dir = repo_root / ".repobrain" / "kb" / "adrs"
        adrs_dir.mkdir(parents=True, exist_ok=True)

        for cluster_key, group in clusters.items():
            if len(group) >= min_count:
                slug = cluster_key[:48]
                target_adr = adrs_dir / f"ADR_auto_{slug}.md"
                if target_adr.exists():
                    continue

                affected_symbols = list({ep.target_symbol for ep in group})
                error_signatures = list({ep.error_signature for ep in group})
                latest = group[-1]

                adr_content = (
                    f"# ADR: Auto-Promoted Policy for `{cluster_key.replace('_', ' ').title()}`\n\n"
                    f"**Status:** Enforced Architectural Policy (Auto-Promoted via Tier 2 Self-Learning)\n"
                    f"**Created:** {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n"
                    f"**Recurrence Count:** {len(group)} verified fixes across the codebase\n\n"
                    f"## 1. Problem Statement & Symptoms\n"
                    f"This failure pattern occurred {len(group)} times across multiple modules:\n"
                    + "\n".join(f"- `{sym}`: *{sig}*" for sym, sig in zip(affected_symbols[:5], error_signatures[:5]))
                    + f"\n\n## 2. Enforced Architectural Rule & Root Cause\n"
                    f"{latest.root_cause_summary}\n\n"
                    f"## 3. Proven Minimal Fix Pattern (Reference Diff)\n"
                    f"```diff\n{latest.resolution_diff}\n```\n\n"
                    f"## 4. Policy Enforcement\n"
                    f"All coding agents modifying these namespaces must adhere to this pattern. "
                    f"This document is indexed directly by Layer 3 CRAG at 0 external token cost.\n"
                )

                target_adr.write_text(adr_content, encoding="utf-8")
                promoted_paths.append(target_adr)

        return promoted_paths

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

