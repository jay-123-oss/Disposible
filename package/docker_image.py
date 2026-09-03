"""Docker image archive package builder."""
import subprocess

def export_docker_image(tag="latest", output="dist/fractal-system-image.tar"):
    print(f"[*] Exporting Docker image to {output}...")
    subprocess.run(["docker", "save", "-o", output, f"fractal_agent_system:{tag}"], check=False)
    return True

if __name__ == "__main__":
    export_docker_image()
