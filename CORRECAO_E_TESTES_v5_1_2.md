# Laser Tools Free v5.1.2 — Correção de codificação e pipeline Windows

## Problema confirmado em 21/10/2026
- Primeiro build: falha de `UnicodeDecodeError` em `cp1252` durante testes de estrutura.
- Segundo build: `UnicodeDecodeError: utf-8 codec cannot decode byte 0xe1`, em dois testes de CLI no Windows, pois o subprocesso Python produzia saída na codificação local e o processo pytest a lia em UTF-8.
- Nenhuma dessas execuções chegou à etapa de compilar a DLL C#.

## Correções desta versão
1. O motor CLI produz stdout e stderr explicitamente em UTF-8 (independente da região do Windows).
2. Os testes criam subprocessos explicitamente em UTF-8, controlando a codificação de entrada/saída e a variável de ambiente.
3. `EngineRunner.cs` decodifica saída/erros em UTF-8, compatível com o motor no Windows.
4. Teste novo reproduz saída acentuada com `PYTHONIOENCODING=cp1252` e valida JSON em UTF-8.
5. Compilação no GitHub foi dividida em **testes, painel C# e executáveis Python independentes**. A próxima execução mostra eventuais falhas destas etapas ao mesmo tempo, sem bloquear compilação da DLL por um teste.
6. A montagem do instalador só ocorre quando as três verificações anteriores forem aprovadas.
7. Binários gerados são verificados pela assinatura PE `MZ` e existência antes de distribuir.
8. Corrigido erro de indentação preexistente em `Python_DXF/corel_panel_externo.py`, fora da cobertura dos testes anteriores.
9. Incluída verificação sintática de **todos os arquivos Python** e auditoria dos arquivos DXF de exemplo.
10. Corrigido `TESTAR_TUDO.bat`, que se referia a um instalador e uma pasta Python antigos inexistentes na versão de desenvolvimento.

## Como atualizar sem reenviar os outros arquivos
1. Extraia o ZIP de correção (o pacote PATCH contém apenas arquivos alterados).
2. Pelo GitHub Desktop, use **Repository > Show in Explorer**.
3. Copie o conteúdo extraído do patch para a **raiz** do repositório, substituindo arquivos existentes.
4. Em Changes, veja apenas os arquivos modificados e o teste novo.
5. **Commit to main**, depois **Push origin**.
6. Acesse **Actions**: há jobs separados `Testes DXF / integracao`, `Compilar DLL WPF no Windows` e `Compilar Python portatil Windows`.
7. Se os três ficarem verdes, a etapa `Montar pacote apos todas as verificacoes` produzirá o ZIP em **Artifacts**.

## Resultado e limite do que foi testado
- Testes Python executados neste ambiente Linux: verifique TESTES_LOCAIS_v5_1_2.txt.
- O GitHub fará a validação real de compilação e EXE no Windows.
- Ainda é necessário testar pessoalmente o carregamento de docker no CorelDRAW 2024 e ida/volta DXF com o RDWorks. Não use DXFs de produção antes desta validação.
