"""Custom exceptions for the Infrastructure Domain agents."""

from core.exceptions import AgentError


class InfrastructureError(AgentError):
    """Base exception for all errors originating in the infrastructure layer."""


class DockerError(InfrastructureError):
    """Raised when Dockerfile generation or build optimization fails."""


class ComposeError(InfrastructureError):
    """Raised when docker-compose specification generation fails."""


class CICDError(InfrastructureError):
    """Raised when CI/CD workflow pipeline generation fails."""


class EnvironmentError(InfrastructureError):
    """Raised when environment variables or template generation fails."""


class KubernetesError(InfrastructureError):
    """Raised when Kubernetes manifest synthesis fails."""


class TerraformError(InfrastructureError):
    """Raised when Terraform HCL synthesis or state configuration fails."""


class HealthCheckError(InfrastructureError):
    """Raised when probe configuration fails validation."""


class LoadBalancerError(InfrastructureError):
    """Raised when Nginx/Traefik/ALB configuration fails."""


class MonitoringError(InfrastructureError):
    """Raised when Prometheus or Grafana stack setup fails."""


class LoggingError(InfrastructureError):
    """Raised when ELK/EFK logging configuration fails."""


class SecretError(InfrastructureError):
    """Raised when HashiCorp Vault or Secrets Manager setup fails."""


class NetworkError(InfrastructureError):
    """Raised when VPC, firewall, or service mesh configuration fails."""


class BackupError(InfrastructureError):
    """Raised when backup or disaster recovery plan generation fails."""
