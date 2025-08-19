import json
import os
from typing import Any, Dict

try:
    import anthropic
except Exception:  # optional dependency at runtime
    anthropic = None  # type: ignore


class AnthropicProvider:
    """Wrapper for Anthropic Claude models to extract structured email metadata."""

    def __init__(self, model: str | None = None) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or anthropic is None:
            raise RuntimeError("Anthropic is not available: missing SDK or ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")

    def analyze(self, email_text: str) -> Dict[str, Any]:
        system = (
            "You are a helpful assistant that extracts structured information from emails. "
            "Return STRICT JSON only with keys: summary_lines (array of exactly 5 strings), "
            "category (one of: Academic, HR, Finance, IT, General), "
            "urgency (one of: Critical, High, Normal), "
            "action_required (one of: Yes, No)."
        )
        user = (
            "Email:\n\n" + email_text + "\n\n"
            "Instructions:\n"
            "- Summarize the email into exactly 5 concise bullet points (no bullets in output), one sentence per item.\n"
            "- Classify category: Academic, HR, Finance, IT, or General.\n"
            "- Set urgency: Critical, High, or Normal.\n"
            "- Set action_required: Yes if the user is asked to do anything explicit; otherwise No.\n"
            "Output JSON only, no extra text."
        )
        resp = self.client.messages.create(
            model=self.model,
            temperature=0.2,
            max_tokens=800,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        content_text = ""
        for block in resp.content:
            if hasattr(block, "text"):
                content_text += block.text
        return self._parse_json(content_text or "{}")

    @staticmethod
    def _parse_json(content: str) -> Dict[str, Any]:
        if content.strip().startswith("```"):
            parts = content.strip().split("\n", 1)
            if len(parts) == 2:
                content = parts[1]
            if content.strip().endswith("```"):
                content = content.strip().removesuffix("```")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(content[start : end + 1])
            raise