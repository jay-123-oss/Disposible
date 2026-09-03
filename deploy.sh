#!/usr/bin/env bash
# Production Deployment Wrapper Script for Linux/macOS
set -e

echo "[+] Initiating Fractal Multi-Agent System Deployment..."
python3 deploy.py --type "${1:-docker}"
echo "[+] Deployment execution completed with exit code $?."
