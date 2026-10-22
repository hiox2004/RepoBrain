# tests/test_storage_sqlite.py
"""
Test Suite for SQLite Persistent Storage Tier.
Validates zero-setup single-file persistence across all 4 layers.
Compatible with pytest and python -m unittest.
"""

import sys
import unittest
from pathlib import Path
from uuid import uuid4

# Ensure src is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.schemas import (
    ASTChildNode,
    ASTParentNode,
    EpisodicBugRecord,
    TechKnowledgeChunk,
    TemplateBlueprint,
)
from repobrain.storage_sqlite import SQLiteStorageTier


class TestSQLiteStorageTier(unittest.TestCase):
    def setUp(self):
        self.test_db_path = Path("test_scratch_db") / "test_repobrain.db"
        self.storage = SQLiteStorageTier(db_path=self.test_db_path)

    def tearDown(self):
        self.storage.close()
        import shutil
        if self.test_db_path.parent.exists():
            shutil.rmtree(self.test_db_path.parent)

    def test_layer1_parent_and_children_upsert(self):
        p_id = uuid4()
        parent = ASTParentNode(
            parent_id=p_id,
            file_path="src/billing/ledger.py",
            language="python",
            imports_header="from decimal import Decimal",
            enclosing_scope=None,
            git_blob_sha="abc123sha",
        )
        child = ASTChildNode(
            child_id=uuid4(),
            parent_id=p_id,
            file_path="src/billing/ledger.py",
            node_kind="callable",
            symbol_name="settleInvoiceById",
            signature="def settleInvoiceById():",
            docstring="Settles invoice",
            body_code="def settleInvoiceById(): return 100",
            start_line=1,
            end_line=2,
        )

        self.storage.upsert_parent_and_children(parent, [child])

        loaded_parent = self.storage.get_parent_by_path("src/billing/ledger.py")
        self.assertIsNotNone(loaded_parent)
        self.assertEqual(loaded_parent.git_blob_sha, "abc123sha")

        all_nodes = self.storage.get_all_children_with_parents()
        self.assertEqual(len(all_nodes), 1)
        p, c = all_nodes[0]
        self.assertEqual(c.symbol_name, "settleInvoiceById")

    def test_layer2_episodic_memory_persistence(self):
        ep = EpisodicBugRecord(
            episode_id=uuid4(),
            error_signature="AssertionError: 120.0000 != 120.00",
            target_symbol="LedgerService.settleInvoiceById",
            file_path="src/billing/ledger.py",
            root_cause_summary="Decimal scale mismatch requires explicit quantization.",
            resolution_diff="--- patch",
        )
        self.storage.record_episode(ep)

        matches = self.storage.find_matching_episodes(symbol_name="settleInvoiceById")
        self.assertEqual(len(matches), 1)
        self.assertIn("quantization", matches[0].root_cause_summary)

    def test_layer3_tech_knowledge_persistence(self):
        chunk = TechKnowledgeChunk(
            chunk_id=uuid4(),
            source_doc="rfcs/oauth2.md",
            domain="security",
            title="OAuth2 Bearer Token Flow",
            content="Use Annotated[str, Depends(oauth2_scheme)] to decode JWT tokens securely.",
        )
        self.storage.add_tech_chunk(chunk)

        results = self.storage.search_tech_chunks("OAuth2 Bearer Token")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "OAuth2 Bearer Token Flow")

    def test_layer4_template_blueprints_persistence(self):
        bp = TemplateBlueprint(
            blueprint_id=uuid4(),
            repo_name="tiangolo/full-stack-fastapi-template",
            file_path="backend/app/deps.py",
            symbol_name="get_current_user",
            stack_domain="fastapi",
            description="FastAPI dependency injection pattern.",
            code_snippet="def get_current_user(): pass",
        )
        self.storage.add_blueprint(bp)

        results = self.storage.search_blueprints("get_current_user", stack_domain="fastapi")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].symbol_name, "get_current_user")


if __name__ == "__main__":
    unittest.main()

