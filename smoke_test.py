#!/usr/bin/env python3
"""Real smoke test for the Antigravity+ IDE / Freebuff Desktop backend.

What it actually does (no fake "True" results):
1. Hits the FastAPI endpoints defined in server.py through TestClient:
   - GET  /                 (frontend HTML)
   - GET  /api/status       (health)
   - GET  /api/files        (file tree)
   - GET  /api/file/...     (read + path-traversal guard)
   - POST /api/file/...     (native save)
   - POST /api/chat         (orchestrator -> staged files with content map + deltas)
   - GET  /api/staged-file  (staged preview)
   - POST /api/accept       (writes staged files to disk)
   - POST /api/reject       (discards staged files)
   - WS   /ws               (real-time agent stream + accept flow)
2. Runs the project's real pytest suite and reports pass/fail honestly.

Exit code is 0 only when every check AND the pytest suite pass.

Notes:
- When executed from inside a running pytest process (e.g.
  tests/test_final_integration_agents.py::test_20 spawns smoke_test.py standalone),
  the nested full-pytest run is skipped to avoid recursion; endpoint checks still run.
- Use --no-pytest to skip the pytest suite explicitly.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROBE_PY = "qa_smoke_probe.py"
REJECT_PY = "qa_smoke_reject.py"
WS_PY = "qa_smoke_ws.py"
SAVE_TXT = "qa_smoke_save.txt"
PROBE_FILES = [PROBE_PY, REJECT_PY, WS_PY, SAVE_TXT]


def _clean_probe_files() -> None:
    for name in PROBE_FILES:
        try:
            if os.path.exists(name):
                os.remove(name)
        except OSError:
            pass


# ==============================================================================
# Tiny check harness (tracks every assertion, prints PASS/FAIL honestly)
# ==============================================================================
_CHECKS: dict = {"passed": 0, "failed": 0}
_FAILED_DETAILS: list = []


def check(section: str, name: str, cond: bool, detail: str = "") -> bool:
    ok = bool(cond)
    if ok:
        _CHECKS["passed"] += 1
        print(f"  [PASS] {section} :: {name} {detail}".rstrip())
    else:
        _CHECKS["failed"] += 1
        _FAILED_DETAILS.append(f"{section} :: {name} {detail}".strip())
        print(f"  [FAIL] {section} :: {name} {detail}".rstrip())
    return ok


# ==============================================================================
# Section 1: REST API endpoints + mutation lifecycle
# ==============================================================================
def test_server_endpoints() -> None:
    print("=" * 66)
    print("SMOKE SECTION 1: REST API endpoints & staged-file lifecycle")
    print("=" * 66)
    from fastapi.testclient import TestClient

    import server

    _clean_probe_files()
    try:
        with TestClient(server.app) as c:
            # -- basic endpoints -------------------------------------------------
            r = c.get("/")
            check("REST", "GET / serves frontend HTML",
                  r.status_code == 200 and "Antigravity" in r.text, f"[{r.status_code}]")

            r = c.get("/api/status")
            check("REST", "GET /api/status healthy",
                  r.status_code == 200 and r.json().get("status") == "ready", str(r.json())[:60])

            r = c.get("/api/files")
            body = r.json()
            top = [f.get("name") for f in body.get("files", [])]
            check("REST", "GET /api/files lists project files",
                  r.status_code == 200 and body.get("status") == "success" and "server.py" in top,
                  f"top={top[:5]}")

            r = c.get("/api/file/server.py")
            check("REST", "GET /api/file/server.py returns real content",
                  r.status_code == 200 and "FastAPI" in r.json().get("content", ""))

            r = c.get("/api/file/..%2F..%2Frequirements.txt")
            check("REST", "path traversal blocked",
                  r.status_code in (403, 404), f"code={r.status_code}")

            # -- mutation lifecycle: chat -> staged -> preview -> accept ---------
            r = c.post("/api/chat", json={"prompt": f"create {PROBE_PY} hello world", "session_id": "smoke"})
            body = r.json()
            check("REST", "POST /api/chat ok (CREATE/MUTATION)",
                  r.status_code == 200 and body.get("intent") == "CREATE"
                  and body.get("execution_mode") == "MUTATION",
                  f"intent={body.get('intent')} mode={body.get('execution_mode')}")

            files = body.get("files") or {}
            content = files.get(PROBE_PY, "")
            deltas = body.get("deltas") or []
            check("REST", "chat returns content map (not bare name list)",
                  isinstance(files, dict) and PROBE_PY in files and "Hello" in content,
                  f"keys={list(files.keys())}")
            check("REST", "chat returns review deltas",
                  len(deltas) == 1 and deltas[0]["path"] == PROBE_PY
                  and deltas[0]["status"] == "CREATED", str(deltas)[:80])
            check("REST", "staged file NOT written before accept",
                  not os.path.exists(PROBE_PY))

            r = c.get("/api/staged-file", params={"session_id": "smoke", "path": PROBE_PY})
            check("REST", "GET /api/staged-file serves staged content",
                  r.status_code == 200 and "Hello" in r.json().get("content", ""))

            r = c.post("/api/accept", json={"session_id": "smoke"})
            check("REST", "POST /api/accept commits staged file",
                  r.json().get("status") == "success" and PROBE_PY in r.json().get("committed_files", []))
            if os.path.exists(PROBE_PY):
                with open(PROBE_PY, encoding="utf-8") as f:
                    check("REST", "accepted file on disk with real content", "Hello" in f.read())
                os.remove(PROBE_PY)
            else:
                check("REST", "accepted file on disk with real content", False)

            # -- reject discards ---------------------------------------------------
            r = c.post("/api/chat", json={"prompt": f"create {REJECT_PY} hello world", "session_id": "smoke-reject"})
            check("REST", "2nd chat staged for reject path",
                  r.json().get("files_count") == 1)
            r = c.post("/api/reject", json={"session_id": "smoke-reject"})
            check("REST", "POST /api/reject discards staged files",
                  r.json().get("status") == "rejected")
            check("REST", "rejected file never written", not os.path.exists(REJECT_PY))

            # -- native file save/read roundtrip ------------------------------------
            r = c.post("/api/file/" + SAVE_TXT, json={"content": "smoke roundtrip"})
            check("REST", "POST /api/file saves natively", r.status_code == 200)
            r = c.get("/api/file/" + SAVE_TXT)
            check("REST", "saved file readable back",
                  r.status_code == 200 and r.json().get("content") == "smoke roundtrip")
            if os.path.exists(SAVE_TXT):
                os.remove(SAVE_TXT)
    finally:
        _clean_probe_files()


# ==============================================================================
# Section 2: WebSocket real-time agent stream + accept flow
# ==============================================================================
def test_websocket_flow() -> None:
    print("=" * 66)
    print("SMOKE SECTION 2: WebSocket /ws real-time agent stream")
    print("=" * 66)
    from fastapi.testclient import TestClient

    import server

    _clean_probe_files()
    try:
        with TestClient(server.app) as c:
            with c.websocket_connect("/ws") as ws:
                greet = ws.receive_json()
                check("WS", "greeting received from orchestrator",
                      greet.get("type") == "agent_message", str(greet)[:60])

                ws.send_json({"action": "chat", "prompt": f"create {WS_PY} hello world"})
                completed = False
                for _ in range(40):
                    msg = ws.receive_json()
                    if msg.get("type") == "swarm_completed":
                        completed = True
                        check("WS", "swarm_completed carries staged file + deltas",
                              WS_PY in msg.get("files", []) and len(msg.get("deltas") or []) == 1,
                              f"files={msg.get('files')}")
                        break
                check("WS", "full event stream observed", completed)

                ws.send_json({"action": "accept"})
                result = None
                for _ in range(5):
                    msg = ws.receive_json()
                    if msg.get("type") == "action_result":
                        result = msg
                        break
                check("WS", "accept action succeeds",
                      result is not None and result.get("status") == "accepted", str(result)[:80])
                if os.path.exists(WS_PY):
                    os.remove(WS_PY)
                    check("WS", "accepted WS file written & cleaned", True)
                else:
                    check("WS", "accepted WS file written & cleaned", False)
    finally:
        _clean_probe_files()


# ==============================================================================
# Section 3: Real pytest suite (honest pass/fail)
# ==============================================================================
def run_pytest_suite(extra_args: list | None = None) -> dict:
    print("=" * 66)
    print("SMOKE SECTION 3: running the real pytest suite")
    print("=" * 66)
    args = [sys.executable, "-m", "pytest", "-q", "--tb=short", "--no-header"]
    if extra_args:
        args.extend(extra_args)
    print("  $", " ".join(args))
    started = time.time()
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=1200)
    except subprocess.TimeoutExpired:
        return {"ran": True, "timed_out": True, "passed": 0, "failed": -1, "error": "pytest timed out"}
    elapsed = round(time.time() - started, 1)

    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    tail = output.splitlines()

    import re
    passed = failed = 0
    m_pass = re.search(r"(\d+) passed", output)
    if m_pass:
        passed = int(m_pass.group(1))
    m_fail = re.search(r"(\d+) failed", output)
    if m_fail:
        failed = int(m_fail.group(1))
    failed_ids = [ln.strip()[len("FAILED "):] for ln in tail if ln.strip().startswith("FAILED ")]

    summary = f"pytest: {passed} passed, {failed} failed, {len(failed_ids)} listed, in {elapsed}s (exit {proc.returncode})"
    print("  " + ("[PASS]" if proc.returncode == 0 else "[FAIL]") + " " + summary)
    for fid in failed_ids:
        print(f"    FAILED: {fid}")

    ok = proc.returncode == 0 and failed == 0
    check("pytest", "full suite is green", ok, summary if not ok else "")
    return {
        "ran": True,
        "timed_out": False,
        "exit_code": proc.returncode,
        "passed": passed,
        "failed": failed,
        "failed_ids": failed_ids,
        "elapsed_s": elapsed,
    }


# ==============================================================================
# Report
# ==============================================================================
def generate_report(started_at: float, pytest_result: dict | None, skipped_pytest: bool) -> dict:
    total_ok = _CHECKS["failed"] == 0 and (pytest_result is None or pytest_result.get("failed", 1) == 0)
    report = {
        "smoke_test_id": f"SMK_{int(started_at)}",
        "timestamp": started_at,
        "duration_s": round(time.time() - started_at, 2),
        "checks_passed": _CHECKS["passed"],
        "checks_failed": _CHECKS["failed"],
        "failed_checks": list(_FAILED_DETAILS),
        "pytest": pytest_result or {"ran": False, "skipped": skipped_pytest},
        "smoke_tests_passed": bool(total_ok),
    }
    print("=" * 66)
    print("SMOKE TEST REPORT:", json.dumps(report, indent=2))
    print("=" * 66)
    if report["smoke_tests_passed"]:
        print("[+] SMOKE TESTS PASSED (all checks + pytest suite green).")
    else:
        print("[-] SMOKE TESTS FAILED. See failed checks / pytest failures above.")
    return report


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Antigravity+ real smoke test (endpoints + pytest)")
    parser.add_argument("--no-pytest", action="store_true", help="Skip the pytest suite run")
    parser.add_argument("--pytest-args", nargs="*", default=[], help="Extra args forwarded to pytest")
    args = parser.parse_args(argv)

    started_at = time.time()
    print("Starting REAL smoke tests (no fake pass results)...")

    test_server_endpoints()
    test_websocket_flow()

    # Avoid recursion: when pytest itself spawns smoke_test.py (test_20), skip the
    # nested full-pytest run and rely on the endpoint checks above.
    under_pytest = bool(os.environ.get("PYTEST_CURRENT_TEST"))
    skip_pytest = args.no_pytest or under_pytest

    pytest_result = None
    if not skip_pytest:
        pytest_result = run_pytest_suite(args.pytest_args)
    elif under_pytest:
        print("NOTE: detected execution inside a running pytest process -> skipping nested pytest suite.")
    else:
        print("NOTE: pytest suite skipped via --no-pytest.")

    report = generate_report(started_at, pytest_result, skipped_pytest=skip_pytest)
    return 0 if report["smoke_tests_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
