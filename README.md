# Cyber Detective Noir

Protótipo de investigação noir com regras testáveis em Python. Este repositório contém
um **modo de demonstração por terminal**, independente de bibliotecas externas.
O modo de terminal funciona de forma independente da interface Godot.

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
desta versão. As alterações foram revisadas e autorizadas para integração ao branch principal.

## Incremento: relatório de investigação

`case_report.py` produz relatório JSON de pistas coletadas, pistas disponíveis, pré-requisitos bloqueados e progresso sem alterar o save ou expor a solução por adivinhação.

```bash
python case_report.py
python case_report.py investigacao.json
python -m unittest test_case_report.py -v
```

O arquivo opcional `investigacao.json` segue o formato versionado de `Investigation.to_dict()`. O relatório não substitui a interface narrativa.

## Próximas etapas

O escopo original prevê capítulos com cenários interativos, diálogos e integração gráfica. O modo terminal entrega apenas a primeira experiência verificável; o conteúdo narrativo mais amplo continua planejado. Todos os casos e personagens demonstrativos são fictícios.

## Protótipo visual em Godot

O modo visual é um protótipo de investigação visual 2D em Godot 4.2+, com um caso curto e gráficos geométricos de estilo neon/noir.

### Como jogar
1. Abra `project.godot` no Godot e pressione **F5**.
2. Clique nos três locais de investigação para descobrir pistas.
3. Após encontrar todas as pistas, escolha o suspeito.
4. Pressione **R** para reiniciar.

## História demonstrativa
No caso **O Chip Desaparecido**, a câmera foi desligada, um cartão de acesso foi usado e não havia sinais de arrombamento. O jogador deve conectar as pistas e apontar o responsável.

## Funcionalidades
- Cena urbana em 2D com chuva animada e painéis de investigação.
- Três locais clicáveis, quadro de evidências, interrogatório dos suspeitos e conclusão.
- Regras isoladas em `scripts/case_rules.gd` e testes `tests/test_case_rules.gd`.
- CI headless verifica as regras e a carga inicial da cena.

## Executar testes
```bash
godot --headless --path . --script tests/test_case_rules.gd
```

## Limitações
É um protótipo de um caso, sem diálogos ramificados, salvamento, inventário persistente, arte final, áudio ou múltiplos cenários. O editor Godot deve ser usado para validar a experiência visual antes de publicar o jogo.


## Sistema de dicas (novo)

Durante a investigação, pressione **H** para receber uma orientação sobre a próxima pista ainda não encontrada. As dicas não identificam o culpado: apenas apontam o local que falta examinar. O quadro agora mostra quantas evidências estão pendentes.

O cálculo foi isolado em `scripts/case_rules.gd` e coberto por testes, incluindo estados completos e dados inválidos. Após concluir o caso, as dicas não alteram o resultado; use **R** para reiniciar.
