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
            bp_tokens = set(re.findall(r"\w+", text))
            intersection = q_tokens.intersection(bp_tokens)
            score = len(intersection) / max(1, len(q_tokens))

            if bp.symbol_name.lower() in query.lower() or bp.stack_domain.lower() in query.lower():
                score += 0.5

            if score > 0.1:
                matches.append((score, bp))

        matches.sort(key=lambda x: x[0], reverse=True)
        return [bp for _, bp in matches[:limit]]

    def add_blueprint(self, blueprint: TemplateBlueprint) -> None:
        self._blueprints.append(blueprint)

