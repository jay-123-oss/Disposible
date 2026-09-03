"""Domain exceptions for Deployment & Distribution Layer."""


class DeploymentError(Exception):
    """Base exception for all deployment and distribution failures."""
    pass


class SetupError(DeploymentError):
    """Raised when setup, installation, or configuration scripts fail."""
    pass


class DockerError(DeploymentError):
    """Raised when Docker image building, pushing, or running fails."""
    pass


class KubernetesError(DeploymentError):
    """Raised when Kubernetes manifest application, scaling, or rollout fails."""
    pass


class CloudError(DeploymentError):
    """Raised when AWS, GCP, Azure, or Terraform deployment fails."""
    pass


class PackageError(DeploymentError):
    """Raised when wheel, sdist, executable, or container packaging fails."""
    pass


class VersionError(DeploymentError):
    """Raised when semantic version bumping or tag comparison fails."""
    pass


class ReleaseError(DeploymentError):
    """Raised when release notes generation or release publishing fails."""
    pass


class UpdateError(DeploymentError):
    """Raised when checking, downloading, or applying updates fails."""
    pass


class RollbackError(DeploymentError):
    """Raised when executing or verifying deployment rollback fails."""
    pass


class CICDError(DeploymentError):
    """Raised when CI/CD pipeline generation or execution fails."""
    pass


class EnvironmentSetupError(DeploymentError):
    """Raised when dev, staging, or production environment setup fails."""
    pass


class SecretDeploymentError(DeploymentError):
    """Raised when secret injection or vault configuration fails."""
    pass


class HealthCheckDeploymentError(DeploymentError):
    """Raised when liveness, readiness, or metrics probe deployment fails."""
    pass
