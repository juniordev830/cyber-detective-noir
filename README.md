# Cyber Detective Noir

**Estado:** protótipo de investigação visual 2D em Godot 4.2+, com um caso curto e gráficos geométricos de estilo neon/noir.

## Como jogar
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
