@echo off
cd /d "%~dp0"
py -m pip install pywin32
if errorlevel 1 (echo Falha ao instalar pywin32. & pause & exit /b 1)
echo Requisito instalado. Execute ABRIR_COREL_TESTE.bat
pause
