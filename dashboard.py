#!/usr/bin/env python3
"""Fractal Multi-Agent System - Interactive Web Dashboard Launcher.

Starts the FastAPI Command & Observability Dashboard and opens it in the browser.
Usage:
    python dashboard.py
    python dashboard.py --port 8080 --no-browser
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
import webbrowser

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def is_port_in_use(port: int) -> bool:
    """Check if a local port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def find_free_port(start_port: int = 8080) -> int:
    """Find next available free port starting from start_port."""
    port = start_port
    while is_port_in_use(port) and port < start_port + 50:
        port += 1
    return port


def main():
    parser = argparse.ArgumentParser(description="Launch Fractal Multi-Agent GUI Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the dashboard server (default: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    args = parser.parse_args()

    port = args.port
    if is_port_in_use(port):
        free_p = find_free_port(port + 1)
        print(f"⚠️ Port {port} is currently in use. Switching to port {free_p}.")
        port = free_p

    dashboard_url = f"http://localhost:{port}"

    print("=" * 70)
    print("⚡ FRACTAL MULTI-AGENT SYSTEM - WEB DASHBOARD LAUNCHER")
    print("=" * 70)
    print(f"🌐 Dashboard URL:    {dashboard_url}")
    print(f"🔌 API Swagger Docs: {dashboard_url}/docs")
    print(f"📡 WebSocket Stream: ws://localhost:{port}/ws")
    print("=" * 70)

    if not args.no_browser:
        def _open():
            time.sleep(1.2)
            print(f"🚀 Opening dashboard in your default browser: {dashboard_url}")
            webbrowser.open(dashboard_url)

        t = threading.Thread(target=_open, daemon=True)
        t.start()

    import uvicorn
    # Import the FastAPI application
    from gui.api.main import app

    try:
        uvicorn.run(app, host=args.host, port=port, log_level="info")
    except KeyboardInterrupt:
        print("\n[!] Dashboard server stopped.")


if __name__ == "__main__":
    main()
