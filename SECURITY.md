# Segurança e escopo dos dados

## Conteúdo distribuído

Este repositório distribui a skill, referências de uso, dois scripts auxiliares, template HTML, um exemplo fictício e testes sintéticos. Projetos reais, relatórios operacionais locais, caches, arquivos de ambiente, chaves e histórico de conversas não fazem parte da distribuição.

Fixtures de teste incluem bitmaps mínimos e entradas propositalmente inválidas para verificar rejeição de conteúdo ativo, referências externas e travessia de pastas. Não são fotos de clientes ou payloads executados pelo aplicativo. Domínios em testes servem apenas como entradas sintéticas; os testes não fazem requisições de rede.

## Execução

- Os auxiliares usam somente a biblioteca padrão de Python e arquivos locais escolhidos pelo usuário.
- O inventário não executa SVG nem resolve referências externas. Seus alertas não são certificado de segurança ou qualidade visual.
- O gerador HTML valida estrutura e incorpora somente imagens locais admitidas, sem JavaScript, fontes externas ou CDN.
- Os testes executam os scripts locais com argumentos em lista e trabalham com diretórios temporários.
- A etapa de geração de imagens é distinta: usa o motor nativo do Codex e processa as referências enviadas a essa ferramenta. Não equivale a processamento totalmente offline.

Não use a skill para transmitir credenciais ou dados sensíveis. Antes de entregar um pacote de marca ou publicar uma apresentação, revise também os insumos e saídas do projeto específico. Uma distribuição sem dados privados não impede que o usuário acrescente dados privados depois.

## Limites da revisão

Busca por padrões, testes e revisão manual reduzem riscos, mas não garantem ausência absoluta de vulnerabilidades ou dados sensíveis. Para comunicar um problema, não exponha segredos em issues públicas. Se houver vazamento real, revogue primeiro a credencial afetada e reporte apenas os detalhes mínimos necessários.
