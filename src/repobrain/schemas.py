# src/repobrain/schemas.py
"""
Strict Pydantic v2 Data Contracts for RepoBrain
Governed strictly by REPOBRAIN_MASTER_CONTEXT_SPEC.md Section 5.
Includes seamless fallback support for pure Python standard library environments.
"""

from __future__ import annotations
import json
from typing import Any, List, Literal, Optional, Union
from uuid import UUID, uuid4

try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    
    # Standard-library fallback preserving exact Pydantic v2 behavior & validation
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
            # Collect class annotations and defaults
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
                
                # Coerce UUIDs
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


class ASTParentNode(BaseModel):
    parent_id: UUID = Field(default_factory=uuid4)
    file_path: str = Field(..., description="Repo-relative POSIX path, UNIQUE in DB")
    language: Literal["python", "typescript"]
    imports_header: str
    enclosing_scope: Optional[str] = None
    git_blob_sha: str


class ASTChildNode(BaseModel):
    child_id: UUID = Field(default_factory=uuid4)
    parent_id: UUID
    file_path: str
    node_kind: Literal["callable", "method", "type_definition"]
    symbol_name: str
    signature: str
    docstring: Optional[str] = None
    body_code: str
    start_line: int = Field(..., ge=1)
    end_line: int = Field(..., ge=1)


class EpisodicFixRecord(BaseModel):
    episode_id: UUID = Field(default_factory=uuid4)
    error_signature: str
    target_symbol: str
    file_path: str
    root_cause_summary: str
    resolution_diff: str


class RetrievedCodeContext(BaseModel):
    file_path: str
    language: Literal["python", "typescript"]
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
    related_episodes: List[EpisodicFixRecord] = Field(default_factory=list)

    def to_xml_prompt_block(self) -> str:
        episodes_xml = ""
        if self.related_episodes:
            items = "\n".join(
                f'    <past_episodic_fix symbol="{ep.target_symbol}" error="{ep.error_signature}">\n'
                f'      <root_cause>{ep.root_cause_summary}</root_cause>\n'
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


class PatchAndTestResponse(BaseModel):
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
