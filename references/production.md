# Produção e direção de arte

## Da estratégia ao desenho

Transforme cada atributo em hipótese testável. “Técnica” pode aparecer em hierarquia precisa, repetição coerente e construção consistente. “Humana” pode aparecer em ritmo, fotografia e linguagem, sem obrigar cantos arredondados. A escolha depende do setor e do público.

Para cada direção, registre:

1. Ideia central ligada à marca, em uma frase específica.
2. Elemento reconhecível e lógica de construção.
3. Relação entre símbolo e tipografia.
4. Comportamento em uma cor e em escala reduzida.
5. Desdobramento em layout, grafismo ou família de produtos.
6. Trade-off real, não uma defesa promocional da proposta.

Direções diferentes não são a mesma marca com três cores. Diferencie estrutura, ritmo ou abordagem sem perder o briefing. Duas propostas bem resolvidas podem ser melhores do que uma terceira artificial.

## Evitar aparência genérica

Pergunte: sem o nome, esse símbolo serviria igualmente para dezenas de concorrentes? Se sim, encontre um vínculo mais específico ou uma solução tipográfica própria. Combinar dois ícones de biblioteca não garante originalidade.

Não force complexidade. Uma marca simples pode ter desenho preciso, proporções próprias e ritmo reconhecível. Uma marca complexa pode esconder uma ideia fraca. Originalidade precisa sobreviver sem textura, mockup e iluminação.

Refinamento útil inclui ajuste de curva, terminais, junções, espaços internos, relação de massas, kerning e modulação de traço. Evite mudanças microscópicas apresentadas como novo conceito. Mostre o efeito na leitura e no uso.

## Ferramenta de imagem e finalização

| Situação | Procedimento |
| --- | --- |
| Vetor existente protegido | Preserve a geometria e a aparência já aprovadas; use cópia para organização e exportação fiel. Não crie alterações visuais locais como atalho para edição nativa |
| Conceito com imagem generativa | Use obrigatoriamente o motor nativo `image_gen` do Codex, com referências vistas e briefing autorizado |
| Marca tipográfica ou geométrica nova | Crie a imagem pelo motor nativo. Se não houver fonte vetorial real aprovada, a entrega de vetor editável permanece pendente; não reconstrua por código para substituir o motor |
| Ilustração, banner, capa ou mockup | Gere e edite pelo motor nativo do Codex, sem substituir por desenho em código ou serviço externo |
| Motor nativo indisponível | Informe bloqueio da geração/edição. Avance somente no briefing ou documentação autorizados, sem motor alternativo |

Siga o [protocolo nativo](codex-image-engine.md) e as instruções atuais da ferramenta. Não contorne geração obrigatória desenhando com código. Em edição de imagem, use o mesmo motor nativo com a referência inspecionada e invariantes explícitas.

Não procure chaves nem ofereça API/CLI como fallback. O uso nativo não exige configurar `OPENAI_API_KEY`. Não prometa um nome de modelo, resolução ou formato que a ferramenta não confirmou. Defina quantidade de estudos no escopo criativo, não como contratação de uma API externa.

## Geometria e texto

- Vetor final deve ter geometria editável real quando esse for o formato contratado.
- Operações locais em vetor preservam a geometria existente e sua aparência. Mudanças criativas de forma, letras, cor ou composição em imagens pertencem ao motor nativo. Se isso impedir entregar o vetor solicitado, exponha a pendência; não invente compatibilidade nem outra arte.
- SVG com `<image>` não é automaticamente um mestre vetorial. Gradientes e filtros exigem teste no destino.
- Texto vivo requer fonte disponível e licenciada. Entregue uma versão editável e, se possível e autorizado, uma cópia com curvas para uso final.
- Não afirme “convertido em curvas” se ainda houver texto dependente de fonte.
- Confira acentos, cedilha, caixa, número, símbolo e grafia literal. Não corrija nome de marca por conta própria.
- Não distribua arquivos de fonte comercial com o pacote sem licença. Alternativas precisam de comparação e aprovação, não substituição silenciosa.
- Licença indefinida bloqueia o uso ou a distribuição afetados, não todo o projeto. Inventário, briefing e estrutura podem avançar. Permissão de usar a fonte em uma arte não implica permissão de distribuir o arquivo da fonte.
- RGB e HEX atendem tela; CMYK e perfil de impressão dependem de conversão e prova apropriadas. Não invente equivalência Pantone.

## Sistema e arquitetura

Escolha papéis de cor antes de combinações: fundo, texto, ação, destaque e uso decorativo. Assegure hierarquia mesmo sem a cor. Defina o que cada produto herda da marca e onde pode variar.

Não prenda uma marca permanente ao ano de um produto atualizável. Edição, data, turma ou versão normalmente pertencem ao título complementar ou layout da oferta, exceto quando o briefing determina o contrário.

Ícones auxiliares, padrões e ornamentos devem partir de uma lógica da marca, sem repetir o logo em todo canto. Mostre limites de uso para evitar saturação.

## Comparação justa

Apresente opções com a mesma caixa de apresentação, peso visual comparável, mesmo fundo e mesmo exemplo de aplicação. A escala óptica importa: igualar apenas altura de arquivo pode distorcer a comparação.

Testes de 16, 24 ou 32 px fazem sentido para ícones de interface; miniaturas de catálogo precisam do tamanho real do catálogo; banners precisam do viewport real. Não use uma dimensão fixa como selo universal de qualidade.

## Refinar feedback

Se vier “6/10”, “simples” ou “cara de Canva”, peça uma preferência concreta apenas quando não houver diagnóstico visível suficiente. Em seguida mostre duas correções focadas, com antes e depois. Não descarte uma direção já escolhida sem explicar o problema que exige isso.
