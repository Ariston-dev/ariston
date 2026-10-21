@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
where py >nul 2>nul
if errorlevel 1 (
  echo Este teste e apenas para desenvolvedores e requer Python no ambiente de desenvolvimento.
  echo O pacote final do GitHub nao exige Python no PC do usuario.
  pause
  exit /b 1
)
py -3 -m pytest -q Python_DXF/tests CorelAddon/tests
if errorlevel 1 (
  echo FALHA nos testes. Consulte as mensagens acima.
  pause
  exit /b 1
)
echo Testes de codigo aprovados. A validacao do painel exige CorelDRAW 2024 real.
pause
