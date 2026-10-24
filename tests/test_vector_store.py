# tests/test_vector_store.py
"""
Test Suite for RepoBrain Embedded Persistent Vector Cache.
Verifies TF-IDF vector generation, cosine similarity scoring, and disk persistence.
"""

import sys
import unittest
from pathlib import Path
from uuid import uuid4

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repobrain.schemas import ASTChildNode
from repobrain.vector_store import EmbeddedVectorIndex


class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.test_root = Path("test_scratch_vectors").resolve()
        self.test_root.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.test_root / "vector_cache.json"
        self.index = EmbeddedVectorIndex(cache_file_path=self.cache_file)

    def tearDown(self):
        import shutil
        if self.test_root.exists():
            shutil.rmtree(self.test_root, ignore_errors=True)

    def test_vector_indexing_and_cosine_search(self):
        child1 = ASTChildNode(
            child_id=uuid4(),
            parent_id=uuid4(),
            file_path="src/billing/ledger.py",
            node_kind="method",
            symbol_name="LedgerService.settleInvoiceById",
            signature="def settleInvoiceById(self, req: InvoiceRequest) -> Decimal:",
            docstring="Calculates invoice settlement with decimal quantization.",
            body_code="return req.subtotal * Decimal('1.20')",
            start_line=10,
            end_line=15,
        )

        child2 = ASTChildNode(
            child_id=uuid4(),
            parent_id=uuid4(),
            file_path="src/auth/jwt.py",
            node_kind="callable",
            symbol_name="verify_jwt_token",
            signature="def verify_jwt_token(token: str) -> dict:",
            docstring="Verifies RS256 JWT bearer signature.",
            body_code="return jwt.decode(token, key, algorithms=['RS256'])",
            start_line=1,
            end_line=5,
        )

        self.index.index_child(child1, "sha-ledger")
        self.index.index_child(child2, "sha-jwt")
        self.assertEqual(self.index.size(), 2)

        # Query matching child1
        results = self.index.search_top_k("settle invoice decimal quantization", top_k=2)
        self.assertGreaterEqual(len(results), 1)
        top_cid, top_score = results[0]
        self.assertEqual(top_cid, str(child1.child_id))
        self.assertGreater(top_score, 0.4)

        # Save to disk and reload
        self.assertTrue(self.index.save())
        self.assertTrue(self.cache_file.exists())

        new_index = EmbeddedVectorIndex(cache_file_path=self.cache_file)
        self.assertEqual(new_index.size(), 2)


if __name__ == "__main__":
    unittest.main()
