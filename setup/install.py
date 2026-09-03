"""Automated system installer."""
import os
import sys
import subprocess

def install_system():
    print("[*] Installing Fractal Multi-Agent System...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    print("[+] Dependencies successfully installed.")
    return True

if __name__ == "__main__":
    install_system()
