# Laser Tools Free v5.1 — código-fonte preparado para build Windows

**Comece em [LEIA_ME_INICIO.md](LEIA_ME_INICIO.md).**

Este pacote de desenvolvimento não contém a DLL ou os EXEs Windows. O workflow em `.github/workflows/compilar-plugin-windows.yml` tenta criar, testar e empacotar as versões binárias em um runner Windows 2022 do GitHub Actions. Se a compilação for concluída com sucesso, o ZIP produzido é instalável e o PC do usuário não precisa de Python ou Visual Studio.

## O que foi verificado neste ambiente

- 56 testes automatizados em Python para geometria DXF, regras de integridade e estrutura do addon; 19 subtestes também aprovados.
- Execução direta do motor `laser_cli.py report` com um exemplo DXF, retornando JSON.
- Não foi possível compilar a DLL WPF nem os EXEs do Windows neste ambiente Linux.
- A DLL nunca foi carregada e usada em CorelDRAW 2024 real; o fluxo de DXF para RDWorks também não foi validado em hardware/produção.

## Próximo passo de integração

Compilar com o workflow, baixar o artifact, instalar e testar no CorelDRAW 2024. Não usar em arquivos de produção antes de validar unidades e geometrias.
