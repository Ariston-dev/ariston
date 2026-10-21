# Resultado dos testes — v5

- Motor Python DXF: **42 testes aprovados** (execução em Linux, Python 3.13, `ezdxf` e `shapely`).
- Estrutura do painel CorelDRAW (XML/XAML, manifesto, handlers, referencias do `.csproj` e presença de rotinas): **10 testes aprovados e 19 subtestes aprovados**.
- DXFs gerados em testes de integração por linha de comando com `clean`, `shape`, `rectangle`, `offset`, `report` e `rdworks` foram reabertos corretamente nos cenários avaliados.
- Originais DXF preservados nos testes, e falhas de entrada inválida geram erro em vez de sobrescrever fonte.

**NÃO TESTADO:** compilação da DLL do painel C#/.NET Framework 4.8, carregamento do docker no CorelDRAW 2024, operações de importação/exibição no CDR e importação/simulação física pelo RDWorks. Esses testes exigem Windows 11 + CorelDRAW 2024 + MSBuild + RDWorks. O ZIP contém **código-fonte e instalador para compilar**, e **não** DLL/EXE final pronto.

Em especial, os testes XML e Python não substituem integração COM real no Windows. Não interprete a contagem de testes como garantia de 100% de compatibilidade.
