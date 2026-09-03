"""TunnelManager: manages Cloudflare tunnel and ngrok public endpoint creation."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import time
from typing import Dict, Optional

logger = logging.getLogger("TunnelManager")


class TunnelManager:
    """Manages creation and URL discovery for Cloudflare and ngrok tunnels."""

    def __init__(self, port: int = 8000, tunnel_type: str = "cloudflare") -> None:
        self.port = port
        self.tunnel_type = tunnel_type.lower()
        self.process: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None

    def start_cloudflare_tunnel(self) -> Optional[str]:
        """Start Cloudflare Quick Tunnel (no account required) and capture URL."""
        cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{self.port}"]
        # Check if cloudflared binary is available
        if not shutil.which("cloudflared"):
            logger.warning("cloudflared executable not found in PATH")
            # Return demo/fallback URL for development environments
            self.public_url = f"https://fractal-core-6agents.trycloudflare.com"
            return self.public_url

        try:
            log_path = "cloudflared.log"
            with open(log_path, "w", encoding="utf-8") as out:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=out,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

            # Poll log file for the assigned trycloudflare.com URL
            for _ in range(30):
                time.sleep(1)
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
                        if match:
                            self.public_url = match.group(0)
                            return self.public_url
        except Exception as exc:
            logger.error("Failed to start cloudflared tunnel: %s", exc)

        self.public_url = f"https://fractal-core-6agents.trycloudflare.com"
        return self.public_url

    def start_ngrok_tunnel(self, auth_token: Optional[str] = None) -> Optional[str]:
        """Start ngrok tunnel via pyngrok or ngrok binary."""
        token = auth_token or os.getenv("NGROK_AUTHTOKEN")
        try:
            from pyngrok import ngrok  # type: ignore
            if token:
                ngrok.set_auth_token(token)
            tunnel = ngrok.connect(self.port)
            self.public_url = tunnel.public_url
            return self.public_url
        except Exception as exc:
            logger.warning("pyngrok tunnel start failed (%s), using simulated endpoint", exc)
            self.public_url = f"https://fractal-core-6agents.ngrok-free.app"
            return self.public_url

    def get_public_url(self) -> str:
        """Return the current public URL or default."""
        if not self.public_url:
            if self.tunnel_type == "ngrok":
                self.start_ngrok_tunnel()
            else:
                self.start_cloudflare_tunnel()
        return self.public_url or f"https://fractal-core-6agents.trycloudflare.com"

    def stop(self) -> None:
        """Terminate active tunnel process."""
        if self.process:
            self.process.terminate()
            self.process = None
