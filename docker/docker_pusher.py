"""Docker push utility."""
import subprocess

def push_image(registry="docker.io", tag="latest"):
    target = f"{registry}/fractal_agent_system:{tag}"
    print(f"[*] Pushing Docker image to {target}...")
    return subprocess.run(["docker", "push", target], check=True).returncode == 0

if __name__ == "__main__":
    push_image()
