"""System installation verifier."""
import subprocess
import sys

def verify_system():
    print("[*] Verifying system integrity...")
    res = subprocess.run([sys.executable, "cli.py", "health"], capture_output=True, text=True)
    print(res.stdout)
    return res.returncode == 0

if __name__ == "__main__":
    verify_system()
