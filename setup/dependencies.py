"""Dependency resolution and verification."""
import subprocess
import sys

def install_dependencies(dev=False):
    req_file = "requirements-dev.txt" if dev else "requirements.txt"
    print(f"[*] Installing dependencies from {req_file}...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], check=True)
    return True

if __name__ == "__main__":
    install_dependencies()
