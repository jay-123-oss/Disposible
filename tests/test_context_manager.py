"""Unit tests for AST-based Codebase Indexer and Context Manager."""

from core.context import CodebaseIndexer, ContextManager


def test_indexer_ast_parsing():
    indexer = CodebaseIndexer(root_dir="core")
    summary = indexer.index_workspace()
    assert summary["indexed_files"] > 0
    assert summary["total_functions"] > 0

    # Search for known symbol in core
    symbols = indexer.find_symbols("ToolManager")
    assert any(s["name"] == "ToolManager" for s in symbols)


def test_context_manager_budgeting():
    ctx_mgr = ContextManager(root_dir="core", max_token_budget=2000)
    context = ctx_mgr.retrieve_relevant_context("Fix issue in ToolManager safety policy")

    assert "selected_files" in context
    assert len(context["selected_files"]) > 0
    assert context["budget_remaining"] > 0
    # Highest ranked file should be tool-related
    top_file = context["selected_files"][0]["path"]
    assert "tool" in top_file.lower()
