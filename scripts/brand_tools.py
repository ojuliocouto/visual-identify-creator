#!/usr/bin/env python3
"""Offline identity-project helpers. Python 3.9+, standard library only.

This inventories local structure; it does not render artwork, sanitize SVG,
verify ownership, certify accessibility, or approve a deliverable.
"""

import argparse
import hashlib
import json
import math
import os
import re
import stat
import struct
import sys
import zlib
from pathlib import Path
from xml.parsers import expat


MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
MAX_ENTRIES = 10000
MAX_DIRECTORY_DEPTH = 64
MAX_XML_DEPTH = 128
MAX_XML_ELEMENTS = 100000
PROJECT_DIRECTORIES = (
    "sources", "directions", "approved", "applications", "manual", "delivery", "evidence"
)
CSS_VALUE_ATTRIBUTES = {
    "style", "fill", "stroke", "filter", "clip-path", "mask", "marker",
    "marker-start", "marker-mid", "marker-end", "cursor", "color-profile",
    "background", "background-image", "shape-inside", "shape-outside", "offset-path",
}
AUDIT_LIMITATIONS = [
    "Inventário estrutural local: não renderiza, não aprova visualmente e não certifica um SVG como seguro ou vetor final.",
    "PNG: somente assinatura e IHDR são inspecionados; o bitmap completo não é decodificado.",
    "SVG: XML limitado; DOCTYPE e entidades são rejeitados, e referências nunca são resolvidas ou executadas.",
    "A detecção de CSS, fontes e conteúdo ativo é conservadora, não é um sanitizador nem uma análise completa de navegador.",
    "Textos, fontes, URLs, metadados autorais e conteúdo dos arquivos não são exportados; nomes relativos dos arquivos permanecem no relatório.",
    "Arquivos desconhecidos, inclusive JPEG, PDF, AI e EPS, recebem hash quando cabem no limite, mas não são interpretados.",
    "Links simbólicos são ignorados. Limites: 16 MiB por arquivo, 256 MiB de leitura total, 10000 entradas e profundidade de pasta 64.",
    "O resultado não verifica licenças, originalidade, legibilidade, contraste de uma aplicação real, perfis de cor ou qualidade de impressão.",
]


class ToolError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


class JSONArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # Do not echo arbitrary command-line values or private paths.
        raise ToolError("invalid_arguments", "Argumentos inválidos ou incompletos. Consulte o comando com --help.")


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))


