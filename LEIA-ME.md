# Laser Tools Free v3 — Windows 11 / CorelDRAW 2024 / RDWorks

**Software livre de dependência do eCut**: este é um programa Python independente, não uma cópia do plugin, não contém código do eCut e não usa VBA nem altera licenças de terceiros. **Não há integração direta com CorelDRAW nem RDWorks**: a comunicação usa DXF e o trabalho deve ser conferido no RDWorks.

## Comece em 5 minutos

1. Instale o **Python 3.11 ou superior** para Windows e habilite Python Launcher (`py`).
2. Extraia **todo** o ZIP para uma pasta, por exemplo `Documentos\LaserToolsFreeV3`.
3. Dê dois cliques em **INSTALAR.bat** (necessita internet para baixar `ezdxf` e `shapely`).
4. Dê dois cliques em **ABRIR.bat** para abrir a interface.
5. No CorelDRAW 2024, trabalhe em uma **cópia do desenho**; escolha mm, converta texto e contornos em curvas conforme necessário e exporte **DXF**. Evite objetos rasterizados, efeitos e blocos com geometria não explodida.
6. No Laser Tools Free, escolha seu DXF, a ferramenta desejada, e gere **outro arquivo**. O programa não sobrescreve a entrada; se o nome de saída já existir, adiciona sufixo `..._2`, `..._3` etc.
7. Importe o DXF **gerado** no RDWorks. Confira dimensões reais, cores/camadas, duplicações, sentidos, ordem de operações e faça **simulação em vez de iniciar o corte diretamente**.

Se `.bat` não funcionar, abra o **Prompt de Comando** na pasta e rode:

```bat
py -m pip install -r requirements.txt
py laser_tools_free.py
```

Para executar os testes automatizados:

```bat
py -m pip install pytest
py -m pytest -q
```

Para criar um `.exe` **na sua máquina Windows** (o pacote entregue contém código, não um EXE pronto):

```bat
py -m pip install pyinstaller
py -m PyInstaller --onefile --windowed --name LaserToolsFreeV3 --collect-all ezdxf --collect-all shapely laser_tools_free.py
```

Ou rode **EMPACOTAR_EXE.bat**, gerando `dist\LaserToolsFreeV3.exe`. Execute os testes da versão `.exe` no seu PC antes de distribuí-lo.

## Teste de cada recurso

Cada exemplo de teste está na pasta `exemplos`.

**A. Limpeza (`duplicadas_e_sobrepostas.dxf`)**
- Escolha a aba **Limpeza**, mantenha precisão 4 e opção de sobreposição parcial marcada.
- Gere um novo DXF e compare as entidades no CorelDRAW ou no RDWorks.
- Procure o sufixo `_limpo_v3.dxf`. Segmentos LINE coincidentes são retirados/cortados somente se coincidirem estilo e camada. Duplicatas completas de `LWPOLYLINE` e `POLYLINE` 2D também são tratadas.
- Limite: **não** elimina sobreposição parcial entre duas polilinhas distintas nem entre arcos/splines. Não elimina o original.

**B. Medições (`figuras_fechadas.dxf`)**
- Aba **Medições e custo**, unidade **mm**.
- Informe **100** em material (R$/m²), **10** em corte (R$/m), e **2** em custo fixo.
- Calcule; o relatório mostra tipo e quantidade de entidades, dimensão envolvente e custos aproximados.
- **Atenção:** não subtrai furos, ilhas e desenhos sobrepostos da área; não é tempo real de máquina. A unidade deve ser conferida manualmente com o DXF exportado.

**C. Escala/cópias (`linha_para_escala.dxf`)**
- Aba **Escala e cópias**: X=200%, Y=200%, total 3, gap X=5, gap Y=0.
- Saída terá três linhas (na unidade do arquivo) com cópias deslocadas. Verifique seu tamanho antes de cortar.
- Escala desigual em curvas circulares pode não ser suportada; o programa exibe erro e não grava um arquivo parcial.

**D. Nesting (`figuras_fechadas.dxf`)**
- Aba **Nesting retangular**: chapa 200×120, margem 5, distância 3, cópias 2, giro de 90° permitido.
- Gere `_nest_retangular_v3.dxf` e confira os contornos da chapa.
- **Não é true-shape nesting:** usa somente as caixas que circunscrevem os contornos. Não aceita textos, linhas soltas, blocos, HATCH nem objetos compostos. Uma única peça representada por vários contornos deve ser agrupada/transformada numa entidade compatível antes de usar. **Não divide o trabalho em várias chapas**: se não couber, interrompe sem salvar.

**E. Offset (`figuras_fechadas.dxf`)**
- Aba **Contornos / Offset**: distância +2 cria contornos para fora; -2 desloca para dentro.
- Abra o resultado e encontre a camada `LASER_OFFSET` vermelha. **Original e offset coexistem**: filtre a camada correta no RDWorks para não cortar duas vezes.
- Aceita círculos e polilinhas LWPOLYLINE fechadas e retas. Ainda não gera offsets de curvas com bulge, SPLINE, elipses ou formas ligadas por múltiplos contornos.

**F. Percurso (`linhas_percurso.dxf`)**
- Aba **Percurso de corte**: gere `_percursos_v3.dxf`, veja comprimento de movimentação entre cortes no relatório.
- O recurso só suporta DXF constituído de `LINE` e usa o método guloso de proximidade por camada.
- **Não é controle de máquina**: o RDWorks pode escolher outra ordem. Simule no software da controladora.

## Limitações técnicas e avisos

- Somente o **Modelspace** (espaço do modelo) é processado.
- Em DXF do CorelDRAW, múltiplos componentes podem representar uma única peça. O programa não entende automaticamente essa relação.
- `LWPOLYLINE` pode armazenar **bulges** (arcos); a função de limpeza evita tratar arcos como retas. Os cálculos de perímetro/área incluem arcos circulares representados por bulge.
- Tolerância de limpeza indicada em **casas decimais**, independentemente de mm/cm/m. Confira configurações.
- O nesting não considera furos, geometria irregular nem a largura do feixe (kerf). Sem sinalizadores de início/fim de corte, tabs, lead-ins ou pontes.
- Preço é um cálculo orientativo, não orçamento industrial preciso; não usa horas de máquina, depreciação ou perdas reais de material.
- Antes de utilizar com laser real: confirme mm, dimensão, máquina, frequência, velocidade, espessura e **ordem de corte interna/externa** no RDWorks.
- O código da versão **v2 original** está preservado em `versao_2_original/`.

## Arquitetura

- `laser_core.py`: algoritmos e entrada/saída DXF, importável para outras aplicações.
- `laser_tools_free.py`: interface Tkinter.
- `tests/`: testes de regressão com `pytest`.
- `exemplos/`: DXFs sintéticos gerados para testar cada função.
- `MAPA_DE_FUNCOES.md`: funcionalidades públicas de referência e situação do projeto.

Não foi possível validar este aplicativo dentro do **CorelDRAW 2024** nem do **RDWorks** reais a partir deste ambiente. A revisão nesses programas é obrigatória.
