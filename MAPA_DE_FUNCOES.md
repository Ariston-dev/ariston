# Laser Tools Free × funções publicamente documentadas do eCut

Referência **somente descritiva**: lista pública em https://www.ecutbrasil.com.br/fun%C3%A7%C3%B5es e https://www.ecutbrasil.com.br/o-que-%C3%A9-o-ecut. Não foi usado software binário, API privada nem código proprietário do eCut.

| Família de funcionalidade | Laser Tools Free v3 | Etapas de implementação futura |
|---|---|---|
| Encontrar duplicadas / remover bordas | Parcial: LINE; duplicatas completas LW/POLYLINE; sobreposições de LINE contra segmentos retos | arcos, curvas, sobreposição parcial entre polilinhas |
| Perímetro / Área | Parcial: LINE, ARC, CIRCLE, LW/Polyline 2D com bulge | polígonos com furos, contornos compostos, splines, metrologia por grupo |
| Calcular custo | Parcial: material nominal por área, metros de corte, fixo | rendimento por chapa, tempo por camada, tabelas comerciais |
| Multiplicação / Definir tamanho | Escala X/Y e cópias lineares | matrizes, por seleção, agrupamentos |
| Encaixe retangular | Implementado: caixa envolvente por entidade fechada | múltiplas chapas, peças agrupadas, intertravamento avançado |
| Encaixe automático por forma | **Não implementado** | true-shape nesting com interseção poligonal e rotação otimizada |
| Criar contorno de corte | Parcial: offset simples de LW reta e círculo | curvas, contornos compostos, ilhas, offset robusto |
| Otimizar caminho | Parcial: sequenciar e inverter somente LINE | polígonos, arcos, priorização de furos, ordem por camada, lead-in |
| Exportar DXF | Salvar cópia em formato DXF mantido | compatibilidade de importação mapeada e ajustes RDWorks |
| Ferramentas CAD / conectar caminhos / reduzir nós | **Não implementado** | conexão tolerante, nós, fillets, centros |
| Caixa com malhete, caixa delimitadora, LEDs, NEON, ilhós | **Não implementados** | módulos de design paramétrico |
| Criar grelhas, variáveis, marcas de corte, códigos de barras | **Não implementados** | módulos auxiliares |
| G-Code/CNC | **Não implementado** | exportador próprio validado por controlador alvo |
| Integração com CorelDRAW sem VBA | **Não implementada** | avaliar automação externa/COM e limitações oficiais |

**Meta**: desenvolver comportamentos funcionalmente equivalentes com código próprio, não reprodução fiel da interface, marca, algoritmos ou licenças de outro software.
