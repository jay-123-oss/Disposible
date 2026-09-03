"""Domain exceptions for the Multi-Language Support Layer."""


class MultiLanguageError(Exception):
    """Base exception for all multi-language generation and coordination failures."""
    pass


class PythonGenerationError(MultiLanguageError):
    """Raised when Python code generation fails."""
    pass


class NodeGenerationError(MultiLanguageError):
    """Raised when Node.js code generation fails."""
    pass


class GoGenerationError(MultiLanguageError):
    """Raised when Go code generation fails."""
    pass


class RustGenerationError(MultiLanguageError):
    """Raised when Rust code generation fails."""
    pass


class JavaGenerationError(MultiLanguageError):
    """Raised when Java code generation fails."""
    pass


class LanguageDetectionError(MultiLanguageError):
    """Raised when language detection fails or confidence is below threshold."""
    pass


class LanguageTranslationError(MultiLanguageError):
    """Raised when translating code between languages fails."""
    pass


class CrossLanguageValidationError(MultiLanguageError):
    """Raised when cross-language validation finds unsafe or invalid code."""
    pass


class PackageManagementError(MultiLanguageError):
    """Raised when package management (pip/npm/go/cargo/maven) fails."""
    pass


class FrameworkSelectionError(MultiLanguageError):
    """Raised when optimal framework selection fails."""
    pass


class DependencyResolutionError(MultiLanguageError):
    """Raised when dependency version or conflict resolution fails."""
    pass


class CodeFormattingError(MultiLanguageError):
    """Raised when language-specific code formatting fails."""
    pass


class DocumentationGenerationError(MultiLanguageError):
    """Raised when language-specific documentation generation fails."""
    pass