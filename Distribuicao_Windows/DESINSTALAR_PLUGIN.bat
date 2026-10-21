@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0DESINSTALAR_PLUGIN.ps1"
if errorlevel 1 (echo Falha na operacao. Confira a mensagem acima. & pause & exit /b 1)
pause
