# tests/test_agentic_data_science.py
"""
Test Suite for Agentic AI (LangGraph/LangChain), Data Science (Polars/PyTorch),
and Clean Architecture Intelligence in RepoBrain.
"""

import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.ast_chunker import ASTCodeChunker
from repobrain.template_stockroom import TemplateStockroom
from repobrain.research_brain import ResearchBrainEngine


class TestAgenticDataScience(unittest.TestCase):
    def setUp(self):
        self.chunker = ASTCodeChunker()
        self.stockroom = TemplateStockroom()
        self.research_brain = ResearchBrainEngine()

    def test_agentic_ai_and_tool_chunking(self):
        code = '''
from typing import TypedDict
from langchain_core.tools import tool

class AgentState(TypedDict):
    query: str
    tokens_consumed: int

@tool
def calculate_blast_radius(symbol: str) -> dict:
    """Calculates call graph impact for a symbol."""
    return {"symbol": symbol, "risk": "LOW"}
'''
        parent, children = self.chunker.chunk_code_string(code, virtual_path="agent.py", language="python")
        self.assertGreaterEqual(len(children), 2)

        symbols = {c.symbol_name: c for c in children}
        self.assertIn("AgentState", symbols)
        self.assertEqual(symbols["AgentState"].node_kind, "type_definition")

        self.assertIn("calculate_blast_radius", symbols)
        self.assertIn("@tool", symbols["calculate_blast_radius"].signature)

    def test_pytorch_and_polars_data_science_chunking(self):
        code = '''
import torch
import torch.nn as nn
import polars as pl

class LinearClassifier(nn.Module):
    def __init__(self, d_in: int, d_out: int):
        super().__init__()
        self.linear = nn.Linear(d_in, d_out)
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)

def aggregate_telemetry(df: pl.LazyFrame) -> pl.DataFrame:
    """Aggregates telemetry stream."""
    return df.group_by("service").agg(pl.col("latency").mean()).collect()
'''
        parent, children = self.chunker.chunk_code_string(code, virtual_path="model.py", language="python")
        symbols = {c.symbol_name: c for c in children}

        self.assertIn("aggregate_telemetry", symbols)
        self.assertEqual(symbols["aggregate_telemetry"].node_kind, "callable")
        self.assertIn("LinearClassifier", symbols)
        self.assertEqual(symbols["LinearClassifier"].node_kind, "type_definition")
        self.assertIn("LinearClassifier.forward", symbols)
        self.assertEqual(symbols["LinearClassifier.forward"].node_kind, "method")

    def test_template_stockroom_agentic_and_data_blueprints(self):
        # 1. Agentic AI Blueprint
        agentic_bps = self.stockroom.search_templates("LangGraph MultiAgentSupervisor", stack_domain="agentic_ai")
        self.assertGreaterEqual(len(agentic_bps), 1)
        self.assertIn("StateGraph", agentic_bps[0].code_snippet)

        # 2. Polars Data Science Blueprint
        polars_bps = self.stockroom.search_templates("Polars DataAnalyticsPipeline", stack_domain="data_science")
        self.assertGreaterEqual(len(polars_bps), 1)
        self.assertIn("pl.scan_parquet", polars_bps[0].code_snippet)

        # 3. Clean Architecture Blueprint
        arch_bps = self.stockroom.search_templates("CleanHexagonalPorts", stack_domain="clean_architecture")
        self.assertGreaterEqual(len(arch_bps), 1)
        self.assertIn("CustomerRepositoryPort", arch_bps[0].code_snippet)

    def test_research_brain_agentic_and_data_adrs(self):
        # Local ADR hit on LangGraph
        brief = self.research_brain.research_technology("Agentic AI LangGraph StateGraph standards")
        self.assertGreaterEqual(brief.confidence_score, 0.75)
        self.assertIn("StateGraph", brief.summary_markdown)


if __name__ == "__main__":
    unittest.main()
