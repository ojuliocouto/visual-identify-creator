# QA técnico e visual

## Cinco estados diferentes

Produzido significa arquivo existente. Verificado tecnicamente significa checks executados. Revisado visualmente significa arte inspecionada. Aprovado significa resposta do aprovador sobre aquela versão. Publicado significa destino real verificado. Nenhum estado implica automaticamente o próximo.

## Checklist por tipo

| Tipo | Verificação técnica | Inspeção visual |
| --- | --- | --- |
| Logo | Formato, viewBox, raster embutido, fontes, referências | Leitura, forma, peso, curvas, espaçamento, redução e reversa |
| Banner | Dimensões, peso, formato, transparência | Safe area, títulos, margens, encontros entre blocos, desktop/mobile |
| Capa de produto | Família visual e nome literal | Distinção entre produtos, miniatura e arte completa |
| HTML | Abre sem recursos quebrados, responsividade, metadados | Hierarquia, recortes, texto, movimento, navegação e mobile |
| PDF | Abre, páginas, fontes, links quando necessários | Quebras, cortes, margens, contraste e tamanho de leitura |
| Pacote | Nomes, hashes, arquivo abre, nenhuma credencial | Guia corresponde às variantes realmente entregues |

Inspecione o arquivo final exportado. Uma tela de edição correta não prova exportação correta. Se mudar o mestre após exportação, exporte e confira novamente as dependências afetadas.

## Contraste

O helper usa luminância relativa sRGB e `(L_clara + 0.05) / (L_escura + 0.05)`. As decisões usam o valor sem arredondamento. No WCAG AA, texto normal exige 4,5:1; texto grande exige 3:1. “Grande” equivale a pelo menos 18 pt, ou 14 pt em negrito, não simplesmente uma tag de título. Elementos de interface relevantes podem exigir 3:1 conforme o critério aplicável.

Logotipos têm exceção no requisito de contraste de texto, mas ainda precisam ser legíveis no uso previsto. Não use essa exceção para títulos, preços, CTAs ou conteúdo do manual. Transparência, gradientes e fotografias exigem medir o fundo efetivo ou testar os piores pontos. O helper de cores sólidas não verifica esses casos.

Referência: [W3C, Understanding Contrast Minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). Consulte a versão atual ao fazer declarações de conformidade. Um cálculo não prova acessibilidade da página inteira.

## SVG e limites do inventário

O inventário examina estrutura, não renderiza nem executa SVG. Alertas sobre texto, raster, referências externas e conteúdo ativo indicam revisão necessária. Mesmo sem alerta, não chame o arquivo de seguro, visualmente correto, totalmente vetorial ou compatível com toda plataforma.

Não abra conteúdo ativo suspeito em navegador autenticado. Rejeite DOCTYPE, entidades, scripts e recursos externos inesperados. Não baixe dependências automaticamente. Para conteúdo confiável, renderize em ambiente apropriado e confira contra o mestre.

Referências: [especificação SVG](https://www.w3.org/TR/SVG2/) e [limitações de segurança do XML em Python](https://docs.python.org/3/library/xml.html#xml-vulnerabilities).

## Evidências mínimas

Registre por entregável: arquivo e versão, ferramenta ou comando, resultado, data real, captura ou observação visual e limitações. Para check não executado, escreva “não testado”. Não preencha um checklist como concluído para deixar o documento bonito.

Antes de dizer “pronto”, responda:

- O usuário consegue abrir e usar os arquivos?
- As regras do manual estão demonstradas e são consistentes com o mestre?
- Há alguma fonte ou imagem sem direito de distribuição confirmado?
- O responsável aprovou estas peças ou apenas o conceito?
- Há ajuste de checkout, envio ou publicação ainda sem autorização?

## Critérios de aceitação humana

1. Reconhecimento: os traços protegidos estão preservados ou as mudanças foram aprovadas.
2. Diferenciação: há vínculo específico com a marca, não só símbolo setorial genérico.
3. Qualidade formal: curvas, ritmo, peso e tipografia funcionam sem mockup.
4. Uso: marca e sistema funcionam nas aplicações acordadas.
5. Clareza: manual permite a outra pessoa produzir peças consistentes.

Não gere uma nota automática de beleza. Se o aprovador rejeitar a estética, o teste técnico não encerra a discussão.
