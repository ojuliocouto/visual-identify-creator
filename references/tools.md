# Comandos e formatos

Os dois scripts usam apenas a biblioteca padrão de Python 3.9 ou superior. Não instalam pacotes, não usam rede e não exigem chaves. O agente resolve `SKILL_DIR` para a pasta que contém `SKILL.md`; o usuário não precisa saber Python para pedir o trabalho.

## brand_tools.py

### Inicializar

```bash
python3 "$SKILL_DIR/scripts/brand_tools.py" init --project "$PROJETO_DIR" --name "Minha marca" --mode new
```

Modos: `new`, `refresh`, `applications`. Cria sete pastas e `project.json` em briefing/rascunho, com listas vazias de fontes, aprovações, entregáveis e perguntas. Se já houver `project.json`, recusa sem sobrescrever. Diretórios novos podem permanecer se ocorrer falha de escrita; confira antes de repetir.

O comando inicializa organização, não coleta briefing nem aprova nada. O agente preenche o estado com informações reais e cria o histórico de aprovação conforme `delivery.md`.

### Contraste

```bash
python3 "$SKILL_DIR/scripts/brand_tools.py" contrast --foreground '#17252A' --background '#FFFFFF'
```

Aceita `#RGB` ou `#RRGGBB`, sem alpha. Saída JSON: `foreground`, `background`, `ratio`, `thresholds`, `pass` e `limitations`. `pass` possui `normal_text`, `large_text` e `non_text`, mas cada critério exige classificação correta do uso. Decisões usam valor não arredondado.

### Inventário técnico

```bash
python3 "$SKILL_DIR/scripts/brand_tools.py" audit "$PROJETO_DIR/approved"
```

Aceita um arquivo ou pasta explícita. Retorna JSON com `files`, `issues`, `limitations`. Cada arquivo contém caminho relativo, formato, tamanho, hash e dimensões quando interpretadas. SVG tem contagens de fontes, texto, referências, conteúdo ativo e flag de raster embutido; valores de texto e URLs não são exportados.

PNG recebe inspeção do cabeçalho, não decodificação completa. SVG não é executado, renderizado ou sanitizado. JPEG, PDF, AI e EPS são desconhecidos para este inventário: recebem tamanho/hash, não validação do formato. Isso difere do gerador HTML, que inspeciona contêineres PNG/JPEG/WebP para incorporá-los.

Limites: 16 MiB por arquivo, 256 MiB de leitura total, 10 mil entradas, profundidade de diretório 64. Links simbólicos são ignorados; symlink como entrada é recusado. Não aponte para pastas amplas com conteúdo privado.

Saída 0: operação concluída, podendo haver avisos. Saída 2: argumento inválido, falha de leitura, limite ou problema técnico grave. Nenhum código de saída certifica qualidade visual.

## build_review.py

```bash
python3 "$SKILL_DIR/scripts/build_review.py" --input "$PROJETO_DIR/review.json" --output "$PROJETO_DIR/manual/avaliacao.html"
```

Use `examples/review.json` como exemplo de estrutura e substitua o conteúdo fictício. A pasta de saída precisa existir. O script recusa sobrescrita por padrão; `--force` substitui apenas o HTML explicitamente escolhido, nunca insumos ou template.

Todos os campos de primeiro nível são obrigatórios:

| Campo | Tipo e finalidade |
| --- | --- |
| `brand`, `title`, `summary`, `stage`, `status` | Strings não vazias; status não é inferido |
| `directions` | 1 a 8 objetos com `id`, `title`, `rationale`, `keeps`, `changes`, `risks`; `image` opcional |
| `palette` | Lista de objetos com `name`, `hex` no formato `#RRGGBB`, `role` |
| `typography` | Lista de objetos com `family`, `role`, `license` |
| `applications` | Lista de objetos com `title`, `description`; `image` opcional |
| `decisions`, `limitations` | Listas de strings |

`keeps`, `changes` e `risks` também são listas de strings. Campos desconhecidos, chaves duplicadas e tipos incorretos são recusados. Listas podem estar vazias, exceto `directions`. Para apresentar uma identidade já escolhida, use uma única direção com o estado real.

Imagens precisam estar dentro da pasta do JSON ou subpastas, com caminho relativo. Formatos permitidos: PNG, JPEG e WebP estáticos. Limites: 10 MiB por imagem, 30 MiB somados e 80 milhões de pixels. URL, caminho absoluto, travessia de pasta, SVG e symlink que escape da pasta são recusados. Imagem ausente gera área “não validada” e aviso, não arte inventada.

Os bitmaps são incorporados no HTML, que abre sem CDN ou fontes externas. Tipografia indicada é documentação, não carregamento automático da família. Exporte pranchas tipográficas verificadas se quiser mostrar o desenho exato das fontes.

O gerador não decodifica todos os pixels, não aprova a apresentação e não checa direitos dos arquivos. Inspecione a página no navegador em desktop e mobile. O template traz movimento discreto, redução de movimento e regras de impressão, não exportação PDF automática.

## Testes

```bash
python3 -m unittest discover -s "$SKILL_DIR/tests" -v
```

Os testes usam dados sintéticos em diretórios temporários. Eles cobrem operações técnicas e falhas conhecidas, não a qualidade de um design ou roteamento real do assistente. Não consomem créditos nem acessam contas.
