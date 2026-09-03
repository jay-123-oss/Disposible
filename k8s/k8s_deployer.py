"""Kubernetes deployment runner."""
import subprocess

def apply_manifests():
    manifests = ["configmap.yaml", "secrets.yaml", "deployment.yaml", "service.yaml", "ingress.yaml", "hpa.yaml"]
    for m in manifests:
        print(f"[*] Applying k8s/{m}...")
        subprocess.run(["kubectl", "apply", "-f", f"k8s/{m}"], check=False)
    return True

if __name__ == "__main__":
    apply_manifests()
