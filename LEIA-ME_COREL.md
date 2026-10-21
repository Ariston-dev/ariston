# Laser Tools Free — prova de integração com CorelDRAW 2024

**Status honesto:** Esta integração é um **protótipo externo** em Python + pywin32 (COM). Trabalha diretamente com objetos selecionados no CorelDRAW, **sem VBA** e **sem necessidade de exportar DXF** para as ações abaixo. A janela ainda é independente do CorelDRAW; **não é um docker/plug-in nativo**. O módulo `laser_core.py` continua sendo usado no aplicativo DXF tradicional, não nesta primeira prova COM.

## Funciona neste protótipo

- Detectar o CorelDRAW já aberto e ler nome do CDR, contagem de objetos selecionados e dimensões.
- Duplicar a seleção como um único conjunto em grade (linhas, colunas, espaçamento). Usa posições relativas à caixa de seleção, preservando o conjunto original; não é nesting.
- Criar backup do desenho inteiro com `Document.SaveAsCopy` ANTES da alteração, no diretório escolhido, sem substituir o CDR original.
- Agrupar alterações no histórico de desfazer do CorelDRAW (quando disponível). **Não salvar automaticamente as alterações.**

## Como testar no Windows 11

1. Abra o CorelDRAW 2024, crie um **CDR de testes**, por exemplo 2 retângulos coloridos, e salve-o.
2. Escolha **milímetros** nas unidades do documento CorelDRAW. Este protótipo exige mm para cópias.
3. Selecione os dois retângulos; mantenha o CorelDRAW aberto.
4. Extraia este ZIP, execute **`INSTALAR_COREL_TESTE.bat`** (requer Python e internet) e depois **`ABRIR_COREL_TESTE.bat`**.
5. Clique **Ler seleção do CorelDRAW**. Verifique se o nome do arquivo, a quantidade de objetos e a largura/altura aparecem. Se o programa não encontrar o CorelDRAW, execute os programas como **mesmo usuário e nível de permissão** (ambos sem 'Executar como administrador').
6. Escolha linhas `2`, colunas `3`, espaço `3`, e uma pasta de backup válida, como Documentos.
7. Clique **Gerar grade no CorelDRAW** e confirme. O programa cria um `.cdr` de backup antes de modificar o desenho aberto. Deve gerar **cinco conjuntos novos**, preservando a seleção original (total seis conjuntos).
8. Confira o resultado dentro do CorelDRAW. Tente **Ctrl+Z** para desfazer a geração. Abra o CDR de backup e confirme que mantém o desenho anterior.
9. **Não use desenhos de produção nem corte a laser nesta fase.** O objetivo é validar COM e unidades no seu ambiente real.

Se o Python launcher `py` não estiver instalado, instale Python 3.11+ e marque a opção de adicionar ao PATH.

## Se algo falhar

- **`No module named win32com`**: execute `INSTALAR_COREL_TESTE.bat`.
- **CorelDRAW não encontrado**: abra o CorelDRAW desktop e um arquivo CDR, confira permissões e tente novamente.
- **Nenhum objeto selecionado**: selecione um ou mais objetos no próprio Corel antes de clicar.
- **Unidade diferente de mm**: ajuste para milímetros no CorelDRAW; o protótipo não altera a unidade por conta própria.
- **Falha ao salvar backup**: selecione uma pasta local com permissão de escrita. A operação não prossegue sem backup confirmado.
- **Falha no meio da duplicação**: volte ao CorelDRAW e use Ctrl+Z; o backup está preservado.

## Próxima etapa: painel de verdade dentro do CorelDRAW

Um **addon/docker em C#/.NET**, baseado no SDK oficial do CorelDRAW, dará acesso aos objetos selecionados com botões dentro do programa. O núcleo Python existente será reaproveitado por um adaptador de geometria (ou migrado por módulo para C#). Não se pode afirmar compatibilidade completa com CorelDRAW 2024 sem compilar o addon e testá-lo no Windows. A prova COM atual não instala barra, menu ou docker dentro do CorelDRAW.

Documentação oficial:
- [Addons no CorelDRAW](https://community.coreldraw.com/sdk/w/articles)
- [Acesso via automação externa](https://community.coreldraw.com/sdk/w/guide/210/8-2-working-with-the-application-object)
- [CorelDRAW 2024: ShapeRange.Duplicate](https://community.coreldraw.com/sdk/api/draw/25/m/shaperange.duplicate)
- [CorelDRAW 2024: Document.SaveAsCopy](https://community.coreldraw.com/sdk/api/draw/25/m/document.saveascopy)
