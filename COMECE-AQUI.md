# Visual Identify Creator

Versão 1.1.0. Skill para planejar e criar identidades visuais dentro do Codex, usando obrigatoriamente o motor nativo de imagens para geração e edição. Abrange logos, modernização, aplicações e manuais, com aprovações registradas ao longo do processo.

## Instalar

Extraia o ZIP. Copie a pasta `visual-identify-creator` inteira, mantendo `SKILL.md`, `references`, `scripts`, `assets`, `examples`, `agents` e `tests` juntos.

- Codex: coloque em `~/.codex/skills/visual-identify-creator` no ambiente que já usa esse diretório de skills.
- Outros ambientes: o planejamento e os auxiliares locais são portáteis, mas a criação de imagens exige acesso real ao motor nativo do Codex. Instalar a skill no Claude Code não fornece o motor do Codex. Não substitua por API ou outro gerador.

Não substitua uma instalação existente sem guardar a versão anterior. Abra uma nova conversa ou recarregue a lista de skills se ela não aparecer. O pacote não instala ferramentas de imagem, editor vetorial ou Python.

## Pedir o trabalho

No Codex:

```text
Use $visual-identify-creator para criar a identidade visual da minha marca.
Meu negócio é [descrição] e atende [público].
Preciso usar a marca primeiro em [canais].
Quero avaliar a direção antes da finalização.
```

Também pode mencionar o nome da skill em linguagem natural no Codex. A disponibilidade do motor é verificada antes da etapa de imagens.

Para modernizar:

```text
Use visual-identify-creator para modernizar esta identidade.
Preserve [elementos reconhecidos] e melhore [problema concreto].
Estes são os arquivos atuais e o feedback de quem aprova.
```

Para aplicar uma identidade aprovada:

```text
Use visual-identify-creator para montar o manual e as peças abaixo.
Esta é a versão aprovada. Não redesenhe a logo.
Entregáveis: [lista].
```

## O que esperar

A skill parte do que você já forneceu, pergunta o que ainda importa e organiza o trabalho em briefing, direção, conceitos, refinamento, aplicações e entrega. Uma escolha de conceito não autoriza publicação automática.

Ela não garante uma boa marca com um clique. A aprovação estética continua sendo sua. Sem o motor nativo, a etapa de imagens fica bloqueada, sem troca automática de ferramenta. Não é necessário fornecer chave de API. Geração ou edição autorizada será executada no próprio Codex, não apenas transformada em um prompt para usar fora daqui.

HTML do manual, inspeção, cálculos e organização usam ferramentas locais. Isso não substitui a criação das imagens. Vetor editável exige uma fonte vetorial real e verificada; sem ela, essa entrega fica pendente. Imagem gerada não se torna vetor pela troca de extensão ou por uma reconstrução improvisada.

Os auxiliares locais precisam de Python 3.9 ou superior e não usam rede nem dependências adicionais. Eles iniciam o projeto, calculam contraste, inventariam arquivos e geram uma apresentação HTML para avaliação. O agente pode executá-los por você.

O exemplo em `examples/review.json` é fictício e não é uma identidade pronta. Nenhum ativo de cliente ou credencial acompanha a skill. Não publique exemplos como se fossem entregas aprovadas.
