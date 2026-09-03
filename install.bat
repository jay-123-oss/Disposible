@echo off
echo === Fractal Multi-Agent Coding System Windows Installer ===
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python setup/configure.py
echo [+] Fractal System installed successfully.
