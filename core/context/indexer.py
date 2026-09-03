"""Codebase Indexer supporting AST-based symbol extraction and incremental indexing."""

from __future__ import annotations

import ast
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("AIhenge.Indexer")


class FileSymbolIndex:
    """Symbols and imports extracted from a single source file."""

    def __init__(self, filepath: str, mtime: float):
        self.filepath = filepath
        self.mtime = mtime
        self.functions: List[Dict[str, Any]] = []
        self.classes: List[Dict[str, Any]] = []
        self.imports: List[str] = []
        self.docstring: Optional[str] = None


class CodebaseIndexer:
    """Parses project files incrementally and maintains an in-memory symbol graph."""

    IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache", "dist", "build", ".venv"}

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self._index_cache: Dict[str, FileSymbolIndex] = {}

    def index_workspace(self) -> Dict[str, Any]:
        """Scan and incrementally index the entire workspace."""
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            for f in files:
                ext = Path(f).suffix.lower()
                if ext in {".py", ".js", ".jsx", ".ts", ".tsx"}:
                    full_path = Path(root) / f
                    self._index_file(full_path)

        return self.get_summary()

    def _index_file(self, file_path: Path) -> Optional[FileSymbolIndex]:
        rel_path = file_path.relative_to(self.root_dir).as_posix()
        try:
            mtime = file_path.stat().st_mtime
            cached = self._index_cache.get(rel_path)
            if cached and cached.mtime == mtime:
                return cached  # Incremental cache hit

            ext = file_path.suffix.lower()
            idx = FileSymbolIndex(filepath=rel_path, mtime=mtime)

            if ext == ".py":
                self._parse_python(file_path, idx)
            elif ext in {".js", ".jsx", ".ts", ".tsx"}:
                self._parse_javascript(file_path, idx)

            self._index_cache[rel_path] = idx
            return idx
        except Exception as ex:
            logger.debug("Failed to index %s: %s", rel_path, ex)
            return None

    def _parse_python(self, file_path: Path, idx: FileSymbolIndex) -> None:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=str(file_path))
            idx.docstring = ast.get_docstring(tree)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    idx.functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node),
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    idx.classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": methods,
                        "docstring": ast.get_docstring(node),
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        idx.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        idx.imports.append(f"{module}.{alias.name}")
        except Exception:
            pass

    def _parse_javascript(self, file_path: Path, idx: FileSymbolIndex) -> None:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Extract functions
            fn_matches = re.finditer(r"\bfunction\s+([a-zA-Z0-9_]+)\s*\(", content)
            for m in fn_matches:
                idx.functions.append({"name": m.group(1)})

            const_fn_matches = re.finditer(r"\b(?:const|let)\s+([a-zA-Z0-9_]+)\s*=\s*(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>", content)
            for m in const_fn_matches:
                idx.functions.append({"name": m.group(1)})

            # Extract classes
            cls_matches = re.finditer(r"\bclass\s+([a-zA-Z0-9_]+)", content)
            for m in cls_matches:
                idx.classes.append({"name": m.group(1)})

            # Extract imports
            imp_matches = re.finditer(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", content)
            for m in imp_matches:
                idx.imports.append(m.group(1))
        except Exception:
            pass

    def find_symbols(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        matches = []
        for path, idx in self._index_cache.items():
            for fn in idx.functions:
                if q in fn["name"].lower():
                    matches.append({"type": "function", "file": path, "name": fn["name"], "line": fn.get("line")})
            for cls in idx.classes:
                if q in cls["name"].lower():
                    matches.append({"type": "class", "file": path, "name": cls["name"], "line": cls.get("line")})
        return matches

    def get_summary(self) -> Dict[str, Any]:
        total_files = len(self._index_cache)
        total_fns = sum(len(idx.functions) for idx in self._index_cache.values())
        total_classes = sum(len(idx.classes) for idx in self._index_cache.values())
        return {
            "indexed_files": total_files,
            "total_functions": total_fns,
            "total_classes": total_classes,
        }
