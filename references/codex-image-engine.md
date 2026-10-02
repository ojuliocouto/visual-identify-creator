# Protocolo obrigatório de imagens no Codex

## Regra de execução

Todas as gerações e edições de imagem desta skill usam exclusivamente a ferramenta nativa `image_gen` do Codex. Use o schema realmente disponível no ambiente, não um endpoint HTTP, API, SDK, CLI ou automação de outro gerador.

Não transforme indisponibilidade, limite, preferência de formato ou demora em justificativa para trocar de motor. Informe a limitação. Não peça uma chave de API, não configure cobrança externa e não prometa acesso ao motor por instalar esta skill em outro aplicativo.

O pedido explícito de criar imagens, com briefing suficiente e escopo definido, autoriza executar o motor nativo. Não peça confirmação genérica outra vez. Pedido apenas de planejamento, auditoria ou instalação de skill não autoriza geração de imagens por si só.

## Fluxo real, não só prompts

1. Confira o briefing, os textos literais, as referências e os elementos protegidos.
2. Leia a skill `imagegen` disponível no ambiente, aplicando apenas o modo nativo. Siga as instruções da ferramenta para chamada, espera e apresentação do resultado. Este protocolo não autoriza seu fallback CLI.
3. Classifique como geração nova ou edição. Em edição, liste precisamente o que muda e o que permanece. Em geração por referência, diferencie a imagem de estilo da imagem que é o alvo de edição.
4. Abra referências locais com `view_image` antes de usá-las. Se não conseguir ver a referência crítica, peça o arquivo acessível. Não finja preservar um símbolo ou rosto que não examinou.
5. Monte um prompt específico por proposta, com finalidade, conceito, composição, paleta, texto literal, invariantes e itens a evitar. Não invente slogan ou promessa. Não use “premium” como único direcionamento.
6. Faça uma chamada nativa real por peça ou variante solicitada. Produza um conjunto comparável quando o escopo pedir opções; não obrigue novas aprovações entre cada imagem do mesmo conjunto já autorizado.
7. Apresente o resultado real inline pelo mecanismo da ferramenta. Não substitua a imagem por uma descrição ou pelo prompt.
8. Inspecione a saída: símbolo, letras, acentos, cor, proporções, margens, fundos, detalhes e fidelidade à referência. Corrija desvios pelo próprio motor nativo, com uma mudança objetiva por rodada.
9. Salve os ativos destinados ao projeto na pasta do projeto, com versão e nome claros. Use o caminho efetivamente retornado pelo motor. Se a imagem veio apenas para visualização e não há arquivo recuperável por ferramenta autorizada, informe essa limitação; não invente o caminho.
10. Registre prompt, referências, arquivo/versão, motor nativo utilizado e o que foi revisado. Uma imagem gerada continua proposta até aprovação.

## Referências e parâmetros

Leia o schema atual do motor, pois nomes e capacidades podem variar. Quando houver `referenced_image_paths`, use-o se todas as referências tiverem caminhos locais acessíveis, após inspeção. Quando ao menos uma não tiver caminho local, use `num_last_images_to_include` com a menor quantidade que inclua os alvos, até o limite aceito pela ferramenta. Não use ambos na mesma chamada. Se não puder incluir todas as referências necessárias, peça novo anexo.

Para geração completamente nova, não inclua parâmetros de referência vazios ou artificiais. Não adivinhe parâmetros de resolução, máscara, modelo ou destino inexistentes. Descreva a composição e o formato desejados no prompt e verifique dimensões e arquivo reais após a geração.

Para transparência, peça fundo realmente transparente ao motor e confira o canal alpha; desenho de quadriculado não comprova transparência. Edição de fundo, recorte criativo, retoque e alteração de composição também pertencem ao motor nativo, não a scripts de imagem alternativos.

## Especificação de prompt para marca

Use apenas os campos pertinentes, preenchidos com o briefing real:

```text
Finalidade: estudo de identidade para [marca e uso]
Conceito: [ideia específica ligada ao negócio]
Construção visual: [estrutura, ritmo, relações e detalhes desejados]
Tipografia: [características e hierarquia, sem presumir fonte exata recuperável]
Paleta: [cores e papéis definidos para esta direção]
Composição: [marca isolada, espaço útil, fundo e proporção da prancha]
Texto literal: "[nome com grafia exata]"
Preservar: [elementos obrigatórios]
Alterar: [somente o escopo desta edição, quando aplicável]
Evitar: [clichês e restrições concretas do briefing]
Comparação: [mesmo contexto de apresentação das outras opções]
```

Não use uma geração com o manual inteiro em uma única imagem para substituir um manual legível. Gere os ativos visuais nativamente e monte a documentação em HTML ou documento apropriado, com texto pesquisável e regras verificadas.

## O que não é um motor alternativo

- HTML/CSS para montar manual, galeria, legendas, amostras de cor, navegação e animações de apresentação.
- Cálculo de contraste, leitura de dimensões, hash, inspeção, cópia de arquivos e empacotamento.
- Preservação e uso de uma marca já aprovada, sem regeneração desnecessária.
- Organização e exportação fiel de um vetor existente já aprovado, quando solicitadas e verificadas. Não redesenhe nem reconstrua por código a imagem gerada para criar um mestre alternativo. Se não existir fonte vetorial apropriada, a entrega vetorial fica pendente. Não declare raster como vetor.

Nenhum desses recursos autoriza recriar, retocar ou simular por código uma imagem que deveria ter sido gerada/editada pelo motor nativo. Se a saída solicitada exigir capacidade que não existe, registre a pendência em vez de afirmar que foi entregue.

## Testar e reportar com precisão

Testes de texto podem verificar se este protocolo está presente, mas não provam que o agente chamou o motor ou que a arte ficou boa. Em teste sem geração, registre: “geração nativa real não foi executada”. Uma demonstração real exige um pedido de imagem autorizado, chamada bem-sucedida, saída visível e revisão da imagem produzida.
