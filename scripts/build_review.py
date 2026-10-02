#!/usr/bin/env python3
"""Build an offline review presentation from validated JSON using only stdlib.

Text is rendered only into escaped HTML text/attributes. There is no JavaScript
and no font loading. The sole data-driven CSS value is a validated #RRGGBB color.
Image container checks are not a full pixel decode or visual quality assurance.
"""

import argparse
import base64
import html
import json
import os
import re
import stat
import struct
import sys
import tempfile
import zlib
from pathlib import Path, PurePosixPath
from string import Template


MAX_JSON = 2 * 1024 * 1024
MAX_IMAGE = 10 * 1024 * 1024
MAX_TOTAL_IMAGES = 30 * 1024 * 1024
MAX_PIXELS = 80_000_000
TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "review-template.html"
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


class ReviewError(ValueError):
    """An input cannot be safely rendered."""


def string(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ReviewError(f"{field}: esperado texto não vazio")
    if len(value) > 20_000 or any(ord(char) < 32 and char not in "\n\r\t" for char in value):
        raise ReviewError(f"{field}: texto muito longo ou com caracteres de controle")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ReviewError(f"{field}: texto Unicode inválido") from error


def obj(value, field, required, optional=()):
    if not isinstance(value, dict):
        raise ReviewError(f"{field}: esperado objeto JSON")
    missing = set(required) - value.keys()
    unknown = value.keys() - set(required) - set(optional)
    if missing:
        raise ReviewError(f"{field}: campos obrigatórios ausentes: {', '.join(sorted(missing))}")
    if unknown:
        raise ReviewError(f"{field}: campos desconhecidos: {', '.join(sorted(unknown))}")


def array(value, field, limit=64, minimum=0):
    if not isinstance(value, list) or not minimum <= len(value) <= limit:
        raise ReviewError(f"{field}: esperado array com {minimum} a {limit} itens")


def strings(value, field):
    array(value, field)
    for index, entry in enumerate(value):
        string(entry, f"{field}[{index}]")


def validate(data):
    obj(data, "review", ("brand", "title", "summary", "stage", "status", "directions", "palette", "typography", "applications", "decisions", "limitations"))
    for key in ("brand", "title", "summary", "stage", "status"):
        string(data[key], key)
    array(data["directions"], "directions", 8, 1)
    ids = set()
    for index, direction in enumerate(data["directions"]):
        field = f"directions[{index}]"
        obj(direction, field, ("id", "title", "rationale", "keeps", "changes", "risks"), ("image",))
        for key in ("id", "title", "rationale"):
            string(direction[key], f"{field}.{key}")
        if direction["id"] in ids:
            raise ReviewError(f"{field}.id: identificador duplicado em directions")
        ids.add(direction["id"])
        for key in ("keeps", "changes", "risks"):
            strings(direction[key], f"{field}.{key}")
        if "image" in direction:
            string(direction["image"], f"{field}.image")
    array(data["palette"], "palette", 32)
    for index, color in enumerate(data["palette"]):
        field = f"palette[{index}]"
        obj(color, field, ("name", "hex", "role"))
        for key in ("name", "hex", "role"):
            string(color[key], f"{field}.{key}")
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color["hex"]):
            raise ReviewError(f"{field}.hex: use exatamente #RRGGBB")
    array(data["typography"], "typography", 20)
    for index, item in enumerate(data["typography"]):
        field = f"typography[{index}]"
        obj(item, field, ("family", "role", "license"))
        for key in ("family", "role", "license"):
            string(item[key], f"{field}.{key}")
    array(data["applications"], "applications", 24)
    for index, item in enumerate(data["applications"]):
        field = f"applications[{index}]"
        obj(item, field, ("title", "description"), ("image",))
        for key in ("title", "description"):
            string(item[key], f"{field}.{key}")
        if "image" in item:
            string(item["image"], f"{field}.image")
    for key in ("decisions", "limitations"):
        strings(data[key], key)


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReviewError(f"chave JSON duplicada: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ReviewError(f"constante JSON inválida: {value}")


def load_json(path):
    if not path.is_file():
        raise ReviewError("--input deve apontar para um arquivo JSON regular")
    with path.open("rb") as handle:
        raw = handle.read(MAX_JSON + 1)
    if len(raw) > MAX_JSON:
        raise ReviewError("JSON excede o limite de 2 MiB")
    try:
        data = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=no_duplicate_keys, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ReviewError(f"JSON inválido: {error}") from error
    validate(data)
    return data


def dimensions(width, height):
    if not width or not height or width * height > MAX_PIXELS:
        raise ReviewError("imagem: dimensões inválidas ou superiores a 80 milhões de pixels")


def png_dimensions(data):
    offset, size, idat, result = 8, len(data), False, None
    while offset + 12 <= size:
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > size:
            break
        payload = data[offset + 8:end - 4]
        if zlib.crc32(kind + payload) != struct.unpack_from(">I", data, end - 4)[0]:
            raise ReviewError("imagem PNG: checksum inválido")
        if result is None:
            if kind != b"IHDR" or length != 13:
                break
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            permitted = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
            if depth not in permitted.get(color, ()) or compression or filtering or interlace not in (0, 1):
                break
            result = (width, height)
        elif kind == b"IHDR":
            break
        if kind == b"acTL":
            raise ReviewError("imagem: PNG animado não é aceito; forneça uma prancha estática")
        if kind == b"IDAT" and payload:
            idat = True
        if kind == b"IEND":
            if length == 0 and end == size and idat and result:
                return result
            break
        offset = end
    raise ReviewError("imagem PNG incompleta ou com estrutura inválida")


def jpeg_dimensions(data):
    if not data.endswith(b"\xff\xd9"):
        raise ReviewError("imagem JPEG incompleta")
    offset, result = 2, None
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            break
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in (0x01, *range(0xD0, 0xDA)):
            break
        if offset + 2 > len(data):
            break
        length = struct.unpack_from(">H", data, offset)[0]
        end = offset + length
        if length < 2 or end > len(data):
            break
        if marker in sof:
            if length < 8:
                break
            height, width = struct.unpack_from(">HH", data, offset + 3)
            result = (width, height)
        if marker == 0xDA:
            if result and length >= 6 and end < len(data) - 2:
                return result
            break
        offset = end
    raise ReviewError("imagem JPEG sem cabeçalho e dados válidos")


def webp_dimensions(data):
    if len(data) < 20 or struct.unpack_from("<I", data, 4)[0] + 8 != len(data):
        raise ReviewError("imagem WebP incompleta ou com tamanho inválido")
    offset, result, canvas = 12, None, None
    while offset + 8 <= len(data):
        kind = data[offset:offset + 4]
        length = struct.unpack_from("<I", data, offset + 4)[0]
        end = offset + 8 + length
        if end > len(data):
            break
        payload = data[offset + 8:end]
        if kind in (b"ANIM", b"ANMF"):
            raise ReviewError("imagem: WebP animado não é aceito; forneça uma prancha estática")
        if kind == b"VP8X":
            if length != 10 or payload[0] & 0x02:
                break
            canvas = (int.from_bytes(payload[4:7], "little") + 1, int.from_bytes(payload[7:10], "little") + 1)
        elif kind == b"VP8 ":
            if length < 10 or payload[3:6] != b"\x9d\x01\x2a":
                break
            width, height = struct.unpack_from("<HH", payload, 6)
            result = (width & 0x3FFF, height & 0x3FFF)
        elif kind == b"VP8L":
            if length < 6 or payload[0] != 0x2F:
                break
            bits = int.from_bytes(payload[1:5], "little")
            result = ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
        offset = end + (length % 2)
        if offset == len(data) and result and (canvas is None or canvas == result):
            return result
    raise ReviewError("imagem WebP sem estrutura estática válida")


def inspect_image(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime, size = "image/png", png_dimensions(data)
    elif data.startswith(b"\xff\xd8\xff"):
        mime, size = "image/jpeg", jpeg_dimensions(data)
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        mime, size = "image/webp", webp_dimensions(data)
    else:
        raise ReviewError("imagem: conteúdo não corresponde a PNG, JPEG ou WebP")
    dimensions(*size)
    return mime, size


def prepare_images(data, base):
    images, protected_paths, warnings, total = {}, set(), [], 0
    for section in ("directions", "applications"):
        for index, item in enumerate(data[section]):
            field = f"{section}[{index}].image"
            name = item.get("image")
            if name is None:
                continue
            relative = PurePosixPath(name)
            if (relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name or "\x00" in name or any(ord(char) < 32 for char in name)):
                raise ReviewError(f"{field}: use um caminho relativo local seguro, sem URL ou travessia")
            path = (base / name).resolve()
            if not path.is_relative_to(base):
                raise ReviewError(f"{field}: caminho ou symlink fora da pasta do JSON")
            protected_paths.add(path)
            expected_mime = IMAGE_TYPES.get(path.suffix.lower())
            if expected_mime is None or relative.suffix.lower() not in IMAGE_TYPES:
                raise ReviewError(f"{field}: imagem deve ser PNG, JPEG ou WebP; SVG não é aceito")
            if not path.exists():
                warnings.append(f"{field}: imagem não encontrada; prancha NÃO VALIDADA")
                images[field] = None
                continue
            if not path.is_file():
                raise ReviewError(f"{field}: imagem precisa ser um arquivo regular")
            with path.open("rb") as handle:
                if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                    raise ReviewError(f"{field}: imagem precisa ser um arquivo regular")
                raw = handle.read(MAX_IMAGE + 1)
            if len(raw) > MAX_IMAGE:
                raise ReviewError(f"{field}: imagem excede 10 MiB")
            total += len(raw)
            if total > MAX_TOTAL_IMAGES:
                raise ReviewError("imagens excedem o limite total de 30 MiB")
            mime, size = inspect_image(raw)
            if mime != expected_mime or mime != IMAGE_TYPES[relative.suffix.lower()]:
                raise ReviewError(f"{field}: extensão da imagem não corresponde ao conteúdo")
            images[field] = ("data:" + mime + ";base64," + base64.b64encode(raw).decode("ascii"), size)
    return images, protected_paths, warnings


def esc(value):
    return html.escape(value, quote=True)


def list_html(items, empty="Não informado. Não interpretar como ausência de risco."):
    if not items:
        return '<p class="empty">' + esc(empty) + "</p>"
    return "<ul>" + "".join("<li>" + esc(item) + "</li>" for item in items) + "</ul>"


def board(item, field, images):
    image = images.get(field)
    if image:
        source, (width, height) = image
        return (f'<figure class="board"><div class="board-surface"><img src="{source}" '
                f'width="{width}" height="{height}" alt="{esc(item["title"])}" loading="lazy"></div>'
                '<figcaption>Imagem fornecida · QA visual pendente</figcaption></figure>')
    reason = "Imagem não encontrada" if item.get("image") else "Sem imagem fornecida"
    return ('<figure class="board"><div class="board-surface placeholder"><span class="placeholder-mark" aria-hidden="true">+</span>'
            f'<strong>{reason}</strong><span>Nenhuma arte foi inventada</span></div>'
            '<figcaption>NÃO VALIDADA · Espaço de estrutura, não é peça final</figcaption></figure>')


def render(data, images):
    directions = []
    for index, item in enumerate(data["directions"]):
        comparison = "".join(f'<div><h4>{label}</h4>{list_html(item[key])}</div>' for key, label in (("keeps", "Mantém"), ("changes", "Altera"), ("risks", "Riscos e pontos a testar")))
        directions.append(
            f'<article class="direction"><div class="direction-heading"><span class="index">{esc(item["id"])}</span>'
            f'<h3>{esc(item["title"])}</h3></div>{board(item, f"directions[{index}].image", images)}'
            f'<p class="rationale">{esc(item["rationale"])}</p><div class="comparison">{comparison}</div></article>'
        )
    palette = "".join(
        f'<article class="swatch"><div class="color" style="background-color:{item["hex"]}" aria-hidden="true"></div>'
        f'<div class="swatch-info"><h3>{esc(item["name"])}</h3><code>{item["hex"].upper()}</code><p>{esc(item["role"])}</p></div></article>'
        for item in data["palette"]
    )
    typography = "".join(
        f'<article class="type-row"><span class="type-number">{index + 1:02}</span><div><h3>{esc(item["family"])}</h3>'
        f'<p>{esc(item["role"])}</p></div><div class="type-license"><span class="label">Licença informada</span><p>{esc(item["license"])}</p></div></article>'
        for index, item in enumerate(data["typography"])
    )
    applications = "".join(
        f'<article class="application">{board(item, f"applications[{index}].image", images)}<h3>{esc(item["title"])}</h3><p>{esc(item["description"])}</p></article>'
        for index, item in enumerate(data["applications"])
    )
    replacements = {key: esc(data[key]) for key in ("brand", "title", "summary", "stage", "status")}
    replacements.update(
        directions="\n".join(directions), direction_count=f'{len(directions):02}',
        palette=palette or '<p class="empty">Paleta não fornecida. Não validada.</p>',
        typography=typography or '<p class="empty">Tipografia não fornecida. Não validada.</p>',
        applications=applications or '<p class="empty">Nenhuma aplicação fornecida. Não validada.</p>',
        decisions=list_html(data["decisions"], "Decisões não registradas. Aprovação não inferida."),
        limitations=list_html(data["limitations"], "Limitações não informadas. Isso não comprova ausência de limitações."),
    )
    return Template(TEMPLATE.read_text(encoding="utf-8")).substitute(replacements)


def write_output(output, document, force, protected_paths):
    if output.is_symlink():
        raise ReviewError("--output não pode ser um symlink")
    resolved = output.resolve()
    if resolved in protected_paths:
        raise ReviewError("--output não pode sobrescrever o JSON, uma imagem de entrada ou o template")
    if not output.parent.is_dir():
        raise ReviewError("a pasta de --output precisa existir")
    if output.exists() and not force:
        raise ReviewError("--output já existe; use --force somente para substituí-lo explicitamente")
    # Build and validate everything before opening any output. An exclusive open
    # protects the no-overwrite default; force uses an atomic sibling replacement.
    if not force:
        try:
            with output.open("x", encoding="utf-8") as handle:
                handle.write(document)
        except FileExistsError as error:
            raise ReviewError("--output já existe; use --force para substituir") from error
    else:
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent, prefix=".review-", suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(document)
            os.replace(temporary, output)
            temporary = None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Gera apresentação HTML local de proposta. Não realiza aprovação nem QA visual.")
    parser.add_argument("--input", required=True, type=Path, help="JSON UTF-8; imagens relativas à pasta deste arquivo")
    parser.add_argument("--output", required=True, type=Path, help="HTML de destino em pasta existente")
    parser.add_argument("--force", action="store_true", help="Substitui somente o HTML de destino, após validação completa")
    args = parser.parse_args(argv)
    try:
        source = args.input.resolve()
        data = load_json(source)
        images, protected_paths, warnings = prepare_images(data, source.parent)
        document = render(data, images)
        write_output(args.output, document, args.force, protected_paths | {source, TEMPLATE.resolve()})
    except (ReviewError, OSError, ValueError, RuntimeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2
    for warning in warnings:
        print(f"Aviso: {warning}", file=sys.stderr)
    print(f"HTML gerado: {args.output.absolute()}")
    print("Renderização não comprova QA visual. Proposta sem aprovação inferida.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
