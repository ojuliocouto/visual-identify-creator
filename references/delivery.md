# Aprovação, manual e entrega

## Estado de projeto

`project.json` resume modo, estágio, status, fontes, perguntas abertas e entregáveis. Acrescente briefing e restrições depois de coletados. Não apague histórico para trocar uma proposta.

`approval-log.jsonl` é um registro de eventos, não um documento que se reescreve. Cada linha segue este formato; o exemplo é fictício e não é uma aprovação utilizável:

```json
{"event":"direction_selected","stage":"concepts","version":"v02","artifacts":["directions/v02/opcao-b.svg"],"approver":"Pessoa responsável","evidence":"Gostei da B, refine o espaçamento","source":"mensagem do usuário","recorded_at":"DATA_REAL_ISO_8601","scope":"refinar direção B","publication_authorized":false}
```

Eventos úteis: `brief_confirmed`, `direction_selected`, `revision_requested`, `identity_approved`, `application_approved`, `publication_authorized`, `publication_verified`. Escolha não é aprovação final. Autorização de publicação precisa de destino, escopo e evidência explícita. Se a autorização abranger várias etapas claramente, registre esse alcance, sem criar perguntas artificiais.

Para comparar o ativo sem ambiguidade, registre caminho relativo e hash quando possível. Uma alteração posterior gera nova versão e invalida somente aprovações que dependiam do conteúdo alterado, com explicação.

## Estrutura de trabalho

```text
projeto/
  project.json
  approval-log.jsonl
  sources/
  directions/
  approved/
  applications/
  manual/
  delivery/
  evidence/
```

Os diretórios são categorias, não exigência de preencher todos. Fontes privadas e histórico interno ficam fora do pacote do cliente. Não inclua `project.json` integral se contiver informação privada desnecessária.

## Manual visual

Escolha uma narrativa curta que explique o que mudou e como usar. Mínimo conforme escopo:

1. Contexto e objetivo da mudança, sem promessas inventadas.
2. Antes e depois para modernizações, com elementos preservados destacados.
3. Conceito e construção, apenas quando a explicação for verdadeira.
4. Assinaturas, cores, monocromia, reversa, margens e redução.
5. Tipografia, hierarquia e condições de licença.
6. Paleta e exemplos de combinações corretas, inclusive texto.
7. Grafismos, imagens, composição e arquitetura dos produtos quando aplicável.
8. Aplicações reais, variações e erros a evitar demonstrados visualmente.
9. Índice dos arquivos e instruções de uso.
10. Status, versão, aprovação e pendências relevantes.

Não diga que um símbolo vem de uma construção geométrica se ele não foi desenhado assim. Diagramas de construção inventados são decoração enganosa.

Faça o manual ter direção editorial: contraste de escala, espaços consistentes, pranchas com uma ideia por seção e legendas objetivas. Animação deve facilitar orientação, nunca esconder texto, atrasar leitura ou impossibilitar impressão.

O template incluído organiza uma avaliação. Para um manual final, inclua as regras, ativos e aplicações aprovadas; remova espaços vazios e rotule testes incompletos. Gerar HTML não significa publicar uma página.

## Pacote de arquivos

Combine os formatos com o uso. Exemplo:

- Mestre editável no formato realmente produzido.
- SVG final com curvas quando disponível e verificado.
- PNG transparente e versões para fundo claro/escuro em tamanhos úteis.
- PDF vetorial quando exportação real e compatibilidade forem verificadas.
- Manual HTML e/ou PDF.
- `LEIA-ME.md`: qual variante usar, licença, limitações e data/versão.

Nunca invente AI, EPS ou PDF apenas mudando extensão. Não inclua variações sem função nem todo histórico de rascunhos. Arquivo de fonte só acompanha se redistribuição for permitida; caso contrário, inclua link oficial e orientação de aquisição.

## Entrega externa

Enviar por WhatsApp, publicar em domínio ou modificar checkout são ações separadas. Confirme canal, destinatário/destino e versão autorizada. Não reutilize número, instância, token ou endereço de cliente anterior.

Para página publicada, verifique HTTPS, acesso sem sessão, título, descrição, favicon, Open Graph e imagem social realmente acessível. Preview pode ser cacheado pelo canal; teste no canal quando autorizado e não garanta preview só por presença das tags.

Mensagem final objetiva: entregáveis, links, o que foi testado, o que continua pendente e próxima decisão. Não exponha credenciais, caminhos internos sensíveis ou informações do aluno a terceiros.
