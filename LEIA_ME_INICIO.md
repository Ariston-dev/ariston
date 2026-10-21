# Laser Tools Free v5.1 — projeto para compilação Windows automática

**ATENÇÃO: ESTE ZIP AINDA NÃO É UM PLUGIN INSTALÁVEL.** Ele contém o projeto e a configuração da compilação remota. O instalador pronto sai como **outro ZIP**, criado pelo GitHub Actions em Windows.

## Por que não precisa mais de Python e Visual Studio para usar?

- O painel é compilado como `LaserToolsFree.Docker.dll` com MSBuild no runner Windows 2022.
- O motor DXF vira `LaserDXFEngine.exe` e o editor DXF vira `LaserToolsFreeEditor.exe`, ambos empacotados com suas dependências via PyInstaller.
- O ZIP gerado contém `INSTALAR_PLUGIN.bat` para instalação no CorelDRAW 2024 e `DESINSTALAR_PLUGIN.bat`.
- **No PC que vai usar**, apenas CorelDRAW 2024 x64 e componentes normais do Windows/.NET Framework são necessários. Não é necessário instalar Python nem Visual Studio.

## Como obter o ZIP compilado sem instalar ferramentas de desenvolvimento

1. Entre em https://github.com/new e crie um repositório privado chamado, por exemplo, `laser-tools-free-build`.
2. Extraia ESTE ZIP no seu computador. No GitHub, envie todos os arquivos e pastas **da pasta raiz extraída**, incluindo a pasta oculta `.github/workflows` (não envie o próprio ZIP sem extrair).
3. Clique em **Actions > Gerar plugin CorelDRAW Windows > Run workflow**. Se o GitHub pedir para habilitar Actions, habilite no repositório.
4. Após a execução, abra a tarefa concluída. Em **Artifacts**, baixe `Laser_Tools_Free_CorelDRAW_2024_Pronto`. Esse é o pacote que deverá conter o arquivo `Laser_Tools_Free_CorelDRAW_2024_Pronto.zip`.
5. Extraia o ZIP interno, abra `Pacote_Pronto_CorelDRAW_2024` e execute `INSTALAR_PLUGIN.bat` com o CorelDRAW fechado.
6. Abra CorelDRAW e procure **Janela > Janelas de encaixe > Laser Tools Free**. Teste em um novo CDR simples.

Se a compilação ficar **vermelha**, não haverá instalador validado: guarde o log do passo que falhou. Este ambiente Linux não executa MSBuild/WPF ou o CorelDRAW real.

## Testes realizados fora do Windows

- Testes Python + estrutura XML e painel: `PYTHONPATH=Python_DXF python -m pytest -q Python_DXF/tests CorelAddon/tests`.
- O pipeline repetirá os testes no Windows, compilação WPF, conversão com PyInstaller e execução do EXE do motor DXF em um desenho de exemplo.

## Limitações e segurança

**Não foi validado no CorelDRAW 2024 nem no RDWorks real.** Não é o eCut completo: alguns algoritmos operam somente sobre geometrias suportadas. Antes de qualquer produção, confira dimensões, camadas, furos, curvas e a simulação do laser. A importação acontece em camada nova e o aplicativo gera backups CDR antes de editar. Se houver erro, não salve o documento alterado.

O pacote usa somente ferramentas próprias/de código aberto; não contém arquivos proprietários do eCut nem do CorelDRAW. O complemento usa a API do CorelDRAW instalada no computador do usuário.
