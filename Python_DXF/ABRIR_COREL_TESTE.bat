@echo off
cd /d "%~dp0"
py corel_panel_externo.py
if errorlevel 1 pause
