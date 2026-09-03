"""Domain exceptions for the Documentation Layer."""


class DocumentationError(Exception):
    """Base exception for all documentation-related agent failures."""
    pass


class SystemDocumentationError(DocumentationError):
    """Raised when system architecture, component, or data flow generation fails."""
    pass


class ApiDocumentationError(DocumentationError):
    """Raised when OpenAPI, Swagger, endpoint, or schema generation fails."""
    pass


class UserGuideError(DocumentationError):
    """Raised when user guide, quickstart, features, or best practice generation fails."""
    pass


class DeveloperGuideError(DocumentationError):
    """Raised when developer guide, code structure, extension, or contributing guide fails."""
    pass


class InstallationGuideError(DocumentationError):
    """Raised when installation, prerequisites, or verification documentation fails."""
    pass


class ConfigurationGuideError(DocumentationError):
    """Raised when configuration, environment variable, or validation guide fails."""
    pass


class DeploymentGuideError(DocumentationError):
    """Raised when Docker, Kubernetes, cloud, or CI/CD deployment guide fails."""
    pass


class AgentReferenceError(DocumentationError):
    """Raised when agent reference, capability index, or lifecycle documentation fails."""
    pass


class ExampleRepositoryError(DocumentationError):
    """Raised when example catalog or usage scenario generation fails."""
    pass


class TroubleshootingGuideError(DocumentationError):
    """Raised when troubleshooting, error codes, or resolution guide generation fails."""
    pass


class FaqGenerationError(DocumentationError):
    """Raised when FAQ compilation fails."""
    pass
