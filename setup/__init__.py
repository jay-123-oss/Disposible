"""Setup and installation package."""
from setup.install import install_system
from setup.configure import configure_system
from setup.dependencies import install_dependencies
from setup.verify import verify_system

__all__ = ["install_system", "configure_system", "install_dependencies", "verify_system"]
