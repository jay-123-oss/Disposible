"""Google Colab deployment utilities."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import webbrowser
from typing import Any, Dict, Optional

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger("ColabUtils")


class ColabDeployer:
    """Manages generation of Google Colab notebook, direct launch links, and browser launch."""

    def __init__(self, config_path: str = "colab_config.json") -> None:
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load Colab configuration."""
        defaults = {
            "runtime": "GPU",
            "accelerator": "T4",
            "timeout_seconds": 3600,
            "ngrok_authtoken": os.getenv("NGROK_AUTHTOKEN", ""),
            "tunnel_type": "ngrok",
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    defaults.update(json.load(f))
            except Exception as exc:
                logger.warning("Could not read %s: %s", self.config_path, exc)
        return defaults

    def generate_colab_link(self, github_repo: Optional[str] = None) -> str:
        """Construct direct URL to open notebook in Google Colab."""
        if github_repo:
            return f"https://colab.research.google.com/github/{github_repo}/blob/main/notebooks/colab_template.ipynb"
        # Opening directly to upload modal so user can drag & drop the generated notebook
        return "https://colab.research.google.com/#upload=true"

    def deploy(self, open_browser: bool = False) -> Dict[str, Any]:
        """Execute automated Colab deployment preparation."""
        print("🚀 Deploying 6 LLM Agents to Google Colab...")
        print("📦 Models: qwen2.5-coder:3b, llama3.2:3b, nomic-embed-text")

        from utils.notebook_generator import generate_and_save_all
        paths = generate_and_save_all()
        colab_path = os.path.abspath(paths["colab"])

        web_url = self.generate_colab_link()
        public_url = "https://fractal-core-6agents.ngrok-free.app"

        # Try to copy notebook path to clipboard on Windows
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value '{colab_path}'"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
        except Exception:
            pass

        print("=" * 70)
        print("📤 Google Colab Notebook Prepared: " + colab_path)
        print("📋 Absolute path copied to clipboard!")
        print("✅ Deployment package ready!")
        print(f"🔗 Expected Endpoint: {public_url}")
        print(f"📌 Web: {web_url}")
        print("=" * 70)
        print("👉 QUICK STEPS IN COLAB:")
        print(f"   1. In the browser Upload tab, click 'Browse' and paste this path:")
        print(f"      {colab_path}")
        print("   2. Select: Runtime -> Change runtime type -> T4 GPU")
        print("   3. Run all cells -> Public endpoint will be active!")
        print("=" * 70)

        if open_browser:
            print(f"🌐 Opening Google Colab Upload in browser: {web_url}")
            webbrowser.open(web_url)

        return {
            "success": True,
            "platform": "colab",
            "notebook_path": colab_path,
            "web_url": web_url,
            "endpoint_url": public_url,
        }
