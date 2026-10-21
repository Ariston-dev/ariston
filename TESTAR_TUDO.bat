@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "ENGINE=%LOCALAPPDATA%\LaserToolsFree\venv\Scripts\python.exe"
if not exist "%ENGINE%" (
  echo Nao ha ambiente Python do Laser Tools Free. Execute INSTALAR_TUDO.bat primeiro.
  pause
  exit /b 1
)
"%ENGINE%" -m pip install -q pytest
if errorlevel 1 (echo Erro instalando pytest & pause & exit /b 1)
cd /d "%~dp0Python_DXF"
"%ENGINE%" -m pytest -q
if errorlevel 1 (echo Testes de processamento falharam & pause & exit /b 1)
cd /d "%~dp0CorelAddon"
"%ENGINE%" -m pytest -q
if errorlevel 1 (echo Testes de estrutura falharam & pause & exit /b 1)
echo Todos testes de codigo passaram. A integracao real com CorelDRAW e RDWorks
 echo exige validacao manual neste computador.
pause
