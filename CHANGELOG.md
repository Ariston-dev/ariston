# Laser Tools Free — histórico

## v5 (código, integração experimental CorelDRAW 2024)
- Motor DXF CLI com resultado JSON e falhas explícitas.
- Nesting por contornos retos/círculos utilizando Shapely, com checagem de colisões, margem e espaçamento (máximo 60 peças em 1 chapa).
- Offset exportando apenas as curvas geradas, sem importar cópias redundantes.
- Preparação DXF mm com bloqueio de entidades não suportadas.
- Botões integrados no docker de preparação e custos.
- Exportar seleção, executar motor em thread secundária, importar em camada NOVA após confirmação e backup CDR.
- Instalador Python+MSBuild+addon para Windows com teste de pré-instalação, sem VBA.
- Testes de geometria, CLI, XML/XAML e segurança dos arquivos.

## v4 (base herdada, preservada)
- Código inicial do docker WPF, edição direta de medidas e cópias.
- Exportar seleção DXF sem retorno automático ao Corel.

## v3
- Motor Python/ezdxf, limpeza, relatório, escala, offsets e nesting retangular.
