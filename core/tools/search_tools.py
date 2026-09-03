"""Search tools for lexical, symbol, and reference discovery in the codebase."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.tools.base import BaseTool, SafetyLevel, ToolResult


class SearchTextTool(BaseTool):
    name = "search_text"
    description = "Search for exact or regex text patterns across files in the workspace."
    safety_level = SafetyLevel.SAFE

    IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}

    def _run(
        self,
        query: str,
        directory: str = ".",
        is_regex: bool = False,
        file_glob: Optional[str] = None,
        max_results: int = 50,
    ) -> ToolResult:
        dir_path = Path(directory).resolve()
        results: List[Dict[str, Any]] = []

        pattern = re.compile(query, re.IGNORECASE) if is_regex else None

        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            for f in files:
                if file_glob and not Path(f).match(file_glob):
                    continue
                file_path = Path(root) / f
                try:
                    lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for idx, line in enumerate(lines, 1):
                        match = pattern.search(line) if pattern else (query.lower() in line.lower())
                        if match:
                            results.append({
                                "file": file_path.relative_to(dir_path).as_posix(),
                                "line": idx,
                                "content": line.strip(),
                            })
                            if len(results) >= max_results:
                                break
                except Exception:
                    continue
            if len(results) >= max_results:
                break

        return ToolResult(
            success=True,
            output=results,
            stdout=f"Found {len(results)} matches for '{query}'.",
        )


class SearchSymbolTool(BaseTool):
    name = "search_symbol"
    description = "Search for function, class, or variable declarations across code files."
    safety_level = SafetyLevel.SAFE

    def _run(self, symbol_name: str, directory: str = ".") -> ToolResult:
        # Regex matching python def/class and JS/TS function/const/class
        symbol_pattern = rf"\b(def|class|function|const|let|var)\s+{re.escape(symbol_name)}\b"
        return SearchTextTool().execute(query=symbol_pattern, directory=directory, is_regex=True)
