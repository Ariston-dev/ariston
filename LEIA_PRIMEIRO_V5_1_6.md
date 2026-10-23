# Laser Tools Free v5.1.6 — correção da falha SaveAsCopy (CorelDRAW 2022)

## O erro encontrado

Na versão v5.1.5, a cópia de segurança chamava `doc.SaveAsCopy(path)` pelo host WPF / COM. No computador do usuário, a API apresentou a mensagem: **“Não foi possível converter argumento 0 da chamada em SaveAsCopy.”** A operação foi interrompida antes da duplicação.

A documentação CorelDRAW 2022 apresenta `SaveAsCopy(FileName, Options)`, mas a compatibilidade dessa chamada dinâmica não foi demonstrada neste host. Para eliminar essa dependência na operação de edição, **v5.1.6 faz a cópia de backup a partir do CDR já salvo no disco usando a API de arquivos do Windows**.

## Segurança — comportamento intencional

- O documento precisa ter sido salvo **em formato `.cdr`** por meio de Arquivo > Salvar como (ou Ctrl+S em um CDR existente).
- Se houver alterações não salvas, a ferramenta avisa para pressionar Ctrl+S antes de continuar; não salva silenciosamente.
- O aplicativo **não altera o arquivo CDR no disco**; duplica ou transforma a seleção **no documento aberto** após confirmar o backup.
- Backups ficam em `Documentos\LaserToolsFree\Backups` com nomes únicos. A antiga DLL é preservada pelo instalador em `Documentos\LaserToolsFree\PluginBackups`.
- O novo botão **Testar backup (sem modificar desenho)** permite verificar a proteção antes de duplicar qualquer coisa.
- Ao salvar manualmente o desenho **depois** da operação, o CorelDRAW atualizará o CDR como de costume; o backup criado antes permanecerá disponível.

## Como atualizar a partir do GitHub Desktop

1. Extraia este ZIP da correção.
2. Abra GitHub Desktop > Repository > Show in Explorer e copie as pastas `.github`, `CorelAddon` e `Distribuicao_Windows` da correção para **a raiz** do repositório `Ariston`, substituindo os arquivos correspondentes. Não envie o ZIP em si.
3. Em GitHub Desktop, faça **Commit to main** e **Push origin**.
4. Na aba Actions, aguarde a execução mais recente. Confirme **Testes DXF/integracao**, **Compilar DLL WPF no Windows**, **Compilar Python portatil** e **Montar pacote** em verde.
5. Baixe o artefato principal `Laser_Tools_Free_CorelDRAW_2024_Pronto`. O nome do artefato permanece o mesmo para não quebrar o processo existente, mas o instalador da correção procura **2022 e 2024** e prioriza 2022.
6. **Extraia completamente** os ZIPs até localizar `INSTALAR_PLUGIN.bat` junto à DLL e pasta `engine` (não execute de dentro de ZIP).
7. Feche o CorelDRAW 2022, execute o `INSTALAR_PLUGIN.bat` como administrador, e inicie o CorelDRAW novamente.
8. Confirme no cabeçalho do painel: `CorelDRAW 2022 · integração experimental v5.1.6`.

## Teste controlado (sem usar um CDR de produção)

1. Crie um novo desenho CorelDRAW de teste e um retângulo 30 x 20 mm.
2. Escolha **Arquivo > Salvar como**, selecione **CDR** e salve o documento. Isso é obrigatório na estratégia segura desta versão.
3. No painel, clique **Testar backup (sem modificar desenho)**. Espera-se a mensagem de backup criado e um `.cdr` dentro da pasta `Documentos\LaserToolsFree\Backups`.
4. Selecione o retângulo, clique **Atualizar seleção**, informe **2 linhas, 3 colunas, 3 mm** e clique em **Gerar cópias no desenho**.
5. Resultado esperado: 6 peças no total, sem alterar o CDR de disco automaticamente. Confira o backup e as medidas.
6. Se fizer qualquer modificação no documento, **salve explicitamente** antes da próxima operação com backup; caso contrário, o plugin recusará sem modificar os objetos.

## Testes realizados / limitações

- Testes locais Python: **73 aprovados, 20 subtestes aprovados**, incluindo validação da estrutura, contratos e proteção de arquivos.
- Um teste adicional em C# (`CorelAddon/tests/BackupSmoke`) foi criado para compilar e executar no GitHub Actions usando um documento Corel simulado. Exercita cópia de backup, retenção do original, recusa por alterações não salvas e grade 2x3. **Não foi executado neste ambiente Linux**; somente uma execução verde do GitHub comprovará sua compilação e execução Windows.
- A conexão real da DLL com o CorelDRAW 2022 e a geometria produzida ainda precisam de validação no computador com o CorelDRAW. Não há garantia de 100% de compatibilidade.
