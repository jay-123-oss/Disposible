"""Docker run container utility."""
import subprocess

def run_container(port=8000):
    print(f"[*] Starting container on port {port}...")
    cmd = ["docker", "run", "-d", "-p", f"{port}:8000", "--name", "fractal_runtime", "fractal_agent_system:latest"]
    return subprocess.run(cmd, check=True).returncode == 0

if __name__ == "__main__":
    run_container()
