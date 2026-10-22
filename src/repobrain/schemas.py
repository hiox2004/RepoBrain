# src/repobrain/schemas.py
"""
Strict Pydantic v2 Data Contracts for RepoBrain V2 & ResearchBrain OS.
Governed strictly by 00_FOUNDING_ARCHITECTURE.md (Pillars 1-5).
Supports Pydantic v2 natively with a zero-dependency standard-library fallback.
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID, uuid4

try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

    class _FieldInfo:
        def __init__(self, default=..., default_factory=None, ge=None, le=None, description=None):
            self.default = default
            self.default_factory = default_factory
            self.ge = ge
            self.le = le
            self.description = description

    def Field(default=..., *, default_factory=None, ge=None, le=None, description=None):
        return _FieldInfo(default=default, default_factory=default_factory, ge=ge, le=le, description=description)

    class BaseModel:
        def __init__(self, **kwargs: Any) -> None:
            cls = self.__class__
            annotations = getattr(cls, "__annotations__", {})
            for name in annotations:
                default_val = getattr(cls, name, ...)
                if isinstance(default_val, _FieldInfo):
                    if name in kwargs:
                        val = kwargs[name]
                    elif default_val.default_factory is not None:
                        val = default_val.default_factory()
                    elif default_val.default is not ...:
                        val = default_val.default
                    else:
                        raise ValueError(f"Field '{name}' is required on {cls.__name__}")
                else:
                    if name in kwargs:
                        val = kwargs[name]
                    elif default_val is not ...:
                        val = default_val
                    else:
                        raise ValueError(f"Field '{name}' is required on {cls.__name__}")

                if isinstance(val, str) and annotations.get(name) in (UUID, Optional[UUID]):
                    val = UUID(val)
                setattr(self, name, val)

            for k, v in kwargs.items():
                if not hasattr(self, k):
                    setattr(self, k, v)

        def model_dump(self, mode: str = "python") -> dict[str, Any]:
            def _convert(v: Any) -> Any:
                if isinstance(v, BaseModel):
                    return v.model_dump(mode=mode)
                if isinstance(v, UUID):
                    return str(v)
                if isinstance(v, list):
                    return [_convert(item) for item in v]
                if isinstance(v, dict):
                    return {k: _convert(val) for k, val in v.items()}
                return v

            res = {}
            for k in getattr(self.__class__, "__annotations__", {}):
                val = getattr(self, k, None)
                res[k] = _convert(val)
            return res

        def dict(self) -> dict[str, Any]:
            return self.model_dump()

        def model_dump_json(self, indent: Optional[int] = None) -> str:
            return json.dumps(self.model_dump(mode="json"), indent=indent, default=str)

        def __repr__(self) -> str:
            attrs = ", ".join(f"{k}={getattr(self, k)!r}" for k in getattr(self.__class__, "__annotations__", {}))
            return f"{self.__class__.__name__}({attrs})"


# ============================================================================
# Layer 1: Structural AST Memory Contracts
# ============================================================================
class ASTParentNode(BaseModel):
    """File-level envelope capturing module context, imports, and Git blob SHA."""
    parent_id: UUID = Field(default_factory=uuid4)
    file_path: str = Field(..., description="Repo-relative POSIX path, UNIQUE in database")
    language: Literal["python", "typescript", "javascript", "rust", "go"]
    imports_header: str = Field(default="", description="Cleaned top-level imports block")
    enclosing_scope: Optional[str] = Field(default=None, description="Module or enclosing class name")
    git_blob_sha: str = Field(..., description="SHA-1 of blob {len}\\0{bytes}")


class ASTChildNode(BaseModel):
    """Searchable atomic code chunk: function, class method, or schema type."""
    child_id: UUID = Field(default_factory=uuid4)
    parent_id: UUID = Field(..., description="Foreign key referencing ASTParentNode")
    file_path: str = Field(..., description="Repo-relative path")
    node_kind: Literal["callable", "method", "type_definition"]
    symbol_name: str = Field(..., description="Fully qualified symbol name, e.g. LedgerService.settleInvoiceById")
    signature: str = Field(..., description="Signature including outer decorators")
    docstring: Optional[str] = Field(default=None)
    body_code: str = Field(..., description="Raw byte-sliced source block")
    start_line: int = Field(..., ge=1)
    end_line: int = Field(..., ge=1)


# ============================================================================
# Layer 2: Episodic Diagnostic Memory Contracts
# ============================================================================
class EpisodicBugRecord(BaseModel):
    """Distilled bug post-mortem capturing fail-to-pass transitions."""
    episode_id: UUID = Field(default_factory=uuid4)
    error_signature: str = Field(..., description="Normalized exception delta")
    target_symbol: str = Field(..., description="Target symbol identifier")
    file_path: str = Field(..., description="Repo-relative file path")
    root_cause_summary: str = Field(..., description="<= 40-word explanation")
    resolution_diff: str = Field(..., description="Verified minimal git diff")


# Alias for backward compatibility
EpisodicFixRecord = EpisodicBugRecord


# ============================================================================
# Layer 3: Conceptual ResearchBrain Contracts
# ============================================================================
class TechKnowledgeChunk(BaseModel):
    """Chunk from local ADRs, RFCs, or documentation in .repobrain/kb/."""
    chunk_id: UUID = Field(default_factory=uuid4)
    source_doc: str
    domain: str = "general"
    title: str
    content: str
    external_url: Optional[str] = None


class ResearchBrief(BaseModel):
    """Synthesized research brief returned by research_technology tool."""
    query: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    source: Literal["local_kb", "web_fallback", "parametric_fastpath"]
    summary_markdown: str
    cited_passages: List[str] = Field(default_factory=list)
    cached_slug: Optional[str] = None


# ============================================================================
# Layer 4: GitHub Template Stockroom Contracts
# ============================================================================
class TemplateBlueprint(BaseModel):
    """Verified production starter pattern from vetted repositories."""
    blueprint_id: UUID = Field(default_factory=uuid4)
    repo_name: str = Field(..., description="e.g. tiangolo/full-stack-fastapi-template")
    file_path: str
    symbol_name: str
    stack_domain: str = Field(..., description="e.g. fastapi, shadcn, fastmcp, taskiq")
    description: str
    code_snippet: str
    start_line: int = 1
    end_line: int = 1

    def to_advisory_markdown(self) -> str:
        return (
            f"### Scaffold Pattern: `{self.symbol_name}`\n"
            f"- **Source:** `{self.repo_name}` (`{self.file_path}#L{self.start_line}-L{self.end_line}`)\n"
            f"- **Domain:** `{self.stack_domain}`\n"
            f"- **Guidance:** {self.description}\n\n"
            f"```\n{self.code_snippet}\n```"
        )


# ============================================================================
# Retrieval & Context Contracts
# ============================================================================
class RetrievedCodeContext(BaseModel):
    """Final reranked search context returned by search_codebase."""
    file_path: str
    language: Literal["python", "typescript", "javascript", "rust", "go"]
    symbol_name: str
    node_kind: Literal["callable", "method", "type_definition"]
    start_line: int
    end_line: int
    git_blob_sha: str
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    rrf_score: float
    cross_encoder_score: float
    imports_header: str
    enclosing_scope: Optional[str] = None
    body_code: str
    related_episodes: List[EpisodicBugRecord] = Field(default_factory=list)

    def to_xml_prompt_block(self) -> str:
        episodes_xml = ""
        if self.related_episodes:
            items = "\n".join(
                f'    <past_episodic_fix symbol="{ep.target_symbol}" error="{ep.error_signature}">\n'
                f'      <root_cause>{ep.root_cause_summary}</root_cause>\n'
                f'      <proven_diff>\n{ep.resolution_diff}\n      </proven_diff>\n'
                f'    </past_episodic_fix>'
                for ep in self.related_episodes
            )
            episodes_xml = f"\n  <episodic_memory>\n{items}\n  </episodic_memory>"

        scope_block = f"\n  <enclosing_scope>\n{self.enclosing_scope}\n  </enclosing_scope>" if self.enclosing_scope else ""
        return (
            f'<ast_context file="{self.file_path}" symbol="{self.symbol_name}" '
            f'kind="{self.node_kind}" lines="{self.start_line}-{self.end_line}" '
            f'sha="{self.git_blob_sha}" rrf="{self.rrf_score:.6f}" rerank="{self.cross_encoder_score:.4f}">\n'
            f'  <parent_imports>\n{self.imports_header}\n  </parent_imports>{scope_block}\n'
            f'  <child_body>\n{self.body_code}\n  </child_body>{episodes_xml}\n'
            f'</ast_context>'
        )


# ============================================================================
# Bounded Harness Contracts
# ============================================================================
class PatchAndTestResponse(BaseModel):
    """Standardized response emitted by apply_git_patch."""
    task_id: str
    iteration: int = Field(..., ge=0, le=3)
    patch_applied: bool
    static_check_passed: bool = True
    tests_passed: bool
    exit_code: int
    rolled_back: bool
    filtered_traceback: str
    reindexed_files: List[str]
    recorded_episode_id: Optional[str] = None
