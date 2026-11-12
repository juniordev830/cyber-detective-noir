# Cyber Detective Noir

Jogo de investigação de atmosfera noir **planejado**, com análise de evidências, diálogo e decisões.

> **Estado atual:** apenas documentação inicial e licença. Não há capítulos, assets, diálogos interativos ou executável neste repositório.

## Escopo narrativo inicial

Um caso fictício curto com três locais, três pistas e uma conclusão alcançada por dedução. Para manter a primeira versão testável, o jogo pode começar em formato texto antes de receber cenários gráficos.

## Núcleo de regras

- Cada pista tem ID, descrição e condição de descoberta.
- Uma pista descoberta não deve ser duplicada no inventário.
- A dedução final exige um conjunto explícito de evidências, não um palpite escondido do código.
- O jogador pode rever pistas e voltar aos locais sem perder progresso.
- Decisões que alteram o estado devem ser reproduzíveis após recarregar um save.

## Critérios de aceitação

1. Três pistas fictícias podem ser descobertas em qualquer ordem permitida.
2. O caderno mostra apenas pistas coletadas.
3. Acusar alguém sem evidências suficientes apresenta uma resposta clara, sem travar a história.
4. Completar o conjunto de pistas desbloqueia conclusão.
5. Salvar e carregar preserva escolhas e pistas sem duplicar eventos.

## Implementação sugerida

- [ ] Escrever um caso original, com árvore simples de decisões.
- [ ] Testar lógica de evidências e estado em módulo independente da interface.
- [ ] Criar protótipo navegável em texto.
- [ ] Evoluir para UI e recursos visuais com licenças verificáveis.
- [ ] Documentar a execução real antes de anunciar demo.

Não usar dados pessoais reais nem simular coleta indevida de informações de terceiros.
