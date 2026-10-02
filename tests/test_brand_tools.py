"""Local, offline CLI contract tests for brand_tools.py."""

import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "brand_tools.py"


def png_header(width, height):
    payload = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + payload + struct.pack(">I", zlib.crc32(b"IHDR" + payload))


class BrandToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, *args, code=0):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            text=True, capture_output=True, timeout=15,
        )
        self.assertEqual(result.returncode, code, result.stderr + result.stdout)
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail("stdout must contain one JSON object: " + repr(result.stdout))
        self.assertIsInstance(data, dict)
        self.assertNotIn(str(self.root), result.stdout)
        return data

    def svg(self, body, name="logo.svg"):
        path = self.root / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_contrast_black_white(self):
        result = self.cli("contrast", "--foreground", "#000000", "--background", "#FFFFFF")
        self.assertEqual(result["ratio"], 21.0)
        self.assertTrue(all(result["pass"].values()))
        self.assertIn("logo", " ".join(result["limitations"]).lower())

    def test_contrast_does_not_round_normal_text_threshold(self):
        result = self.cli("contrast", "--foreground", "#777777", "--background", "#ffffff")
        self.assertAlmostEqual(result["ratio"], 4.478089453577214, places=12)
        self.assertFalse(result["pass"]["normal_text"])
        self.assertTrue(result["pass"]["large_text"])

    def test_contrast_large_text_threshold(self):
        failed = self.cli("contrast", "--foreground", "#959595", "--background", "#ffffff")
        passed = self.cli("contrast", "--foreground", "#949494", "--background", "#ffffff")
        self.assertLess(failed["ratio"], 3)
        self.assertFalse(failed["pass"]["large_text"])
        self.assertFalse(failed["pass"]["non_text"])
        self.assertGreater(passed["ratio"], 3)
        self.assertTrue(passed["pass"]["non_text"])

    def test_contrast_srgb_linear_segment_and_short_hex(self):
        result = self.cli("contrast", "--foreground", "#0a0a0a", "--background", "#000")
        self.assertAlmostEqual(result["ratio"], 1 + (10 / 255 / 12.92) / 0.05, places=12)

    def test_invalid_color_exits_two_with_json(self):
        result = self.cli("contrast", "--foreground", "#00000080", "--background", "#ffffff", code=2)
        self.assertIn("error", result)

    def test_png_header_dimensions_and_hash(self):
        import hashlib
        content = png_header(320, 240)
        (self.root / "mark.png").write_bytes(content)
        result = self.cli("audit", self.root)
        self.assertEqual(set(result), {"files", "issues", "limitations"})
        record = result["files"][0]
        self.assertEqual(record["path"], "mark.png")
        self.assertEqual(record["format"], "png")
        self.assertEqual(record["dimensions"], {"width": 320, "height": 240, "unit": "px"})
        self.assertEqual(record["sha256"], hashlib.sha256(content).hexdigest())
        self.assertIn("decod", " ".join(result["limitations"]).lower())

    def test_malformed_png_exits_two(self):
        (self.root / "bad.png").write_bytes(b"not a PNG")
        result = self.cli("audit", self.root, code=2)
        self.assertIn("malformed_png", {item["code"] for item in result["issues"]})

    def test_svg_structure_inventory(self):
        self.svg('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="60" viewBox="0 0 120 60"><path d="M0 0 L10 10"/></svg>')
        result = self.cli("audit", self.root)
        record = result["files"][0]
        self.assertEqual(record["viewBox"], [0.0, 0.0, 120.0, 60.0])
        self.assertEqual(record["dimensions"], {"width": "120", "height": "60"})
        self.assertFalse(record["raster_embedded"])
        self.assertEqual(record["text_elements"], 0)

    def test_svg_text_fonts_and_raster_are_warnings(self):
        self.svg('<svg xmlns="http://www.w3.org/2000/svg"><text font-family="SECRET_FONT">CONFIDENTIAL</text><image href="data:image/png;base64,iVBORw0K"/></svg>')
        result = self.cli("audit", self.root)
        record = result["files"][0]
        self.assertTrue(record["raster_embedded"])
        self.assertEqual(record["text_elements"], 1)
        self.assertGreater(record["font_references"], 0)
        self.assertNotIn("CONFIDENTIAL", json.dumps(result))
        self.assertNotIn("SECRET_FONT", json.dumps(result))
        self.assertTrue(all(issue["severity"] == "warning" for issue in result["issues"]))

    def test_malformed_xml_exits_two_and_omits_content(self):
        self.svg('<svg><text>PRIVATE_NAME</svg>')
        result = self.cli("audit", self.root, code=2)
        self.assertIn("malformed_svg", {issue["code"] for issue in result["issues"]})
        self.assertNotIn("PRIVATE_NAME", json.dumps(result))

    def test_doctype_is_rejected_before_entity_expansion(self):
        self.svg('<!DOCTYPE svg [<!ENTITY x "PRIVATE_VALUE">]><svg>&x;</svg>')
        result = self.cli("audit", self.root, code=2)
        self.assertIn("unsafe_xml_declaration", {issue["code"] for issue in result["issues"]})

    def test_utf16_doctype_is_rejected(self):
        document = '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE svg [<!ENTITY x "PRIVATE_VALUE">]><svg>&x;</svg>'
        (self.root / "encoded.svg").write_bytes(document.encode("utf-16"))
        result = self.cli("audit", self.root, code=2)
        self.assertIn("unsafe_xml_declaration", {issue["code"] for issue in result["issues"]})

    def test_unknown_xml_encoding_returns_json_error(self):
        self.svg('<?xml version="1.0" encoding="private-unknown-encoding"?><svg/>')
        result = self.cli("audit", self.root, code=2)
        self.assertIn("malformed_svg", {issue["code"] for issue in result["issues"]})
        self.assertNotIn("private-unknown-encoding", json.dumps(result))

    def test_xml_depth_is_bounded(self):
        self.svg('<svg>' + '<g>' * 130 + '</g>' * 130 + '</svg>')
        result = self.cli("audit", self.root, code=2)
        self.assertIn("xml_limit", {issue["code"] for issue in result["issues"]})

    def test_css_font_shorthand_is_a_warning(self):
        self.svg('<svg xmlns="http://www.w3.org/2000/svg"><style>.title { font: 16px PRIVATE_FONT; }</style></svg>')
        result = self.cli("audit", self.root)
        self.assertEqual(result["files"][0]["font_references"], 1)
        self.assertNotIn("PRIVATE_FONT", json.dumps(result))

    def test_xml_processing_instruction_is_an_error(self):
        self.svg('<?xml-stylesheet href="https://private.example/secret.css"?><svg/>')
        result = self.cli("audit", self.root, code=2)
        self.assertIn("xml_processing_instruction", {issue["code"] for issue in result["issues"]})
        self.assertNotIn("private.example", json.dumps(result))

    def test_svg_active_content_is_an_error(self):
        self.svg('<svg xmlns="http://www.w3.org/2000/svg" onload="privateCode()"><script>secret()</script><foreignObject/></svg>')
        result = self.cli("audit", self.root, code=2)
        record = result["files"][0]
        self.assertEqual(record["scripts"], 1)
        self.assertEqual(record["event_handlers"], 1)
        self.assertEqual(record["foreign_objects"], 1)
        self.assertNotIn("privateCode", json.dumps(result))

    def test_external_svg_references_include_css_without_leaking_url(self):
        self.svg('<svg xmlns="http://www.w3.org/2000/svg"><style>@import "https://private.example/font.css"; .a { fill: url(https://private.example/a); font-family: Secret }</style><use href="other.svg#id"/></svg>')
        result = self.cli("audit", self.root, code=2)
        self.assertGreaterEqual(result["files"][0]["external_references"], 3)
        self.assertNotIn("private.example", json.dumps(result))
        self.assertNotIn("Secret", json.dumps(result))

    def test_css_escaped_external_reference_is_reported(self):
        self.svg(r'<svg xmlns="http://www.w3.org/2000/svg"><style>.a { fill: u\72l(https://private.example/a); }</style></svg>')
        result = self.cli("audit", self.root, code=2)
        self.assertGreater(result["files"][0]["external_references"], 0)

    def test_unterminated_css_url_is_reported(self):
        self.svg('<svg xmlns="http://www.w3.org/2000/svg"><style>.a { fill:url(https://private.example }</style></svg>')
        result = self.cli("audit", self.root, code=2)
        self.assertIn("css_unparsed", {issue["code"] for issue in result["issues"]})
        self.assertNotIn("private.example", json.dumps(result))

    def test_unterminated_css_comment_is_reported(self):
        self.svg('<svg xmlns="http://www.w3.org/2000/svg"><style>/* PRIVATE /* PRIVATE</style></svg>')
        result = self.cli("audit", self.root, code=2)
        self.assertIn("css_unparsed", {issue["code"] for issue in result["issues"]})

    def test_fragment_reference_is_not_external(self):
        self.svg('<svg xmlns="http://www.w3.org/2000/svg"><defs><path id="p"/></defs><use href="#p"/><path style="fill:url(#p)"/></svg>')
        result = self.cli("audit", self.root)
        self.assertEqual(result["files"][0]["external_references"], 0)

    def test_non_svg_xml_is_rejected(self):
        self.svg('<html><body>PRIVATE</body></html>')
        result = self.cli("audit", self.root, code=2)
        self.assertIn("not_svg", {issue["code"] for issue in result["issues"]})

    def test_recursive_relative_paths_and_unknown_format(self):
        nested = self.root / "nested"
        nested.mkdir()
        (nested / "notes.ai").write_bytes(b"PRIVATE SOURCE")
        result = self.cli("audit", self.root)
        self.assertEqual(result["files"][0]["path"], "nested/notes.ai")
        self.assertEqual(result["files"][0]["format"], "unknown")
        self.assertIn("unsupported_format", {issue["code"] for issue in result["issues"]})
        self.assertNotIn("PRIVATE SOURCE", json.dumps(result))

    def test_symlinks_are_not_followed(self):
        with tempfile.TemporaryDirectory() as other:
            outside = Path(other) / "outside.svg"
            outside.write_text('<svg><script>SECRET</script></svg>')
            (self.root / "alias.svg").symlink_to(outside)
            (self.root / "folder").symlink_to(Path(other), target_is_directory=True)
            result = self.cli("audit", self.root)
        self.assertEqual(result["files"], [])
        self.assertEqual(len(result["issues"]), 2)
        self.assertTrue(all(issue["code"] == "symlink_skipped" for issue in result["issues"]))

    def test_symlink_input_is_rejected(self):
        original = self.svg('<svg/>')
        alias = self.root / "alias.svg"
        alias.symlink_to(original)
        result = self.cli("audit", alias, code=2)
        self.assertEqual(result["issues"][0]["code"], "symlink_input")

    def test_oversize_file_is_not_read(self):
        with (self.root / "huge.svg").open("wb") as stream:
            stream.truncate(16 * 1024 * 1024 + 1)
        result = self.cli("audit", self.root, code=2)
        self.assertIn("file_too_large", {issue["code"] for issue in result["issues"]})
        self.assertIsNone(result["files"][0]["sha256"])

    def test_missing_input_returns_audit_contract(self):
        result = self.cli("audit", self.root / "missing", code=2)
        self.assertEqual(set(result), {"files", "issues", "limitations"})
        self.assertEqual(result["files"], [])

    def test_init_creates_draft_project_and_directories(self):
        project = self.root / "project"
        result = self.cli("init", "--project", project, "--name", "Marca exemplo", "--mode", "new")
        self.assertEqual(result["status"], "created")
        record = json.loads((project / "project.json").read_text())
        self.assertEqual(record["name"], "Marca exemplo")
        self.assertEqual(record["mode"], "new")
        self.assertEqual(record["stage"], "briefing")
        self.assertEqual(record["status"], "draft")
        for key in ("approvals", "sources", "deliverables", "open_questions"):
            self.assertEqual(record[key], [])
        for directory in ("sources", "directions", "approved", "applications", "manual", "delivery", "evidence"):
            self.assertTrue((project / directory).is_dir())

    def test_init_never_overwrites_existing_project(self):
        original = b'{"private":"do not change"}'
        (self.root / "project.json").write_bytes(original)
        result = self.cli("init", "--project", self.root, "--name", "Other", "--mode", "refresh", code=2)
        self.assertIn("error", result)
        self.assertEqual((self.root / "project.json").read_bytes(), original)
        self.assertFalse((self.root / "sources").exists())

    def test_init_rejects_existing_symlink_child(self):
        with tempfile.TemporaryDirectory() as other:
            (self.root / "sources").symlink_to(other, target_is_directory=True)
            self.cli("init", "--project", self.root, "--name", "Other", "--mode", "applications", code=2)
        self.assertFalse((self.root / "project.json").exists())

    def test_cli_parse_errors_are_json(self):
        result = self.cli("init", "--name", "Missing project", "--mode", "new", code=2)
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
