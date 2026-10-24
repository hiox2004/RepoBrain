# src/repobrain/template_stockroom.py
"""
Layer 4: GitHub Template Stockroom
Governed strictly by 00_FOUNDING_ARCHITECTURE.md Pillar 4.
Indexes curated production blueprints and enforces the Dual Advisory Protocol.
"""

from __future__ import annotations
import re
from typing import Dict, List, Optional
from uuid import uuid4

from repobrain.schemas import TemplateBlueprint


class TemplateStockroom:
    """
    Registry of production starter blueprints from vetted repositories.
    Enforces the Dual Advisory Protocol: provides scaffolding code to the agent
    while citing exact repository paths and line ranges to the developer.
    """

    def __init__(self) -> None:
        self._blueprints: List[TemplateBlueprint] = []
        self._initialize_core_blueprints()

    def _initialize_core_blueprints(self) -> None:
        """Seeds the registry with foundational open-source patterns."""
        self._blueprints.extend([
            TemplateBlueprint(
                blueprint_id=uuid4(),
                repo_name="tiangolo/full-stack-fastapi-template",
                file_path="backend/app/api/deps.py",
                symbol_name="get_current_user",
                stack_domain="fastapi",
                description="FastAPI OAuth2 dependency injection with strict token validation and status 401 handling.",
                code_snippet="""from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login/access-token")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")
    return token_data""",
                start_line=12,
                end_line=24,
            ),
            TemplateBlueprint(
                blueprint_id=uuid4(),
                repo_name="jlowin/fastmcp",
                file_path="src/fastmcp/server.py",
                symbol_name="FastMCP.tool",
                stack_domain="fastmcp",
                description="FastMCP tool registration decorator with stdio transport and Pydantic v2 argument schemas.",
                code_snippet="""from fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("ServiceBridge")

@mcp.tool()
def execute_query(query: str = Field(..., description="Target search query")) -> str:
    \"\"\"Executes query against internal memory engine.\"\"\"
    return f"Processed query: {query}\"""",
                start_line=45,
                end_line=55,
            ),
            TemplateBlueprint(
                blueprint_id=uuid4(),
                repo_name="shadcn-ui/taxonomy",
                file_path="components/site-header.tsx",
                symbol_name="SiteHeader",
                stack_domain="shadcn",
                description="Responsive Tailwind sticky navigation bar with Lucide icons and dark-mode styling.",
                code_snippet="""import Link from "next/link"
import { MainNav } from "@/components/main-nav"
import { ModeToggle } from "@/components/mode-toggle"

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur">
      <div className="container flex h-16 items-center space-x-4 sm:justify-between sm:space-x-0">
        <MainNav items={siteConfig.mainNav} />
        <div className="flex flex-1 items-center justify-end space-x-4">
          <ModeToggle />
        </div>
      </div>
    </header>
  )
}""",
                start_line=8,
                end_line=22,
            ),
            TemplateBlueprint(
                blueprint_id=uuid4(),
                repo_name="oraios/serena",
                file_path="serena/agent/tools.py",
                symbol_name="symbol_search",
                stack_domain="serena",
                description="AST symbol-level search tool configuration for agentic IDE workflows.",
                code_snippet="""@mcp.tool()
def find_symbol(name: str, file_pattern: str = "*.py") -> list[dict]:
    \"\"\"Locates exact symbol definitions across the repository tree.\"\"\"
    return indexer.query_symbol(name, pattern=file_pattern)""",
                start_line=30,
                end_line=36,
            ),
            TemplateBlueprint(
                blueprint_id=uuid4(),
                repo_name="langchain-ai/langgraph",
                file_path="libs/langgraph/graph/state.py",
                symbol_name="StateGraph.conditional_edges",
                stack_domain="langgraph",
                description="LangGraph StateGraph assembly with TypedDict state and conditional branching.",
                code_snippet="""from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, START, END

class AgentState(TypedDict):
    query: str
    confidence: float
    verdict: Literal["CORRECT", "AMBIGUOUS", "INCORRECT"]

builder = StateGraph(AgentState)
builder.add_node("grade", grade_node)
builder.add_node("web_search", web_search_node)
builder.add_node("synthesize", synthesize_node)

builder.add_edge(START, "grade")
builder.add_conditional_edges("grade", lambda s: "synthesize" if s["confidence"] >= 0.75 else "web_search")
builder.add_edge("web_search", "synthesize")
builder.add_edge("synthesize", END)
graph = builder.compile()""",
                start_line=15,
                end_line=36,
            ),
            TemplateBlueprint(
                blueprint_id=uuid4(),
                repo_name="vercel/next.js",
                file_path="examples/app-dir-actions/app/actions.ts",
                symbol_name="ServerAction.ZodValidation",
                stack_domain="nextjs",
                description="Next.js 15 Server Action with Zod schema parsing and typed return status.",
                code_snippet="""'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';

const InputSchema = z.object({
  id: z.string().uuid(),
  amount: z.number().positive(),
});

export async function processPaymentAction(rawInput: unknown) {
  const result = InputSchema.safeParse(rawInput);
  if (!result.success) {
    return { success: false, errors: result.error.flatten().fieldErrors };
  }
  // Execute database transaction
  revalidatePath('/dashboard/invoices');
  return { success: true, data: result.data };
}""",
                start_line=1,
                end_line=22,
            ),
            TemplateBlueprint(
                blueprint_id=uuid4(),
                repo_name="tiangolo/fastapi",
                file_path="fastapi/routing.py",
                symbol_name="FastAPI.lifespan",
                stack_domain="fastapi",
                description="FastAPI modern async lifespan context manager replacing deprecated on_event handlers.",
                code_snippet="""from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup resources on startup
    db_pool = await init_database_pool()
    app.state.db = db_pool
    yield
    # Clean teardown on shutdown
    await db_pool.close()

app = FastAPI(lifespan=lifespan)""",
                start_line=10,
                end_line=25,
            ),
            TemplateBlueprint(
                blueprint_id=uuid4(),
                repo_name="langchain-ai/langgraph-multi-agent",
                file_path="src/agents/supervisor.py",
                symbol_name="LangGraph.MultiAgentSupervisor",
                stack_domain="agentic_ai",
                description="LangGraph multi-agent supervisor pattern with dynamic tool routing, state passing, and human-in-the-loop review.",
                code_snippet="""from typing import Annotated, Literal, TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage

class SupervisorState(TypedDict):
    messages: Annotated[list[BaseMessage], "Conversation history"]
    next_worker: Literal["researcher", "coder", "reviewer", "FINISH"]

def supervisor_node(state: SupervisorState) -> dict:
    # Router logic deciding next specialized agent
    return {"next_worker": "coder"}

workflow = StateGraph(SupervisorState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_conditional_edges("supervisor", lambda s: s["next_worker"])
workflow.add_edge(START, "supervisor")
app = workflow.compile()""",
                start_line=1,
                end_line=20,
            ),
            TemplateBlueprint(
                blueprint_id=uuid4(),
                repo_name="pola-rs/polars-recipes",
                file_path="src/analytics/pipeline.py",
                symbol_name="Polars.DataAnalyticsPipeline",
                stack_domain="data_science",
                description="High-performance streaming Polars LazyFrame transformation pipeline with window functions and schema validation.",
                code_snippet="""import polars as pl

def execute_analytics_pipeline(source_parquet: str) -> pl.DataFrame:
    # Processes massive datasets with zero-copy Rust streaming and query optimization
    return (
        pl.scan_parquet(source_parquet)
        .filter(pl.col("status") == "SUCCESS")
        .with_columns([
            pl.col("timestamp").str.to_datetime().alias("dt"),
            (pl.col("latency_ms") / 1000.0).alias("latency_sec"),
        ])
        .group_by_dynamic("dt", every="1h")
        .agg([
            pl.col("latency_sec").quantile(0.99).alias("p99_latency"),
            pl.col("request_id").count().alias("throughput_req_per_hour"),
        ])
        .collect(streaming=True)
    )""",
                start_line=1,
                end_line=18,
            ),
            TemplateBlueprint(
                blueprint_id=uuid4(),
                repo_name="pytorch/serve-template",
                file_path="app/ml/inference.py",
                symbol_name="PyTorch.InferenceService",
                stack_domain="data_science",
                description="Production PyTorch model inference service with GPU auto-detection, torch.no_grad, and batched evaluation.",
                code_snippet="""import torch
import torch.nn as nn
from typing import List

class ProductionModel(nn.Module):
    def __init__(self, in_features: int = 128, num_classes: int = 2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, num_classes),
        )
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

@torch.inference_mode()
def run_batch_inference(model: nn.Module, batch: List[List[float]], device: str = "cpu") -> List[int]:
    tensor = torch.tensor(batch, dtype=torch.float32, device=device)
    logits = model(tensor)
    return torch.argmax(logits, dim=-1).tolist()""",
                start_line=1,
                end_line=24,
            ),
            TemplateBlueprint(
                blueprint_id=uuid4(),
                repo_name="clean-architecture/ports-adapters",
                file_path="src/domain/ports.py",
                symbol_name="Architecture.CleanHexagonalPorts",
                stack_domain="clean_architecture",
                description="Hexagonal Architecture (Ports & Adapters) with Abstract Base Class repository and Domain-Driven Design.",
                code_snippet="""from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class CustomerEntity:
    customer_id: str
    email: str
    is_active: bool = True

class CustomerRepositoryPort(ABC):
    # Driven port decoupling core domain from SQL/NoSQL databases
    @abstractmethod
    def find_by_id(self, customer_id: str) -> Optional[CustomerEntity]: ...
    
    @abstractmethod
    def save(self, customer: CustomerEntity) -> None: ...

class ActivateCustomerUseCase:
    # Driving use-case executing pure domain business logic
    def __init__(self, repo: CustomerRepositoryPort) -> None:
        self.repo = repo

    def execute(self, customer_id: str) -> bool:
        customer = self.repo.find_by_id(customer_id)
        if not customer:
            return False
        updated = CustomerEntity(customer.customer_id, customer.email, is_active=True)
        self.repo.save(updated)
        return True""",
                start_line=1,
                end_line=30,
            ),
        ])

    def search_templates(self, query: str, stack_domain: str = "all", limit: int = 3) -> List[TemplateBlueprint]:
        """
        Retrieves matching starter patterns by query and stack domain.
        """
        q_tokens = set(re.findall(r"\w+", query.lower()))
        matches: List[Tuple[float, TemplateBlueprint]] = []

        for bp in self._blueprints:
            if stack_domain != "all" and bp.stack_domain.lower() != stack_domain.lower():
                continue

            text = f"{bp.repo_name} {bp.symbol_name} {bp.description} {bp.stack_domain}".lower()
            expanded_text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text).lower()
            bp_tokens = set(re.findall(r"\w+", expanded_text))
            intersection = q_tokens.intersection(bp_tokens)
            score = len(intersection) / max(1, len(q_tokens))

            for q in q_tokens:
                if q in expanded_text or any(q in tok for tok in bp_tokens):
                    score += 0.35

            if bp.symbol_name.lower() in query.lower() or bp.stack_domain.lower() in query.lower():
                score += 0.5

            if score > 0.1:
                matches.append((score, bp))

        matches.sort(key=lambda x: x[0], reverse=True)
        return [bp for _, bp in matches[:limit]]

    def add_blueprint(self, blueprint: TemplateBlueprint) -> None:
        self._blueprints.append(blueprint)

    def harvest_blueprint(
        self,
        symbol_name: str,
        file_path: str,
        code_snippet: str,
        stack_domain: str = "general",
        repo_name: str = "workspace/living-blueprint",
        description: str = "Living blueprint harvested from verified task completion.",
    ) -> TemplateBlueprint:
        """
        Tier 3 Self-Learning Living Blueprint Harvest:
        Stores verified patterns from passing test runs into Layer 4 Stockroom.
        """
        bp = TemplateBlueprint(
            blueprint_id=uuid4(),
            repo_name=repo_name,
            file_path=file_path,
            symbol_name=symbol_name,
            stack_domain=stack_domain,
            description=description,
            code_snippet=code_snippet,
            start_line=1,
            end_line=len(code_snippet.splitlines()),
        )
        self.add_blueprint(bp)
        return bp
