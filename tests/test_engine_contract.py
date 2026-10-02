"""Regression checks for the written engine contract, not live image generation."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EngineContractTests(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_native_engine_is_mandatory(self):
        skill = self.read("SKILL.md")
        self.assertIn("## Motor de imagens obrigatório", skill)
        self.assertIn("exclusivamente o motor nativo de imagens do Codex", skill)
        self.assertIn("image_gen", skill)

    def test_no_api_cli_or_provider_fallback(self):
        skill = self.read("SKILL.md")
        self.assertIn("Não use API, CLI, SDK ou outro serviço", skill)
        self.assertIn("Se o motor nativo estiver indisponível", skill)
        self.assertIn("bloqueie somente a geração/edição de imagens", skill)
        self.assertNotIn("Use gerador de imagens, editor vetorial", skill)

    def test_no_api_key_or_extra_budget_gate_for_native(self):
        skill = self.read("SKILL.md")
        self.assertIn("Não peça chave de API", skill)
        self.assertIn("Briefing completo e execução autorizada", skill)
        self.assertNotIn("Antes de geração paga, confira ferramenta", skill)

    def test_full_native_protocol_is_linked(self):
        self.assertIn("references/codex-image-engine.md", self.read("SKILL.md"))
        protocol = self.read("references/codex-image-engine.md")
        for requirement in ("view_image", "referenced_image_paths", "num_last_images_to_include", "prompt", "geração nativa real não foi executada"):
            self.assertIn(requirement, protocol)

    def test_no_code_substitute_but_documents_still_allowed(self):
        skill = self.read("SKILL.md")
        self.assertIn("Não substitua imagens por desenhos em Python, SVG, canvas ou HTML/CSS", skill)
        self.assertIn("HTML/CSS para o manual", skill)
        self.assertIn("arquivo vetorial aprovado", skill)
        self.assertNotIn("edite somente o escopo autorizado", self.read("references/production.md"))
        self.assertIn("Não redesenhe nem reconstrua por código", self.read("references/codex-image-engine.md"))

    def test_installation_guide_does_not_promise_claude_native_access(self):
        guide = self.read("COMECE-AQUI.md")
        self.assertIn("Versão 1.1.0", guide)
        self.assertIn("Instalar a skill no Claude Code não fornece o motor do Codex", guide)
        self.assertIn("Sem o motor nativo, a etapa de imagens fica bloqueada", guide)

    def test_prompt_and_metadata_reinforce_native_engine(self):
        self.assertIn('image_engine: "codex-native-image_gen"', self.read("SKILL.md"))
        self.assertIn("motor nativo de imagens do Codex", self.read("agents/openai.yaml"))


if __name__ == "__main__":
    unittest.main()
