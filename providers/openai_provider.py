import json
import os
from typing import Any, Dict, List

try:
    from openai import OpenAI
except Exception:  # optional dependency at runtime
    OpenAI = None  # type: ignore


class OpenAIProvider:
    """Wrapper for OpenAI GPT models to extract structured email metadata."""

    def __init__(self, model: str | None = None) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or OpenAI is None:
            raise RuntimeError("OpenAI is not available: missing SDK or OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _build_messages(self, email_text: str) -> List[Dict[str, str]]:
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
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def analyze(self, email_text: str) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=self._build_messages(email_text),
        )
        content = response.choices[0].message.content or "{}"
        return self._parse_json(content)

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