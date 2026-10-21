# Laser Tools Free v5 — CorelDRAW 2024 (protótipo integrado)

**Ferramenta gratuita original, desenvolvida independentemente do eCut.** Windows 11, CorelDRAW 2024 64-bit, *sem VBA*. Código-fonte para painel WPF C#/.NET Framework 4.8 + motor geométrico Python/ezdxf/Shapely.

> **AVISO TÉCNICO**: não existe DLL Windows pré-compilada neste pacote. Ela é **compilada no seu Windows** pelo instalador, com Visual Studio Build Tools/Community 2022 e .NET Framework 4.8 Developer Pack. O código Python passou nos testes em Linux, mas a DLL **não foi compilada nem carregada aqui no CorelDRAW**, nem testada em RDWorks físico. Não é correto tratá-lo como plugin final certificado nem garantir equivalência total ao eCut.

## Como instalar

1. Instale **Python 3.11/3.12 de 64 bits**, marcando `Add python.exe to PATH` ou disponibilizando o lançador `py`.
2. Instale **Visual Studio 2022 Community** (gratuito) ou Build Tools 2022 com **Desenvolvimento para desktop com .NET** e **.NET Framework 4.8 Targeting Pack**.
3. Feche o CorelDRAW 2024.
4. Extraia o ZIP completo (não execute diretamente de dentro do ZIP). Clique duas vezes em **`INSTALAR_TUDO.bat`**.
5. O instalador cria um Python isolado em `%LOCALAPPDATA%\LaserToolsFree\venv`, instala bibliotecas, faz um teste de DXF, compila a DLL e pede permissão do Windows para copiar os arquivos do complemento para `Programs64\Addons\LaserToolsFree`.
6. Abra **CorelDRAW 2024 > Janela > Janelas de encaixe > Laser Tools Free** (pode aparecer como `Window > Dockers`). Abra um **CDR novo de teste**, não um trabalho real.

Se aparecer *MSBuild não localizado*, não foi instalado o compilador do Visual Studio. Se a DLL não compilar, os erros aparecem no terminal. O instalador **não instala uma DLL falsa e não diz que concluiu** em caso de falha.

## Uso do painel

- **Seleção**: selecione contornos vetoriais e clique **Atualizar seleção**. O documento do Corel precisa usar **milímetros (mm)**.
- **Cópias**: cria grade de cópias diretamente no CDR.
- **Medidas**: redimensionamento e rotação ±90° diretamente no CDR.
- **Preparar corte > Remover segmentos duplicados**: exporta a seleção para DXF, executa `laser_cli.py clean` e, após confirmações, importa um DXF novo **em nova camada do mesmo CDR**. Pode haver limitações em polilinhas com arcos.
- **Preparar corte > Offset**: gera apenas novos contornos a partir de retas fechadas/círculos elegíveis; importa em camada nova.
- **Preparar corte > Nesting retangular**: preenche uma chapa com caixas envolventes conservadoras (apenas entidades fechadas elegíveis).
- **Preparar corte > Nesting real**: coloca polígonos fechados planos retos e círculos pelo **formato do contorno**, usa ângulos 0, 90, 180 e 270, até 60 peças e uma chapa. É **heurístico**, não promete aproveitamento ótimo nem aplica hierarquia de furos. Não aceita Bézier, spline ou bulge sem transformação prévia para polilinhas retas, e não trata grupos de peças como um bloco único.
- **Custos**: mede entidades reconhecidas; áreas são **somadas** e podem contar furos e sobreposições. Valores são estimativas, não cotações de tempo real.
- **RDWorks**: gera **DXF**, não arquivos `.rd` nem comandos do laser; precisa abrir, conferir unidade/camadas e simular no RDWorks.

A importação **não apaga os objetos originais**, gera camada adicional e cria **backup `.CDR`** antes da importação. O CorelDRAW não é salvo automaticamente. **Confira alinhamento/escala no CDR após importar**: comportamento do filtro DXF depende da instalação do CorelDRAW.

## Teste mínimo no CorelDRAW (quando a DLL compilar)

1. Crie um CDR novo em **milímetros**.
2. Desenhe dois **retângulos fechados vetoriais** de 20 × 10 mm e 15 × 8 mm.
3. Selecione-os. No painel, clique **Atualizar seleção**.
4. Na aba Preparar corte, defina chapa 100 × 80 mm, espaço 2 mm, margem 2 mm, cópias 1; clique **Nesting real de contornos retos**.
5. Confirme a exportação e a importação. Verifique no Gerenciador de Objetos a camada nova `LTF_shape_...`.
6. Confira contagem de objetos, dimensões com ferramenta de medição, distâncias mínimas e que o desenho original esteja na sua camada anterior.
7. Faça o mesmo com **Remover segmentos duplicados**, **Offset** e **Nesting retangular** em cópias de teste.
8. Só depois exporte o DXF para RDWorks. Confirme **1 unidade = 1 mm**, tamanho real e cores/camadas; execute a simulação de trajetória sem laser antes do corte real.
9. Execute `TESTAR_TUDO.bat` para os testes automatizados de código.

Se não aparecer painel: confira pasta de instalação `CorelDRAW Graphics Suite 2024\Programs64\Addons\LaserToolsFree`, se existe `LaserToolsFree.Docker.dll` e se o XSLT está ao lado. Consulte o **SDK do Corel**. Não redefina workspace usando F8 antes de fazer uma cópia das suas configurações.

## Estrutura

- `CorelAddon/LaserToolsFree.Docker/` — dock WPF, código C#, manifesto e XML/XSLT.
- `Python_DXF/laser_core.py` — motor anterior v3, preservado.
- `Python_DXF/laser_advanced.py` — nesting por formato, offset-only e exportação DXF.
- `Python_DXF/laser_cli.py` — execução não interativa para o painel, retorna JSON.
- `Python_DXF/tests/` e `CorelAddon/tests/` — testes Python e verificações estruturais.
- `COMPILAR.bat` — compilar manualmente quando Visual Studio/Build Tools estiverem instalados.
- `INSTALAR_NO_COREL.ps1` — copiar plugin compilado para CorelDRAW (administrador).
- `DESINSTALAR_DO_COREL.ps1` — remover apenas diretório do addon, mantendo seus dados.

## Limitações e segurança

- **Não é um clone pronto e completo do eCut**; não promete mais de 40 módulos.
- Não converte sozinho CURVE com nós Bézier para nesting; exportações DXF variam conforme configurações.
- Não garantimos precisão geométrica do CorelDRAW/RDWorks sem teste no ambiente real.
- Backups **não substituem Ctrl+Z** e não impedem que uma importação mal calibrada gere formas extras: não salve desenho de produção sem conferir.
- Os códigos não contêm componentes do eCut, nem quebram licenciamento, nem exigem VBA.

Referência oficial das extensões CorelDRAW: https://community.coreldraw.com/sdk/w/articles/173/custom-add-ons-in-coreldraw-corel-designer-and-corel-photo-paint

Referência oficial de filtros: https://community.coreldraw.com/sdk/w/guide/215/8-7-working-with-import-filters-and-export-filters

Comparação de funcionalidades anunciadas pelo eCut: https://www.ecutbrasil.com.br/fun%C3%A7%C3%B5es
