"""System configuration bootstrapper."""
import os
import shutil

def configure_system():
    print("[*] Configuring Fractal System environment...")
    config_file = "config.yaml"
    example_config = "config.example.yaml"
    if not os.path.exists(config_file) and os.path.exists(example_config):
        shutil.copyfile(example_config, config_file)
        print(f"[+] Created {config_file} from {example_config}")
    else:
        print(f"[+] Config file {config_file} ready.")
    os.makedirs("logs", exist_ok=True)
    os.makedirs("state/checkpoints", exist_ok=True)
    return True

if __name__ == "__main__":
    configure_system()
