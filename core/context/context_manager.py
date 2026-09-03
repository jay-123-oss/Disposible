"""Context Manager for intelligent context pruning and token budgeting."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.context.indexer import CodebaseIndexer, FileSymbolIndex


class ContextManager:
    """Selects and budgets relevant context so LLM is never overwhelmed."""

    def __init__(self, root_dir: str = ".", max_token_budget: int = 4000):
        self.root_dir = Path(root_dir).resolve()
        self.indexer = CodebaseIndexer(root_dir)
        self.max_token_budget = max_token_budget
        self._recently_modified: List[str] = []

    def record_modified_file(self, filepath: str) -> None:
        if filepath not in self._recently_modified:
            self._recently_modified.append(filepath)

    def retrieve_relevant_context(self, task_prompt: str) -> Dict[str, Any]:
        """Index workspace and select top relevant files and symbol signatures."""
        self.indexer.index_workspace()
        lower_prompt = task_prompt.lower()

        # Extract potential filenames and terms (with CamelCase and snake_case splitting)
        raw_terms = set(re.findall(r"\b[a-zA-Z0-9_\-]+\b", lower_prompt))
        terms = set(raw_terms)
        for t in raw_terms:
            terms.add(t.replace("_", ""))
            terms.add(t.replace("-", ""))
        for word in re.findall(r"[A-Za-z0-9]+", task_prompt):
            subwords = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)", word)
            for sw in subwords:
                if len(sw) > 2:
                    terms.add(sw.lower())

        scored_files: List[tuple[float, str, FileSymbolIndex]] = []

        for rel_path, idx in self.indexer._index_cache.items():
            score = 0.0
            p_lower = rel_path.lower().replace("\\", "/")

            # Boost if directly mentioned in prompt
            for term in terms:
                if len(term) > 2 and term in p_lower:
                    score += 5.0

            # Boost if functions or classes match terms
            for fn in idx.functions:
                if any(t in fn["name"].lower() for t in terms if len(t) > 2):
                    score += 3.0

            for cls in idx.classes:
                if any(t in cls["name"].lower() for t in terms if len(t) > 2):
                    score += 4.0

            # Boost recently modified files
            if rel_path in self._recently_modified:
                score += 2.0

            # Prioritize test files if task mentions testing
            if "test" in lower_prompt and "test" in p_lower:
                score += 4.0

            if score > 0:
                scored_files.append((score, rel_path, idx))

        # Sort by relevance score descending
        scored_files.sort(key=lambda x: x[0], reverse=True)

        selected_files: List[Dict[str, Any]] = []
        estimated_tokens = 0

        for score, path, idx in scored_files[:5]:  # Top 5 most relevant files
            file_obj = {
                "path": path,
                "relevance_score": score,
                "functions": [f["name"] for f in idx.functions[:10]],
                "classes": [c["name"] for c in idx.classes[:5]],
                "imports": idx.imports[:8],
            }
            # Roughly 1 token per 4 chars
            tokens = len(str(file_obj)) // 4
            if estimated_tokens + tokens > self.max_token_budget:
                break
            selected_files.append(file_obj)
            estimated_tokens += tokens

        return {
            "selected_files": selected_files,
            "recently_modified": self._recently_modified[-5:],
            "estimated_tokens": estimated_tokens,
            "budget_remaining": self.max_token_budget - estimated_tokens,
        }
