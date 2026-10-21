@echo off
cd /d "%~dp0"
py laser_tools_free.py %*
if errorlevel 1 pause
