# Visual Identify Creator

Skill para planejar e criar identidades visuais dentro do Codex, com geração e edição de imagens exclusivamente pelo motor nativo `image_gen`.

Versão 1.1.0. Voltada a alunos, mentorados e profissionais que precisam desenvolver uma marca com briefing, comparação de conceitos, refinamento, aplicações e manual.

## O que faz

- Cria uma identidade nova a partir do contexto do negócio.
- Moderniza uma marca preservando os elementos reconhecidos e aprovados.
- Produz aplicações e documentação sem redesenhar uma identidade já aprovada.
- Registra versões e aprovações, distinguindo conceito escolhido de publicação autorizada.
- Organiza um manual visual com exemplos de uso, não apenas texto corrido.

## Motor de imagens

O uso do motor nativo de imagens do Codex é obrigatório para gerar e editar imagens. Não há fallback para API, CLI, SDK ou outro gerador, nem substituição das imagens por desenhos em código.

Não exige chave de API. Se o motor estiver indisponível, a etapa de imagens fica bloqueada; briefing e documentação podem continuar. Instalar a skill em outro aplicativo não disponibiliza o motor do Codex nesse aplicativo.

Os scripts deste repositório são auxiliares locais para contraste, inventário, organização e apresentação HTML. Eles não são geradores de imagens. Vetor editável exige uma fonte vetorial real e verificada; um bitmap não vira vetor ao mudar a extensão.

## Instalação

Baixe o repositório e coloque seu conteúdo em uma pasta chamada `visual-identify-creator` no diretório de skills usado pelo seu Codex. No ambiente com skills em `~/.codex/skills`, a estrutura será:

```text
~/.codex/skills/visual-identify-creator/SKILL.md
```

Mantenha as subpastas juntas. Não substitua uma instalação existente sem guardar a versão anterior. Abra uma nova conversa ou recarregue as skills se necessário.

Veja o [guia de instalação e uso](COMECE-AQUI.md).

## Como pedir

```text
Use $visual-identify-creator para criar a identidade visual da minha marca.
Meu negócio é [...], atende [...] e precisa funcionar em [...].
Quero comparar os conceitos antes de finalizar.
```

Para modernização, anexe os ativos existentes e explique o que deve permanecer. Para aplicações, indique a versão aprovada e as peças necessárias.

## Auxiliares e testes

Python 3.9 ou superior, somente biblioteca padrão. Os scripts locais não usam rede nem acessam credenciais.

```bash
python3 -B -m unittest discover -s tests -v
python3 scripts/brand_tools.py contrast --foreground '#777777' --background '#FFFFFF'
python3 scripts/build_review.py --input examples/review.json --output avaliacao-exemplo.html
```

O último comando usa um exemplo fictício de estrutura, sem logo ou identidade final. O arquivo de saída não deve existir. Consulte [comandos e limites](references/tools.md).

## Limites e privacidade

- A qualidade visual depende da criação, revisão e aprovação de cada projeto. A skill não promete uma boa marca com um clique.
- Os 62 testes da versão 1.1.0 verificam auxiliares e contrato documental. Não provam qualidade estética nem execução real do motor de imagens.
- Revisão visual do template HTML permanece pendente. O exemplo não deve ser apresentado como manual aprovado.
- O pacote contém instruções, código, template e dados fictícios de teste. Não inclui projetos de clientes, credenciais ou histórico de conversas.
- A geração nativa processa os insumos fornecidos ao Codex. Não envie dados sensíveis ou ativos sem autorização.
- A skill não publica, envia mensagens ou altera checkout sem autorização específica.

Leia [segurança e escopo dos dados](SECURITY.md) antes de usar materiais privados.
