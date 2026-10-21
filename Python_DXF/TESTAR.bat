@echo off
cd /d "%~dp0"
py -m pip install pytest
py -m pytest -q
pause
