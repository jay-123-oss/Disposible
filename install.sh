#!/usr/bin/env bash
set -e

echo "=== Fractal Multi-Agent Coding System Installer ==="
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python setup/configure.py
echo "[+] Fractal System installed successfully."
