import json
import os
from typing import Any, Dict, List

try:
    from mistralai.client import MistralClient
    from mistralai.models.chat_completion import ChatMessage
except Exception:  # optional dependency at runtime
    MistralClient = None  # type: ignore
    ChatMessage = None  # type: ignore


class MistralProvider:
    """Wrapper for Mistral models to extract structured email metadata."""

    def __init__(self, model: str | None = None) -> None:
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key or MistralClient is None:
            raise RuntimeError("Mistral is not available: missing SDK or MISTRAL_API_KEY")
        self.client = MistralClient(api_key=api_key)
        self.model = model or os.getenv("MISTRAL_MODEL", "open-mixtral-8x7b")

    def _build_messages(self, email_text: str) -> List[ChatMessage]:  # type: ignore[name-defined]
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
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def analyze(self, email_text: str) -> Dict[str, Any]:
        response = self.client.chat(
            model=self.model,
            messages=self._build_messages(email_text),
            temperature=0.2,
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