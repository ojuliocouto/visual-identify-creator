"""Run with: python3 -m unittest discover -s tests -v."""

import base64
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_review.py"
def png_chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))


PNG = (
    b"\x89PNG\r\n\x1a\n"
    + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    + png_chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    + png_chunk(b"IEND", b"")
)
# Small, real, white 16 x 16 fixtures. Runtime tests need no image library.
JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAgAAAQABAAD//gAQTGF2YzYyLjI4LjEwMgD/2wBDAAgEBAQEBAUFBQUFBQYGBgYGBgYGBgYGBgYHBwcICAgHBwcGBgcHCAgICAkJCQgICAgJCQoKCgwMCwsODg4RERT/xABLAAEBAAAAAAAAAAAAAAAAAAAABwEBAAAAAAAAAAAAAAAAAAAAABABAAAAAAAAAAAAAAAAAAAAABEBAAAAAAAAAAAAAAAAAAAAAP/AABEIABAAEAMBIgACEQADEQD/2gAMAwEAAhEDEQA/AL+AD//Z"
)
WEBP = base64.b64decode("UklGRiQAAABXRUJQVlA4IBgAAAAwAQCdASoQABAAAUAmJaQAA3AA/vz0AAA=")


def valid_data():
    return {
        "brand": "Ateliê Horizonte",
        "title": "Revisão de identidade",
        "summary": "Exemplo de estrutura, não é uma identidade final.",
        "stage": "Exploração",
        "status": "Proposta sem aprovação",
        "directions": [{
            "id": "A", "title": "Clareza editorial", "rationale": "Testar hierarquia.",
            "keeps": ["Nome"], "changes": ["Ritmo"], "risks": ["Sem teste físico"],
        }],
        "palette": [{"name": "Carvão", "hex": "#202020", "role": "Texto"}],
        "typography": [{"family": "Georgia", "role": "Títulos", "license": "A verificar"}],
        "applications": [{"title": "Cartão", "description": "Sem arte disponível"}],
        "decisions": ["Escolher direção"],
        "limitations": ["Sem logo nem foto de referência"],
    }


class BuildReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.input = self.base / "review.json"
        self.output = self.base / "review.html"

    def run_cli(self, data=None, *extra):
        self.input.write_text(json.dumps(data or valid_data(), ensure_ascii=False), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--input", str(self.input), "--output", str(self.output), *extra],
            capture_output=True, text=True, check=False,
        )

    def assert_rejected(self, data, expected):
        result = self.run_cli(data)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(expected, result.stderr)
        self.assertFalse(self.output.exists())

    def test_renders_self_contained_proposal_with_explicit_placeholders(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        document = self.output.read_text(encoding="utf-8")
        self.assertIn("Ateliê Horizonte", document)
        self.assertIn("PROPOSTA PARA REVISÃO", document)
        self.assertIn("NÃO VALIDADA", document)
        self.assertIn("Renderização não comprova QA visual", document)
        self.assertIn("prefers-reduced-motion", document)
        self.assertIn("@media print", document)
        self.assertIn("Content-Security-Policy", document)
        self.assertNotIn("<script", document)
        self.assertNotIn("https://", document)

    def test_text_is_escaped_even_with_script_style_and_attribute_payloads(self):
        data = valid_data()
        payload = '</style><script>alert("x")</script><img src=x onerror="alert(1)"> & ${title}'
        for key in ("brand", "title", "summary", "stage", "status"):
            data[key] = payload
        data["directions"][0]["title"] = payload
        data["typography"][0]["family"] = payload
        data["decisions"] = [payload]
        result = self.run_cli(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        document = self.output.read_text(encoding="utf-8")
        self.assertNotIn("<script", document)
        self.assertNotIn("<img src=x", document)
        self.assertIn("&lt;script&gt;", document)
        self.assertIn("&quot;x&quot;", document)
        self.assertIn("&amp; ${title}", document)

    def test_missing_required_field_is_rejected_before_write(self):
        data = valid_data()
        del data["brand"]
        self.assert_rejected(data, "brand")

    def test_wrong_type_and_unknown_field_are_rejected(self):
        for mutate in (lambda d: d.update(directions="wrong"), lambda d: d.update(unknown="x")):
            with self.subTest(mutation=mutate):
                data = valid_data()
                mutate(data)
                self.assert_rejected(data, "Erro:")

    def test_empty_directions_and_duplicate_ids_are_rejected(self):
        for directions in ([], [valid_data()["directions"][0]] * 2):
            with self.subTest(directions=directions):
                data = valid_data()
                data["directions"] = directions
                self.assert_rejected(data, "directions")

    def test_hex_cannot_inject_css(self):
        data = valid_data()
        data["palette"][0]["hex"] = '#123456; background:url("https://example.org")'
        self.assert_rejected(data, "hex")

    def test_missing_image_is_placeholder_and_warning_not_successful_qa(self):
        data = valid_data()
        data["directions"][0]["image"] = "assets/missing.png"
        result = self.run_cli(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Aviso:", result.stderr)
        document = self.output.read_text(encoding="utf-8")
        self.assertIn("Imagem não encontrada", document)
        self.assertIn("NÃO VALIDADA", document)

    def test_valid_local_png_is_embedded_with_verified_mime(self):
        (self.base / "image.png").write_bytes(PNG)
        data = valid_data()
        data["directions"][0]["image"] = "image.png"
        result = self.run_cli(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("data:image/png;base64," + base64.b64encode(PNG).decode(), self.output.read_text())

    def test_valid_jpeg_and_webp_have_verified_mime(self):
        data = valid_data()
        for filename, content, mime in (("image.jpeg", JPEG, "image/jpeg"), ("image.webp", WEBP, "image/webp")):
            (self.base / filename).write_bytes(content)
            data["applications"].append({"title": filename, "description": "Imagem de teste", "image": filename})
        result = self.run_cli(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        document = self.output.read_text()
        self.assertIn("data:image/jpeg;base64,", document)
        self.assertIn("data:image/webp;base64,", document)

    def test_malformed_jpeg_webp_and_png_checksum_are_rejected(self):
        for filename, content in (("bad.jpeg", JPEG[:-10]), ("bad.webp", WEBP[:-2]), ("bad.png", PNG[:-1] + b"X")):
            with self.subTest(filename=filename):
                (self.base / filename).write_bytes(content)
                data = valid_data()
                data["directions"][0]["image"] = filename
                self.assert_rejected(data, "imagem")

    def test_fake_png_svg_and_extension_mismatch_are_rejected(self):
        for filename, content in (("fake.png", b"<svg onload='alert(1)'/>"), ("image.jpg", PNG), ("art.svg", b"<svg/>")):
            with self.subTest(filename=filename):
                (self.base / filename).write_bytes(content)
                data = valid_data()
                data["applications"][0]["image"] = filename
                self.assert_rejected(data, "imagem")

    def test_truncated_image_is_rejected(self):
        (self.base / "truncated.png").write_bytes(PNG[:33])
        data = valid_data()
        data["directions"][0]["image"] = "truncated.png"
        self.assert_rejected(data, "imagem")

    def test_remote_absolute_traversal_and_ambiguous_paths_are_rejected(self):
        for path in ("https://example.com/a.png", "//example.com/a.png", "../a.png", "/tmp/a.png", "data:image/png;base64,QQ==", "a/../b.png", "C:\\a.png", "a\\b.png"):
            with self.subTest(path=path):
                data = valid_data()
                data["directions"][0]["image"] = path
                self.assert_rejected(data, "image")

    def test_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as external:
            target = Path(external) / "outside.png"
            target.write_bytes(PNG)
            (self.base / "escaped.png").symlink_to(target)
            data = valid_data()
            data["directions"][0]["image"] = "escaped.png"
            self.assert_rejected(data, "image")

    def test_oversized_image_is_rejected(self):
        (self.base / "huge.png").write_bytes(PNG + b"x" * (10 * 1024 * 1024))
        data = valid_data()
        data["directions"][0]["image"] = "huge.png"
        self.assert_rejected(data, "10 MiB")

    def test_total_embedding_budget_is_enforced_even_for_repeated_images(self):
        large = PNG[:-12] + png_chunk(b"tEXt", b"note\x00" + b"x" * (8 * 1024 * 1024)) + PNG[-12:]
        (self.base / "large.png").write_bytes(large)
        data = valid_data()
        first = data["directions"][0]
        data["directions"] = [dict(first, id=str(index), image="large.png") for index in range(4)]
        self.assert_rejected(data, "30 MiB")

    def test_empty_optional_sections_are_not_inferred_to_be_verified(self):
        data = valid_data()
        for key in ("palette", "typography", "applications", "decisions", "limitations"):
            data[key] = []
        result = self.run_cli(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        document = self.output.read_text()
        self.assertIn("Paleta não fornecida. Não validada.", document)
        self.assertIn("Aprovação não inferida.", document)
        self.assertIn("Isso não comprova ausência de limitações.", document)

    def test_symlink_output_is_rejected_even_with_force(self):
        target = self.base / "keep.html"
        target.write_text("KEEP")
        self.output.symlink_to(target)
        result = self.run_cli(valid_data(), "--force")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)
        self.assertEqual(target.read_text(), "KEEP")

    def test_bundled_example_validates(self):
        example = json.loads((ROOT / "examples" / "review.json").read_text(encoding="utf-8"))
        result = self.run_cli(example)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Exemplo fictício", self.output.read_text())

    def test_no_overwrite_without_explicit_force(self):
        self.output.write_text("KEEP", encoding="utf-8")
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_text(), "KEEP")
        result = self.run_cli(valid_data(), "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Ateliê Horizonte", self.output.read_text())

    def test_force_does_not_damage_output_on_validation_failure(self):
        self.output.write_text("KEEP", encoding="utf-8")
        data = valid_data()
        data["palette"][0]["hex"] = "invalid"
        result = self.run_cli(data, "--force")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_text(), "KEEP")

    def test_rejects_duplicate_json_keys(self):
        self.input.write_text('{"brand":"a","brand":"b"}', encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPT), "--input", str(self.input), "--output", str(self.output)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicada", result.stderr)
        self.assertFalse(self.output.exists())

    def test_cannot_overwrite_input_or_an_image_even_with_force(self):
        (self.base / "image.png").write_bytes(PNG)
        for target in (self.input, self.base / "image.png"):
            with self.subTest(target=target):
                data = valid_data()
                data["directions"][0]["image"] = "image.png"
                self.input.write_text(json.dumps(data), encoding="utf-8")
                before = target.read_bytes()
                result = subprocess.run([sys.executable, str(SCRIPT), "--input", str(self.input), "--output", str(target), "--force"], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(target.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
