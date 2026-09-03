"""Built-in SecurityScannerPlugin that scans code and plugins for vulnerabilities."""

from __future__ import annotations

import re

from plugins.plugin_api import PluginInterface

_RISK = re.compile(r"(eval\s*\(|exec\s*\(|subprocess|child_process|os\.system|password\s*=)", re.IGNORECASE)


class SecurityScannerPlugin(PluginInterface):
    """Scans artifacts for vulnerabilities and risky patterns."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "security-scanner"
        self.version = "1.0.0"
        self.author = "Fractal System"
        self.description = "Scans for vulnerabilities"

    def get_hooks(self):
        return {"on_security_scan": self._scan}

    def get_actions(self):
        return {"scan_security": self._scan}

    def _scan(self, source: str = "", **kwargs):
        """Scan source text for risky patterns."""
        findings = list(_RISK.findall(source))
        return {"vulnerabilities": findings, "safe": len(findings) == 0}