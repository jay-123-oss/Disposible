import os
import sys
from setuptools import setup, find_packages

def run_first_time_installer():
    """First-time environment setup, CLI check, and configuration scaffolding."""
    print("=" * 70)
    print("🛠️  Fractal 6-Agent Auto-Deployment System First-Time Setup Installer")
    print("=" * 70)
    
    # 1. Create notebooks
    try:
        from utils.notebook_generator import generate_and_save_all
        paths = generate_and_save_all()
        print(f"✅ Generated Kaggle template: {paths['kaggle']}")
        print(f"✅ Generated Colab template:  {paths['colab']}")
    except Exception as exc:
        print(f"⚠️ Notebook generation note: {exc}")

    # 2. Check Kaggle configuration
    if not os.path.exists("kaggle_config.json"):
        import json
        default_kaggle = {
            "username": "",
            "key": "",
            "notebook_name": "6-llm-agents",
            "accelerator": "gpu-t4",
            "enable_internet": True,
            "enable_gpu": True,
            "enable_tpu": False,
            "models": ["qwen2.5-coder:3b", "llama3.2:3b", "nomic-embed-text"],
        }
        with open("kaggle_config.json", "w", encoding="utf-8") as f:
            json.dump(default_kaggle, f, indent=2)
        print("✅ Created kaggle_config.json")

    # 3. Check .env
    if not os.path.exists(".env"):
        default_env = (
            "KAGGLE_USERNAME=your_username\n"
            "KAGGLE_KEY=your_api_key\n"
            "COLAB_RUNTIME=GPU\n"
            "TUNNEL_TYPE=cloudflare\n"
            "TUNNEL_PORT=8000\n"
        )
        with open(".env", "w", encoding="utf-8") as f:
            f.write(default_env)
        print("✅ Created .env file")

    print("=" * 70)
    print("🎉 First-time setup complete! Run 'python deploy.py --help' to get started.")
    print("=" * 70)


if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] in ("init", "setup", "--setup", "--init")):
    run_first_time_installer()
    sys.exit(0)

setup(
    name="fractal-agent-system",
    version="1.0.0",
    author="Fractal Systems Team",
    description="Fractal Multi-Agent Autonomous Coding System & 6-Agent Auto-Deployer",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "pydantic>=2.0.0",
        "psutil>=5.9.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
    ],
    entry_points={
        "console_scripts": [
            "fractal=cli:main",
            "fractal-deploy=deploy:main",
        ],
    },
)

