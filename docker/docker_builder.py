"""Docker build utility."""
import subprocess

def build_image(tag="latest"):
    print(f"[*] Building Docker image with tag: {tag}...")
    cmd = ["docker", "build", "-t", f"fractal_agent_system:{tag}", "-f", "docker/Dockerfile", "."]
    return subprocess.run(cmd, check=True).returncode == 0

if __name__ == "__main__":
    build_image()
