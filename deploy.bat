@echo off
REM Production Deployment Wrapper Script for Windows
echo [+] Initiating Fractal Multi-Agent System Deployment...
python deploy.py --type "%~1"
echo [+] Deployment execution finished with exit code %ERRORLEVEL%.
exit /b %ERRORLEVEL%
