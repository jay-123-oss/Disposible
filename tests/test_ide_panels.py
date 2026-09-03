"""Tests for the IDE shell endpoints: search, source control, and run & debug."""

from __future__ import annotations

import os
import shutil

from fastapi.testclient import TestClient

from server import BASE_DIR, app

client = TestClient(app)


class TestSearchEndpoint:
    def test_search_requires_query(self):
        res = client.get("/api/search")
        assert res.status_code == 400

    def test_search_finds_file_by_name(self):
        res = client.get("/api/search", params={"q": "llm.py"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        paths = [r["path"] for r in data["results"]]
        assert "llm.py" in paths

    def test_search_finds_file_by_content_with_line(self):
        res = client.get("/api/search", params={"q": "build_staged_deltas"})
        assert res.status_code == 200
        data = res.json()
        hits = [r for r in data["results"] if r["path"] == "server.py" and r["type"] == "content"]
        assert hits, "content search should find build_staged_deltas in server.py"
        assert hits[0]["matches"][0]["line"] >= 1
        assert "build_staged_deltas" in hits[0]["matches"][0]["snippet"]

    def test_search_respects_ignored_dirs(self):
        # A file inside an ignored dir must never appear in results.
        probe_dir = os.path.join(BASE_DIR, ".probe_ignore_test")
        probe_file = os.path.join(probe_dir, "zxqprobe123.txt")
        os.makedirs(probe_dir, exist_ok=True)
        try:
            with open(probe_file, "w", encoding="utf-8") as fh:
                fh.write("zxqprobe123 unique marker\n")
            # It IS searchable normally...
            res = client.get("/api/search", params={"q": "zxqprobe123"})
            assert any("zxqprobe123" in r["path"] for r in res.json()["results"]), \
                "probe file should be searchable before ignore is applied"

            # ...and NOT searchable once its dir is ignored.
            import server as server_mod
            old_ignored = server_mod.IGNORED_DIRS
            server_mod.IGNORED_DIRS = set(old_ignored) | {".probe_ignore_test"}
            try:
                res = client.get("/api/search", params={"q": "zxqprobe123"})
                # The test file itself matches by content; the probe file must not.
                assert all("zxqprobe123" not in r["path"] for r in res.json()["results"]), \
                    "ignored dirs must be excluded from search"
            finally:
                server_mod.IGNORED_DIRS = old_ignored
        finally:
            shutil.rmtree(probe_dir, ignore_errors=True)

    def test_search_unknown_term_returns_empty(self):
        # Random term so no file in the repo (including this test) contains it.
        import uuid
        term = "zz-no-such-term-" + uuid.uuid4().hex
        res = client.get("/api/search", params={"q": term})
        assert res.status_code == 200
        assert res.json()["count"] == 0


class TestGitStatusEndpoint:
    def test_git_status_shape(self):
        res = client.get("/api/git/status")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["branch"] == "main"
        assert isinstance(data["changes"], list)
        assert isinstance(data["commits"], list)
        assert data["dirty_count"] == len(data["changes"])
        # Every change carries a 2-char code and a path.
        for change in data["changes"]:
            assert len(change["code"]) == 2
            assert change["path"]

    def test_git_status_paths_are_not_shifted(self):
        # Regression: .strip() on the whole git output used to eat the leading
        # space of the first status line, corrupting its path ("core/x.py"
        # became "ore/x.py"). The modified files in this working tree must all
        # appear with intact, full paths.
        res = client.get("/api/git/status")
        data = res.json()
        paths = {c["path"] for c in data["changes"]}
        assert "server.py" in paths
        assert "llm.py" in paths
        # The first entry alphabetically — this one was shifted before the fix.
        assert "core/canonical_orchestrator.py" in paths


class TestDebugRunEndpoint:
    def test_targets_whitelist(self):
        res = client.get("/api/debug/targets")
        assert res.status_code == 200
        ids = [t["id"] for t in res.json()["targets"]]
        assert {"compile-check", "smoke", "pytest"}.issubset(ids)

    def test_run_rejects_unknown_target(self):
        res = client.post("/api/debug/run", json={"target": "rm -rf /"})
        assert res.status_code == 400
        assert "Unknown target" in res.json()["detail"]

    def test_run_compile_check_succeeds(self):
        res = client.post("/api/debug/run", json={"target": "compile-check"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["exit_code"] == 0
        assert data["elapsed_seconds"] >= 0