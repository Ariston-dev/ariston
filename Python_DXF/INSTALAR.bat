@echo off
cd /d "%~dp0"
echo Instalando as dependencias do Laser Tools Free v3...
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo Falha ao instalar. Verifique o Python e a conexao com a Internet.
) else (
  echo Instalacao concluida. Execute ABRIR.bat.
)
pause
