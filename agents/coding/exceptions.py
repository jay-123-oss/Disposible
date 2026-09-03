"""Custom exceptions for the Coding Domain agents."""

from core.exceptions import AgentError


class CodingError(AgentError):
    """Base exception for all errors originating in the coding layer."""


class APIGenerationError(CodingError):
    """Raised when route, endpoint, or OpenAPI generation fails."""


class MiddlewareGenerationError(CodingError):
    """Raised when authentication, logging, or rate-limiting middleware generation fails."""


class ControllerGenerationError(CodingError):
    """Raised when controller handlers or request/response mapping fails."""


class ServiceGenerationError(CodingError):
    """Raised when business logic services or transactional workflows fail."""


class DatabaseGenerationError(CodingError):
    """Raised when database connection, schema, or migration generation fails."""


class ModelGenerationError(CodingError):
    """Raised when ORM models, schemas, or field validators fail to construct."""


class QueryGenerationError(CodingError):
    """Raised when SQL/NoSQL query generation or AST validation fails."""


class MigrationGenerationError(CodingError):
    """Raised when DDL migration revisions, upgrade, or downgrade scripts fail."""
