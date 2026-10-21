# Catálogo público eCut e estado REAL do Laser Tools Free v5

Referência de **funcionalidades anunciadas ao público**, NÃO código, engenharia reversa de binário, interface copiada ou apropriação do eCut: https://www.ecutbrasil.com.br/fun%C3%A7%C3%B5es

| Categoria pública do eCut | Laser Tools Free v5 | Limite conhecido |
|---|---|---|
| Encaixe automático | PARCIAL | Nesting por polígonos simples, heurístico, um painel, sem grupos/furos e sem spline |
| Encaixe retangular | PARCIAL | Aceita contornos fechados elegíveis, uma chapa |
| Multiplicação | SIM no código | Grade nativa Corel, precisa teste Windows |
| Cortar/imprimir | NÃO | Somente DXF; não controla máquina |
| Linhas para depilar | NÃO | — |
| Separar curvas | NÃO | — |
| Mostrar interseções | NÃO | — |
| Encontrar/remover duplicadas | PARCIAL | Linhas/polilinhas DXF; não curvas Bézier |
| Criar contorno de corte | PARCIAL | Offset de polígonos retos e círculos |
| Criar marcas simples | NÃO | — |
| Área/perímetro/custo | PARCIAL | Agregado por entidade sem dedução de furos/sobreposição |
| Tempo de corte | NÃO | Não simula potência e velocidade de máquina |
| Volume | NÃO | — |
| LED/Ilhós/NEON/Letra caixa | NÃO | — |
| Código G | NÃO | — |
| Grades CAD e linhas | PARCIAL | Grade de cópias, não todas ferramentas CAD |
| Criar caixa e malhetes | NÃO | — |
| Divisão esperta / fatiar | NÃO | — |
| Centro de linha | NÃO | — |
| Conectar caminhos | NÃO | — |
| Reduzir pontos e arredondar curvas | NÃO | — |
| Ferramentas CAD completas | NÃO | Apenas transformações simples |
| Exportar DXF | PARCIAL | Exporta novo DXF em mm, não testado com hardware |
| Otimizar caminho | PARCIAL no Python v3 | LINE somente, pode ser ignorado pelo RDWorks |
| Alinhar/Definir tamanho | PARCIAL | Escala e grade nativa |
| Procurar/trocar objetos | NÃO | — |

**SIM no código não significa testado em CorelDRAW.** A DLL WPF precisa de compilação no Windows. Operações críticas exigem verificação de dimensões e simulação RDWorks.
