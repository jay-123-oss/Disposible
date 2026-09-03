"""Distribution artifact validation and checksum generator."""
import hashlib
import os

def generate_checksums(dist_dir="dist/"):
    os.makedirs(dist_dir, exist_ok=True)
    manifest = {}
    for root, _, files in os.walk(dist_dir):
        for f in files:
            p = os.path.join(root, f)
            with open(p, "rb") as fh:
                manifest[f] = hashlib.sha256(fh.read()).hexdigest()
    return manifest

if __name__ == "__main__":
    print(generate_checksums())
