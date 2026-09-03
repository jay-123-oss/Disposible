"""Domain exceptions for the Plugin System Layer."""


class PluginError(Exception):
    """Base exception for all plugin system failures."""
    pass


class PluginManagerError(PluginError):
    """Raised when plugin registration, activation, or lifecycle management fails."""
    pass


class PluginLoaderError(PluginError):
    """Raised when dynamic, static, runtime, or hot-loading of plugins fails."""
    pass


class PluginStoreError(PluginError):
    """Raised when local/remote store or cache/index operations fail."""
    pass


class PluginInstallerError(PluginError):
    """Raised when plugin download, extraction, setup, or verification fails."""
    pass


class PluginUninstallerError(PluginError):
    """Raised when plugin removal, clean-up, or rollback fails."""
    pass


class PluginValidationError(PluginError):
    """Raised when plugin syntax, schema, compatibility, or performance validation fails."""
    pass


class PluginSecurityError(PluginError):
    """Raised when vulnerability, malware, permission, or signature checks fail."""
    pass


class PluginAPIError(PluginError):
    """Raised when hook/event/filter/action API interaction fails."""
    pass


class PluginEventError(PluginError):
    """Raised when plugin event registration, dispatch, handling, or logging fails."""
    pass


class PluginMarketplaceError(PluginError):
    """Raised when marketplace search, recommendation, rating, or review fails."""
    pass


class PluginVersionError(PluginError):
    """Raised when plugin version check, update, or rollback fails."""
    pass


class PluginDependencyError(PluginError):
    """Raised when plugin dependency resolution, conflict, or compatibility fails."""
    pass


class PluginDocumentationError(PluginError):
    """Raised when plugin documentation generation fails."""
    pass