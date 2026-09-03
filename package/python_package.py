"""Python package build automation."""
import subprocess
import sys

def build_python_package():
    print("[*] Building Python source distribution and wheel...")
    cmd = [sys.executable, "setup.py", "sdist", "bdist_wheel"]
    return subprocess.run(cmd, check=True).returncode == 0

if __name__ == "__main__":
    build_python_package()
