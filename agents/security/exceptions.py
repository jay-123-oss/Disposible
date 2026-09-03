"""Custom exceptions for the Security Domain agents."""

from core.exceptions import AgentError


class SecurityError(AgentError):
    """Base exception for all errors originating in the security audit layer."""


class AuthenticationError(SecurityError):
    """Raised when authentication policy or token verification check fails."""


class PermissionError(SecurityError):
    """Raised when RBAC or policy enforcement check fails."""


class InjectionVulnerability(SecurityError):
    """Raised when unparameterized SQL or command injection is detected."""


class XSSVulnerability(SecurityError):
    """Raised when unescaped HTML/JS output or missing CSP is detected."""


class CSRFVulnerability(SecurityError):
    """Raised when missing anti-CSRF token or insecure origin handling is detected."""


class EncryptionError(SecurityError):
    """Raised when weak cryptographic algorithms or insecure keys are detected."""


class ComplianceError(SecurityError):
    """Raised when regulatory compliance (GDPR, HIPAA, PCI) criteria fail."""
