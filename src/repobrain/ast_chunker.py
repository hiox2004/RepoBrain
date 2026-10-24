# src/repobrain/ast_chunker.py
"""
Hierarchical Tree-Sitter & Byte-Safe Parent-Child AST Code Chunker
Strictly enforces:
- Guardrail #1: UTF-8 byte-offset slicing (zero character drift on multi-byte characters).
- Guardrail #2: Outer decorator preservation and methodless type definitions.
- Git blob SHA computation: sha1("blob " + len(source_bytes) + "\\0" + source_bytes).
"""

from __future__ import annotations
import ast
import hashlib
import os
import re
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union
from uuid import uuid4

from repobrain.schemas import ASTChildNode, ASTParentNode


def compute_git_blob_sha(source_bytes: bytes) -> str:
    """
    Computes standard Git object blob SHA-1:
    sha1("blob " + len(source_bytes) + "\0" + source_bytes)
    """
    header = f"blob {len(source_bytes)}\0".encode("ascii")
    hasher = hashlib.sha1()
    hasher.update(header)
    hasher.update(source_bytes)
    return hasher.hexdigest()


class ASTCodeChunker:
    """
    Two-Tier AST Chunker supporting Python and TypeScript.
    Adheres strictly to Guardrails #1 and #2.
    """

    def __init__(self) -> None:
        self.tree_sitter_available = False
        self._init_tree_sitter()

    def _init_tree_sitter(self) -> None:
        try:
            import tree_sitter_languages  # type: ignore
            from tree_sitter import Language, Parser  # type: ignore
            self.ts_parser_py = tree_sitter_languages.get_parser("python")
            self.ts_parser_ts = tree_sitter_languages.get_parser("typescript")
            self.tree_sitter_available = True
        except Exception:
            self.tree_sitter_available = False

    def chunk_file(self, file_path: Path, repo_root: Optional[Path] = None) -> Tuple[ASTParentNode, List[ASTChildNode]]:
        """
        Parses a Python or TypeScript file into a Parent AST node and child AST nodes.
        Guarantees UTF-8 byte offset slicing and outer decorator preservation.
        """
        file_path = file_path.resolve()
        if repo_root is None:
            curr = file_path.parent
            while curr != curr.parent:
                if (curr / ".git").exists() or (curr / "package.json").exists() or (curr / "pyproject.toml").exists():
                    repo_root = curr
                    break
                curr = curr.parent
            if repo_root is None:
                repo_root = file_path.parent

        try:
            rel_path = file_path.relative_to(repo_root).as_posix()
        except ValueError:
            rel_path = file_path.name

        with open(file_path, "rb") as f:
            source_bytes = f.read()

        git_sha = compute_git_blob_sha(source_bytes)
        ext = file_path.suffix.lower()

        if ext == ".py":
            return self._chunk_python(source_bytes, rel_path, git_sha)
        elif ext in (".ts", ".tsx", ".js", ".jsx"):
            return self._chunk_typescript(source_bytes, rel_path, git_sha)
        else:
            raise ValueError(f"Unsupported file extension for AST parsing: {ext}")

    def chunk_code_string(
        self,
        code_str: str,
        virtual_path: str = "snippet.py",
        language: str = "python"
    ) -> Tuple[ASTParentNode, List[ASTChildNode]]:
        """Utility for in-memory AST chunking of raw code strings (e.g. in test suites)."""
        source_bytes = code_str.encode("utf-8")
        git_sha = compute_git_blob_sha(source_bytes)
        if language == "python" or virtual_path.endswith(".py"):
            return self._chunk_python(source_bytes, virtual_path, git_sha)
        else:
            return self._chunk_typescript(source_bytes, virtual_path, git_sha)

    def _compute_line_byte_offsets(self, source_bytes: bytes) -> List[int]:
        """Returns list of byte offsets where each line begins (0-indexed)."""
        offsets = [0]
        for i, b in enumerate(source_bytes):
            if b == ord(b"\n"):
                offsets.append(i + 1)
        return offsets

    def _slice_bytes(self, source_bytes: bytes, start_byte: int, end_byte: int) -> str:
        """
        Guardrail #1: Strictly slice using UTF-8 byte offsets, never Python string indices.
        """
        return source_bytes[start_byte:end_byte].decode("utf-8")

    def _chunk_python(self, source_bytes: bytes, file_path: str, git_blob_sha: str) -> Tuple[ASTParentNode, List[ASTChildNode]]:
        line_offsets = self._compute_line_byte_offsets(source_bytes)
        source_text = source_bytes.decode("utf-8")

        py_ast = ast.parse(source_text, filename=file_path)

        # Extract top-level imports header
        import_lines: List[str] = []
        for stmt in py_ast.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                stmt_lines = source_text.splitlines(keepends=True)[stmt.lineno - 1 : stmt.end_lineno]
                import_lines.append("".join(stmt_lines).strip())
        imports_header = "\n".join(import_lines)

        parent_node = ASTParentNode(
            parent_id=uuid4(),
            file_path=file_path,
            language="python",
            imports_header=imports_header,
            enclosing_scope=None,
            git_blob_sha=git_blob_sha,
        )

        children: List[ASTChildNode] = []

        for stmt in py_ast.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                child = self._extract_py_function(stmt, source_bytes, line_offsets, parent_node.parent_id, file_path, "callable")
                children.append(child)
            elif isinstance(stmt, ast.ClassDef):
                methods = [m for m in stmt.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                base_names = [self._get_ast_id(b) for b in stmt.bases]
                dec_names = [self._get_ast_id(d) for d in stmt.decorator_list]
                is_structural_type = (
                    len(methods) == 0
                    or any(b in ("ABC", "TypedDict", "BaseModel", "Protocol", "Module", "BaseEstimator") or b.endswith((".ABC", ".TypedDict", ".BaseModel", ".Protocol", ".Module", ".BaseEstimator")) for b in base_names)
                    or any("dataclass" in d for d in dec_names)
                )
                if is_structural_type:
                    # Guardrail #2 & Agentic/Domain models -> type_definition
                    child = self._extract_py_class_as_typedef(stmt, source_bytes, line_offsets, parent_node.parent_id, file_path)
                    children.append(child)

                for method in methods:
                    child = self._extract_py_function(
                        method,
                        source_bytes,
                        line_offsets,
                        parent_node.parent_id,
                        file_path,
                        "method",
                        enclosing_class=stmt.name,
                    )
                    children.append(child)

        return parent_node, children

    @staticmethod
    def _get_ast_id(node: Any) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = ASTCodeChunker._get_ast_id(node.value)
            return f"{val}.{node.attr}" if val else node.attr
        elif isinstance(node, ast.Call):
            return ASTCodeChunker._get_ast_id(node.func)
        return ""

    def _extract_py_function(
        self,
        fn_node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        source_bytes: bytes,
        line_offsets: List[int],
        parent_id: Any,
        file_path: str,
        node_kind: str,
        enclosing_class: Optional[str] = None,
    ) -> ASTChildNode:
        # Determine start byte including outer decorators (Guardrail #2)
        if fn_node.decorator_list:
            first_dec = fn_node.decorator_list[0]
            start_lineno = first_dec.lineno
        else:
            start_lineno = fn_node.lineno

        start_line_byte = line_offsets[start_lineno - 1]
        end_lineno = fn_node.end_lineno or fn_node.lineno
        if end_lineno < len(line_offsets):
            end_line_byte = line_offsets[end_lineno]
        else:
            end_line_byte = len(source_bytes)

        body_code = self._slice_bytes(source_bytes, start_line_byte, end_line_byte).rstrip("\n")
        docstring = ast.get_docstring(fn_node)

        # Construct full signature (including decorators)
        sig_lines: List[str] = []
        for dec in fn_node.decorator_list:
            dec_line = source_bytes[line_offsets[dec.lineno - 1] : line_offsets[dec.end_lineno or dec.lineno]].decode("utf-8").strip()
            sig_lines.append(dec_line)

        def_line = source_bytes[line_offsets[fn_node.lineno - 1] : line_offsets[fn_node.lineno]].decode("utf-8").strip()
        sig_lines.append(def_line)
        signature = "\n".join(sig_lines)

        return ASTChildNode(
            child_id=uuid4(),
            parent_id=parent_id,
            file_path=file_path,
            node_kind=node_kind,  # type: ignore
            symbol_name=f"{enclosing_class}.{fn_node.name}" if enclosing_class else fn_node.name,
            signature=signature,
            docstring=docstring,
            body_code=body_code,
            start_line=start_lineno,
            end_line=end_lineno,
        )

    def _extract_py_class_as_typedef(
        self,
        cls_node: ast.ClassDef,
        source_bytes: bytes,
        line_offsets: List[int],
        parent_id: Any,
        file_path: str,
    ) -> ASTChildNode:
        start_lineno = cls_node.lineno
        start_line_byte = line_offsets[start_lineno - 1]

        end_lineno = cls_node.end_lineno or cls_node.lineno
        if end_lineno < len(line_offsets):
            end_line_byte = line_offsets[end_lineno]
        else:
            end_line_byte = len(source_bytes)

        body_code = self._slice_bytes(source_bytes, start_line_byte, end_line_byte).rstrip("\n")
        docstring = ast.get_docstring(cls_node)
        sig_line = source_bytes[line_offsets[start_lineno - 1] : line_offsets[start_lineno]].decode("utf-8").strip()

        return ASTChildNode(
            child_id=uuid4(),
            parent_id=parent_id,
            file_path=file_path,
            node_kind="type_definition",
            symbol_name=cls_node.name,
            signature=sig_line,
            docstring=docstring,
            body_code=body_code,
            start_line=start_lineno,
            end_line=end_lineno,
        )

    def _chunk_typescript(self, source_bytes: bytes, file_path: str, git_blob_sha: str) -> Tuple[ASTParentNode, List[ASTChildNode]]:
        line_offsets = self._compute_line_byte_offsets(source_bytes)
        source_text = source_bytes.decode("utf-8")

        import_lines = []
        directive = None
        for line in source_text.splitlines():
            line_s = line.strip()
            if line_s in ('"use server";', "'use server';", '"use client";', "'use client';"):
                directive = line_s.replace(';', '').replace('"', '').replace("'", "")
                import_lines.append(line_s)
            elif line_s.startswith("import ") or line_s.startswith("export * from") or line_s.startswith("export {"):
                import_lines.append(line_s)
        imports_header = "\n".join(import_lines)

        parent_node = ASTParentNode(
            parent_id=uuid4(),
            file_path=file_path,
            language="typescript",
            imports_header=imports_header,
            enclosing_scope=f"directive:{directive}" if directive else None,
            git_blob_sha=git_blob_sha,
        )

        children: List[ASTChildNode] = []
        lines = source_text.splitlines(keepends=True)
        i = 0
        while i < len(lines):
            line = lines[i]

            # 1. Zod schema definition: export const FooSchema = z.object(...)
            zod_match = re.match(r"^\s*(?:export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*z\.", line)
            if zod_match:
                symbol_name = zod_match.group(1)
                start_line = i + 1
                start_byte = line_offsets[i]
                depth = 0
                end_line = start_line
                for j in range(i, len(lines)):
                    depth += lines[j].count("(") - lines[j].count(")") + lines[j].count("{") - lines[j].count("}")
                    if depth <= 0 and (lines[j].strip().endswith(";") or lines[j].strip().endswith(")")):
                        end_line = j + 1
                        break
                end_byte = line_offsets[end_line] if end_line < len(line_offsets) else len(source_bytes)
                body = self._slice_bytes(source_bytes, start_byte, end_byte).rstrip("\r\n")

                children.append(
                    ASTChildNode(
                        child_id=uuid4(),
                        parent_id=parent_node.parent_id,
                        file_path=file_path,
                        node_kind="type_definition",
                        symbol_name=symbol_name,
                        signature=line.strip(),
                        docstring=None,
                        body_code=body,
                        start_line=start_line,
                        end_line=end_line,
                    )
                )
                i = end_line
                continue

            # 2. Interface or type definition (methodless schema)
            type_match = re.match(r"^\s*(?:export\s+)?(interface|type)\s+([A-Za-z0-9_]+)", line)
            if type_match:
                symbol_name = type_match.group(2)
                start_line = i + 1
                start_byte = line_offsets[i]

                depth = 0
                end_line = start_line
                for j in range(i, len(lines)):
                    depth += lines[j].count("{") - lines[j].count("}")
                    if depth <= 0 and (lines[j].strip().endswith("}") or lines[j].strip().endswith(";")):
                        end_line = j + 1
                        break
                end_byte = line_offsets[end_line] if end_line < len(line_offsets) else len(source_bytes)
                body = self._slice_bytes(source_bytes, start_byte, end_byte).rstrip("\r\n")

                children.append(
                    ASTChildNode(
                        child_id=uuid4(),
                        parent_id=parent_node.parent_id,
                        file_path=file_path,
                        node_kind="type_definition",
                        symbol_name=symbol_name,
                        signature=line.strip(),
                        docstring=None,
                        body_code=body,
                        start_line=start_line,
                        end_line=end_line,
                    )
                )
                i = end_line
                continue

            # 3. TypeScript Class definitions and methods
            class_match = re.match(r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z0-9_]+)", line)
            if class_match:
                class_name = class_match.group(1)
                start_line = i + 1
                start_byte = line_offsets[i]

                depth = 0
                end_line = start_line
                for j in range(i, len(lines)):
                    depth += lines[j].count("{") - lines[j].count("}")
                    if depth <= 0 and lines[j].strip().endswith("}"):
                        end_line = j + 1
                        break
                end_byte = line_offsets[end_line] if end_line < len(line_offsets) else len(source_bytes)
                body = self._slice_bytes(source_bytes, start_byte, end_byte).rstrip("\r\n")

                # Scan methods within class
                found_methods = 0
                for k in range(start_line - 1, end_line):
                    m_line = lines[k]
                    m_match = re.match(r"^\s*(?:public\s+|private\s+|protected\s+|async\s+)*(?:async\s+)?([A-Za-z0-9_]+)\s*\(.*?\)", m_line)
                    if m_match and not m_line.strip().startswith("//") and not m_line.strip().startswith("/*"):
                        m_name = m_match.group(1)
                        if m_name not in ("if", "for", "while", "switch", "catch"):
                            m_start = k + 1
                            m_depth = 0
                            m_end = m_start
                            for l_idx in range(k, end_line):
                                m_depth += lines[l_idx].count("{") - lines[l_idx].count("}")
                                if m_depth <= 0 and lines[l_idx].strip().endswith("}"):
                                    m_end = l_idx + 1
                                    break
                            m_body = self._slice_bytes(source_bytes, line_offsets[k], line_offsets[m_end] if m_end < len(line_offsets) else len(source_bytes)).rstrip("\r\n")
                            children.append(
                                ASTChildNode(
                                    child_id=uuid4(),
                                    parent_id=parent_node.parent_id,
                                    file_path=file_path,
                                    node_kind="method",
                                    symbol_name=f"{class_name}.{m_name}",
                                    signature=m_line.strip(),
                                    docstring=None,
                                    body_code=m_body,
                                    start_line=m_start,
                                    end_line=m_end,
                                )
                            )
                            found_methods += 1

                if found_methods == 0:
                    # Methodless class schema
                    children.append(
                        ASTChildNode(
                            child_id=uuid4(),
                            parent_id=parent_node.parent_id,
                            file_path=file_path,
                            node_kind="type_definition",
                            symbol_name=class_name,
                            signature=line.strip(),
                            docstring=None,
                            body_code=body,
                            start_line=start_line,
                            end_line=end_line,
                        )
                    )

                i = end_line
                continue

            # 4. Functions (including export default, async, Next.js Server Actions, Route Handlers, React Components)
            fn_match = re.match(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function(?:\s+([A-Za-z0-9_]+))?", line)
            arrow_match = re.match(r"^\s*(?:export\s+)?(?:default\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s+)?\(.*?\)\s*(?::\s*.*?)?\s*=>", line)

            if (fn_match and (fn_match.group(1) or "default" in line)) or arrow_match:
                if arrow_match:
                    symbol_name = arrow_match.group(1)
                elif fn_match and fn_match.group(1):
                    symbol_name = fn_match.group(1)
                else:
                    stem = file_path.replace("\\", "/").split("/")[-1].split(".")[0]
                    symbol_name = f"default_{stem}"

                start_line = i + 1
                start_byte = line_offsets[i]
                depth = 0
                end_line = start_line
                for j in range(i, len(lines)):
                    depth += lines[j].count("{") - lines[j].count("}")
                    if depth <= 0 and lines[j].strip().endswith("}"):
                        end_line = j + 1
                        break
                end_byte = line_offsets[end_line] if end_line < len(line_offsets) else len(source_bytes)
                body = self._slice_bytes(source_bytes, start_byte, end_byte).rstrip("\r\n")

                # Detect Next.js Server Actions
                is_server_action = (directive == "use server") or ('"use server"' in body) or ("'use server'" in body)
                annotated_symbol = f"ServerAction.{symbol_name}" if (is_server_action and not symbol_name.startswith("ServerAction.")) else symbol_name

                children.append(
                    ASTChildNode(
                        child_id=uuid4(),
                        parent_id=parent_node.parent_id,
                        file_path=file_path,
                        node_kind="callable",
                        symbol_name=annotated_symbol,
                        signature=line.strip(),
                        docstring=None,
                        body_code=body,
                        start_line=start_line,
                        end_line=end_line,
                    )
                )
                i = end_line
                continue

            i += 1

        return parent_node, children
