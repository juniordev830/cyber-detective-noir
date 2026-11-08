# Cyber Detective Noir

Protótipo de investigação noir com regras testáveis em Python. Esta branch contém
um **modo de demonstração por terminal**, independente de bibliotecas externas.
A integração visual com Godot é um trabalho separado; este módulo ainda não
controla a cena gráfica do jogo.

## Executar o caso demonstrativo

Requer Python 3.11 ou superior. Na raiz do repositório:

```bash
python detective_cli.py --save meu-caso.json new
python detective_cli.py --save meu-caso.json status
python detective_cli.py --save meu-caso.json locations
python detective_cli.py --save meu-caso.json hint
python detective_cli.py --save meu-caso.json inspect camera alley
python detective_cli.py --save meu-caso.json inspect badge alley
python detective_cli.py --save meu-caso.json inspect door lab
python detective_cli.py --save meu-caso.json inspect logs office
python detective_cli.py --save meu-caso.json suspects
python detective_cli.py --save meu-caso.json accuse technician
```

O comando `new` não substitui um salvamento existente. Cada descoberta e
acusação é persistida em JSON usando um arquivo temporário e substituição
atômica. Uma pista só pode ser coletada no local correto, após as dependências
serem desbloqueadas. Suspeitos exonerados pelas provas não podem ser acusados.

## Testes e integração contínua

```bash
python -m unittest discover -v -p 'test_*.py'
python -m compileall -q investigation.py casebook.py detective_cli.py
```

O workflow `.github/workflows/python-investigation.yml` executa os testes
automaticamente nas versões 3.11, 3.12 e 3.13 do Python.

## Arquitetura

- `investigation.py`: grafo acíclico de pistas, locais, pré-requisitos,
  dicas sem spoilers, progresso e remoção de descobertas dependentes.
- `casebook.py`: suspeitos, evidências exoneratórias, acusações,
  estado do caso, validação de saves e gravação atômica.
- `detective_cli.py`: comandos do modo jogável em terminal.
- `test_*.py`: testes de regras, persistência, integridade e fluxo completo.

O caso de exemplo possui seis pistas, três suspeitos e quatro provas
obrigatórias para uma acusação. A dica informa apenas uma pista acessível,
sem entregar a solução.

## Limitações e segurança

Este é um protótipo **local**, sem autenticação e sem integração com
servidores. O arquivo JSON contém a definição do caso, incluindo a resposta,
portanto **não é apropriado para distribuir mistérios sem spoilers**.
Salvamentos têm limite de 1 MiB, e o carregamento valida referências,
ciclos de dependências, tentativas e consistência do encerramento.
A gravação atômica protege contra arquivos parcialmente escritos, mas
não oferece criptografia, isolamento de usuários ou controle de acesso.

A interface gráfica Godot, arte, áudio e múltiplos casos não fazem parte
desta branch. Não mesclar com a `main` sem revisão e autorização.