def contrast(foreground, background):
    def parse_color(value):
        if not re.fullmatch(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?", value):
            raise ToolError("invalid_color", "Use cor opaca em #RGB ou #RRGGBB; alpha, nomes e gradientes não são aceitos.")
        digits = value[1:]
        if len(digits) == 3:
            digits = "".join(character * 2 for character in digits)
        components = [int(digits[index:index + 2], 16) / 255 for index in (0, 2, 4)]
        linear = [component / 12.92 if component <= 0.04045 else ((component + 0.055) / 1.055) ** 2.4 for component in components]
        return "#" + digits.upper(), sum(component * weight for component, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    fg, fg_luminance = parse_color(foreground)
    bg, bg_luminance = parse_color(background)
    ratio = (max(fg_luminance, bg_luminance) + 0.05) / (min(fg_luminance, bg_luminance) + 0.05)
    thresholds = {"normal_text": 4.5, "large_text": 3.0, "non_text": 3.0}
    return {
        "foreground": fg,
        "background": bg,
        "ratio": ratio,
        "thresholds": thresholds,
        "pass": {name: ratio >= threshold for name, threshold in thresholds.items()},
        "limitations": [
            "Cálculo sRGB WCAG para duas cores opacas uniformes, sem arredondamento antes de comparar limites.",
            "Texto grande: ao menos 18 pt regular ou 14 pt em negrito; confirme o tamanho na aplicação real.",
            "O limite não textual depende do papel do componente e das cores adjacentes; não se aplica indistintamente a toda arte.",
            "Texto integrante de logo ou nome de marca é isento do requisito de contraste de texto WCAG; esta medição não aprova nem reprova um logo.",
            "Não avalia transparência, fotos, gradientes, antialiasing, tamanho visual, estados interativos ou acessibilidade completa.",
        ],
    }


def add_issue(result, path, code, severity, message):
    result["issues"].append({"path": path, "code": code, "severity": severity, "message": message})


def local_name(value):
    return value.rsplit("}", 1)[-1].lower()


def css_plain(value):
    def unescape(match):
        digits = match.group(1)
        if digits:
            number = int(digits, 16)
            return chr(number) if 0 < number <= 0x10FFFF else "\ufffd"
        return match.group(2) or ""

    # Advance past each comment once. A repeated unclosed comment must not
    # provoke quadratic regex scanning over an untrusted style block.
    chunks = []
    position = 0
    while True:
        start = value.find("/*", position)
        if start == -1:
            chunks.append(value[position:])
            break
        end = value.find("*/", start + 2)
        if end == -1:
            raise ToolError("css_unparsed", "Comentário CSS não terminado; revisão manual necessária.")
        chunks.append(value[position:start])
        position = end + 2
    value = "".join(chunks)
    return re.sub(r"\\([0-9a-fA-F]{1,6})(?:\r\n|[\t\n\r\f ])?|\\([^\n\r\f])|\\\r?\n", unescape, value)


def inspect_svg(data, record, result):
    path = record["path"]
    record.update({
        "viewBox": None, "raster_embedded": False, "text_elements": 0,
        "font_references": 0, "external_references": 0, "scripts": 0,
        "event_handlers": 0, "foreign_objects": 0,
    })
    state = {"depth": 0, "elements": 0, "styles": [], "root": False}

    def reference(value):
        value = value.strip().strip('"\'').strip()
        if not value or value.startswith("#"):
            return
        if re.match(r"data:image/(?:png|jpe?g|gif|webp|avif|bmp|tiff?|x-icon)(?:;|,)", value, flags=re.I):
            record["raster_embedded"] = True
        else:
            # Includes remote, relative, absolute, javascript:, file:, and
            # uninspected data: documents, without resolving or exposing them.
            record["external_references"] += 1

    def inspect_css(value):
        value = css_plain(value)
        record["font_references"] += len(re.findall(r"(?:\bfont(?:-family)?\s*:|@font-face\b)", value, flags=re.I))
        position = 0
        url_start = re.compile(r"\burl\s*\(", flags=re.I)
        while True:
            match = url_start.search(value, position)
            if match is None:
                break
            end = value.find(")", match.end())
            if end == -1:
                raise ToolError("css_unparsed", "Função url CSS não terminada; revisão manual necessária.")
            reference(value[match.end():end])
            position = end + 1
        for match in re.finditer(r"@import\s+([\"'])(.*?)\1", value, flags=re.I | re.S):
            reference(match.group(2))

    def start_element(name, attributes):
        state["depth"] += 1
        state["elements"] += 1
        if state["depth"] > MAX_XML_DEPTH or state["elements"] > MAX_XML_ELEMENTS:
            raise ToolError("xml_limit", "SVG excede os limites de profundidade ou quantidade de elementos XML.")
        tag = local_name(name)
        if not state["root"]:
            state["root"] = True
            if name not in ("svg", "http://www.w3.org/2000/svg}svg"):
                raise ToolError("not_svg", "O elemento raiz não é SVG reconhecido.")
            dimensions = {}
            for key in ("width", "height"):
                value = attributes.get(key)
                dimensions[key] = value if value and re.fullmatch(r"[+\-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?(?:px|pt|pc|mm|cm|in|em|ex|%)?", value.strip()) else None
            record["dimensions"] = dimensions
            if "viewBox" in attributes:
                try:
                    values = [float(part) for part in re.split(r"[\s,]+", attributes["viewBox"].strip())]
                    if len(values) != 4 or not all(math.isfinite(value) for value in values) or values[2] < 0 or values[3] < 0:
                        raise ValueError
                    record["viewBox"] = values
                except ValueError:
                    add_issue(result, path, "invalid_viewbox", "warning", "viewBox ausente de números válidos; revisar geometria no editor.")
        if tag == "text":
            record["text_elements"] += 1
        elif tag == "script":
            record["scripts"] += 1
        elif tag == "foreignobject":
            record["foreign_objects"] += 1
        elif tag == "style":
            state["styles"].append({"depth": state["depth"], "parts": []})
        for key, value in attributes.items():
            attribute = local_name(key)
            if attribute.startswith("on"):
                record["event_handlers"] += 1
            if attribute == "font-family":
                record["font_references"] += 1
            if attribute in ("href", "src", "base"):
                reference(value)
            # Only style and URL-bearing presentation attributes are CSS.
            if attribute in CSS_VALUE_ATTRIBUTES:
                inspect_css(value)

    def end_element(name):
        if state["styles"] and state["styles"][-1]["depth"] == state["depth"]:
            inspect_css("".join(state["styles"].pop()["parts"]))
        state["depth"] -= 1

    def characters(value):
        if state["styles"]:
            state["styles"][-1]["parts"].append(value)

    def reject_declaration(*unused):
        raise ToolError("unsafe_xml_declaration", "DOCTYPE, declarações de entidades e entidades externas não são aceitos.")

    def processing_instruction(target, value):
        add_issue(result, path, "xml_processing_instruction", "error", "Instrução de processamento XML exige revisão; não foi executada.")

    parser = expat.ParserCreate(namespace_separator="}")
    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    parser.CharacterDataHandler = characters
    parser.StartDoctypeDeclHandler = reject_declaration
    parser.EntityDeclHandler = reject_declaration
    parser.ExternalEntityRefHandler = reject_declaration
    parser.ProcessingInstructionHandler = processing_instruction
    try:
        # Expat decodes XML before declaration callbacks, including UTF-16.
        # No DTD callback can proceed to entity expansion.
        parser.Parse(data, True)
    except ToolError as error:
        add_issue(result, path, error.code, "error", error.message)
    except (expat.ExpatError, ValueError, LookupError):
        add_issue(result, path, "malformed_svg", "error", "XML inválido ou codificação XML não suportada; nenhum conteúdo foi executado.")

    alerts = (
        ("scripts", "svg_scripts", "error", "SVG contém script; não executar nem considerar entrega final."),
        ("event_handlers", "svg_event_handlers", "error", "SVG contém atributos de evento; revisão necessária."),
        ("foreign_objects", "svg_foreign_object", "error", "SVG contém foreignObject; conteúdo incorporado requer revisão."),
        ("external_references", "svg_external_references", "error", "SVG contém referência externa ou conteúdo data não inspecionado; nada foi resolvido."),
        ("raster_embedded", "svg_raster_embedded", "warning", "SVG contém imagem raster incorporada; a extensão SVG não comprova arte vetorial."),
        ("text_elements", "svg_live_text", "warning", "SVG contém texto editável; conferir texto, fontes, licença e substituições no editor."),
        ("font_references", "svg_font_references", "warning", "SVG menciona fontes; disponibilidade e licença não foram verificadas."),
    )
    for field, code, severity, message in alerts:
        if record[field]:
            add_issue(result, path, code, severity, message)


def inspect_png(data, record, result):
    valid = len(data) >= 33 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[8:16] == b"\x00\x00\x00\rIHDR"
    if valid:
        width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", data[16:29])
        allowed_depths = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
        valid = (0 < width <= 2147483647 and 0 < height <= 2147483647
                 and bit_depth in allowed_depths.get(color_type, ())
                 and compression == 0 and filtering == 0 and interlace in (0, 1)
                 and zlib.crc32(data[12:29]) == struct.unpack(">I", data[29:33])[0])
        if valid:
            record["dimensions"] = {"width": width, "height": height, "unit": "px"}
    if not valid:
        add_issue(result, record["path"], "malformed_png", "error", "Assinatura ou cabeçalho IHDR PNG inválido ou incompleto.")


def audit(input_path):
    result = {"files": [], "issues": [], "limitations": list(AUDIT_LIMITATIONS)}
    root = Path(input_path).expanduser().absolute()
    if root.is_symlink():
        add_issue(result, root.name, "symlink_input", "error", "A entrada é um link simbólico. Informe diretamente uma pasta ou arquivo local.")
        return result
    try:
        root_stat = root.stat()
    except OSError:
        add_issue(result, ".", "input_unavailable", "error", "Entrada inexistente ou sem permissão de leitura.")
        return result
    root_is_dir = stat.S_ISDIR(root_stat.st_mode)
    if not root_is_dir and not stat.S_ISREG(root_stat.st_mode):
        add_issue(result, root.name, "unsupported_input", "error", "A entrada deve ser um arquivo regular ou pasta local.")
        return result
    boundary = root.resolve() if root_is_dir else root.parent.resolve()
    budget = {"entries": 0, "bytes": 0, "stopped": False}

    def relative(path):
        return path.relative_to(root).as_posix() if root_is_dir else path.name

    def inspect_file(path, info):
        name = relative(path)
        extension = path.suffix.lower()
        kind = {".png": "png", ".svg": "svg"}.get(extension, "unknown")
        record = {"path": name, "format": kind, "size_bytes": info.st_size, "sha256": None, "dimensions": None}
        result["files"].append(record)
        if info.st_size > MAX_FILE_BYTES:
            add_issue(result, name, "file_too_large", "error", "Arquivo excede 16 MiB; conteúdo não foi lido nem recebeu hash.")
            return
        if budget["bytes"] + info.st_size > MAX_TOTAL_BYTES:
            budget["stopped"] = True
            add_issue(result, name, "total_size_limit", "error", "Leitura total excederia 256 MiB; inventário interrompido.")
            return
        try:
            if os.path.commonpath((str(boundary), str(path.resolve()))) != str(boundary):
                raise ToolError("path_escape", "Caminho sai da entrada autorizada; leitura recusada.")
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
            descriptor = os.open(path, flags)
            with os.fdopen(descriptor, "rb") as stream:
                opened = os.fstat(stream.fileno())
                if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                    raise ToolError("file_changed", "Arquivo mudou durante o inventário; leitura recusada.")
                data = stream.read(MAX_FILE_BYTES + 1)
            if len(data) > MAX_FILE_BYTES:
                raise ToolError("file_too_large", "Arquivo excede 16 MiB; inspeção interrompida.")
            if len(data) != info.st_size:
                raise ToolError("file_changed", "Tamanho mudou durante o inventário; execute novamente com a pasta estável.")
        except ToolError as error:
            add_issue(result, name, error.code, "error", error.message)
            return
        except OSError:
            add_issue(result, name, "file_read_error", "error", "Não foi possível ler o arquivo regular local.")
            return
        budget["bytes"] += len(data)
        record["sha256"] = hashlib.sha256(data).hexdigest()
        if kind == "svg":
            inspect_svg(data, record, result)
        elif kind == "png":
            inspect_png(data, record, result)
        else:
            add_issue(result, name, "unsupported_format", "warning", "Formato não interpretado; somente tamanho e hash foram coletados.")

    def visit(path, depth):
        if budget["stopped"]:
            return
        budget["entries"] += 1
        if budget["entries"] > MAX_ENTRIES:
            budget["stopped"] = True
            add_issue(result, relative(path), "entry_limit", "error", "Limite de 10000 entradas atingido; inventário incompleto.")
            return
        try:
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                add_issue(result, relative(path), "symlink_skipped", "warning", "Link simbólico ignorado; destino não foi lido.")
            elif stat.S_ISREG(info.st_mode):
                inspect_file(path, info)
            elif stat.S_ISDIR(info.st_mode):
                if depth > MAX_DIRECTORY_DEPTH:
                    add_issue(result, relative(path), "directory_depth_limit", "error", "Pasta excede a profundidade máxima; conteúdo não foi listado.")
                    return
                # Bound directory enumeration as well as total traversal.
                children = []
                with os.scandir(path) as iterator:
                    for child in iterator:
                        children.append(path / child.name)
                        if len(children) > MAX_ENTRIES:
                            budget["stopped"] = True
                            add_issue(result, relative(path), "entry_limit", "error", "Uma pasta excede 10000 entradas; inventário interrompido.")
                            return
                for child in sorted(children, key=lambda item: item.name):
                    visit(child, depth + 1)
            else:
                add_issue(result, relative(path), "special_file_skipped", "warning", "Entrada não regular ignorada; nenhum dispositivo ou socket foi lido.")
        except OSError:
            add_issue(result, relative(path), "path_read_error", "error", "Não foi possível inspecionar esta entrada local.")

    visit(root, 0)
    return result


def init_project(project_path, name, mode):
    if not name.strip() or len(name) > 200 or any(ord(character) < 32 for character in name):
        raise ToolError("invalid_name", "Nome deve ter entre 1 e 200 caracteres, sem controles ou quebras de linha.")
    project = Path(project_path).expanduser().absolute()
    state_path = project / "project.json"
    if project.is_symlink():
        raise ToolError("symlink_project", "A pasta de projeto não pode ser um link simbólico.")
    if state_path.exists() or state_path.is_symlink():
        raise ToolError("project_exists", "project.json já existe; nada foi sobrescrito. Escolha outra pasta ou revise o projeto existente.")
    if project.exists() and not project.is_dir():
        raise ToolError("project_not_directory", "O caminho de projeto já existe e não é uma pasta.")
    for directory in PROJECT_DIRECTORIES:
        destination = project / directory
        if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
            raise ToolError("directory_conflict", "Uma pasta prevista já é arquivo ou link simbólico; inicialização recusada.")
    record = {
        "schema_version": 1, "name": name.strip(), "mode": mode,
        "stage": "briefing", "status": "draft", "approvals": [],
        "sources": [], "deliverables": [], "open_questions": [],
    }
    try:
        project.mkdir(parents=True, exist_ok=True)
        for directory in PROJECT_DIRECTORIES:
            (project / directory).mkdir(exist_ok=True)
        # Exclusive creation prevents an existing project from being overwritten,
        # including one created between the preflight checks and this write.
        with state_path.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
    except FileExistsError:
        raise ToolError("project_exists", "Arquivo ou pasta mudou durante a inicialização; nada existente foi sobrescrito.")
    except OSError:
        raise ToolError("project_write_error", "Falha ao criar projeto. Diretórios ou um arquivo parcial recém-criados podem permanecer; revise antes de repetir.")
    return {"status": "created", "project_file": "project.json", "directories": list(PROJECT_DIRECTORIES), "project": record}


def make_parser():
    parser = JSONArgumentParser(description="Helpers locais de marca. Não geram logo, não renderizam e não aprovam entregas.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    contrast_parser = subparsers.add_parser("contrast", help="Calcular contraste WCAG sRGB entre duas cores opacas.")
    contrast_parser.add_argument("--foreground", required=True, help="Cor de frente em '#RGB' ou '#RRGGBB'.")
    contrast_parser.add_argument("--background", required=True, help="Cor de fundo em '#RGB' ou '#RRGGBB'.")
    audit_parser = subparsers.add_parser("audit", help="Inventariar PNG/SVG localmente; nenhum conteúdo é executado.")
    audit_parser.add_argument("path", help="Arquivo ou pasta explícita; links simbólicos não são seguidos.")
    init_parser = subparsers.add_parser("init", help="Criar estrutura e project.json em rascunho, sem sobrescrever.")
    init_parser.add_argument("--project", required=True, help="Pasta explícita do projeto.")
    init_parser.add_argument("--name", required=True, help="Nome do projeto, até 200 caracteres.")
    init_parser.add_argument("--mode", required=True, choices=("new", "refresh", "applications"))
    return parser


def main(argv=None):
    try:
        arguments = make_parser().parse_args(argv)
        if arguments.command == "contrast":
            result = contrast(arguments.foreground, arguments.background)
        elif arguments.command == "audit":
            result = audit(arguments.path)
        else:
            result = init_project(arguments.project, arguments.name, arguments.mode)
        emit(result)
        return 2 if arguments.command == "audit" and any(issue["severity"] == "error" for issue in result["issues"]) else 0
    except ToolError as error:
        emit({"error": {"code": error.code, "message": error.message}})
        return 2


if __name__ == "__main__":
    sys.exit(main())
