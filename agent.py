from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

from heuristics import analyze_with_heuristics

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Lazy imports of providers to avoid requiring all SDKs at runtime
try:
    from providers import OpenAIProvider
except Exception:
    OpenAIProvider = None  # type: ignore

try:
    from providers import AnthropicProvider
except Exception:
    AnthropicProvider = None  # type: ignore

try:
    from providers import MistralProvider
except Exception:
    MistralProvider = None  # type: ignore

try:
    from sheets import append_row_to_sheet
except Exception:
    append_row_to_sheet = None  # type: ignore


def select_provider(preferred: Optional[str] = None):
    provider_name = (preferred or os.getenv("PROVIDER") or "").lower().strip()

    if provider_name in ("openai", "gpt", "gpt-4o"):
        if OpenAIProvider is None:
            raise RuntimeError("OpenAI provider code not available")
        return OpenAIProvider()

    if provider_name in ("anthropic", "claude"):
        if AnthropicProvider is None:
            raise RuntimeError("Anthropic provider code not available")
        return AnthropicProvider()

    if provider_name in ("mistral", "mixtral"):
        if MistralProvider is None:
            raise RuntimeError("Mistral provider code not available")
        return MistralProvider()

    # Auto-detect by env keys
    if os.getenv("OPENAI_API_KEY") and OpenAIProvider is not None:
        return OpenAIProvider()
    if os.getenv("ANTHROPIC_API_KEY") and AnthropicProvider is not None:
        return AnthropicProvider()
    if os.getenv("MISTRAL_API_KEY") and MistralProvider is not None:
        return MistralProvider()

    return None


def normalize_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    summary_lines = raw.get("summary_lines") or raw.get("summary") or []
    if isinstance(summary_lines, str):
        summary_lines = [s.strip("- *\t ") for s in summary_lines.splitlines() if s.strip()]
    if not isinstance(summary_lines, list):
        summary_lines = []
    summary_lines = summary_lines[:5]
    while len(summary_lines) < 5:
        summary_lines.append(summary_lines[-1] if summary_lines else "")

    category = raw.get("category") or "General"
    urgency = raw.get("urgency") or "Normal"
    action_required = raw.get("action_required") or raw.get("action") or "No"
    action_required = "Yes" if str(action_required).strip().lower() in ("yes", "true", "y") else "No"

    return {
        "summary_lines": [str(s).strip() for s in summary_lines],
        "category": str(category),
        "urgency": str(urgency),
        "action_required": action_required,
    }


def format_makefile_line(result: Dict[str, Any]) -> str:
    summary = " ".join(result["summary_lines"]).replace("\n", " ")
    summary = " ".join(summary.split())
    return f"Summary: {summary} Category: {result['category']} Urgency: {result['urgency']} Action: {result['action_required']}"


def analyze_email(email_text: str, provider_hint: Optional[str] = None) -> Dict[str, Any]:
    provider = select_provider(provider_hint)
    if provider is None:
        raw = analyze_with_heuristics(email_text)
    else:
        try:
            raw = provider.analyze(email_text)
        except Exception:
            raw = analyze_with_heuristics(email_text)
    return normalize_result(raw)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Smart Notification Agent for email processing")
    parser.add_argument("--provider", choices=["openai", "anthropic", "mistral"], help="LLM provider to use", nargs="?")
    parser.add_argument("--email-file", help="Path to a text file with raw email content")
    parser.add_argument("--email", help="Raw email content passed directly", nargs="?")
    parser.add_argument("--sheet-id", help="Google Sheets spreadsheet ID (optional)")
    parser.add_argument("--sheet-tab", help="Worksheet name (optional)")
    parser.add_argument("--service-account", help="Path to service account JSON (optional)")

    args = parser.parse_args(argv)

    email_text = ""
    if args.email:
        email_text = args.email
    elif args.email_file:
        with open(args.email_file, "r", encoding="utf-8") as f:
            email_text = f.read()
    else:
        if not sys.stdin.isatty():
            email_text = sys.stdin.read()
    email_text = email_text.strip()
    if not email_text:
        print("No email text provided. Use --email or --email-file or pipe input.", file=sys.stderr)
        return 2

    result = analyze_email(email_text, args.provider)
    output_line = format_makefile_line(result)
    print(output_line)

    if args.sheet_id and args.sheet_tab and append_row_to_sheet is not None:
        row = [
            " ".join(result["summary_lines"]),
            result["category"],
            result["urgency"],
            result["action_required"],
        ]
        try:
            append_row_to_sheet(
                spreadsheet_id=args.sheet_id,
                worksheet_name=args.sheet_tab,
                row_values=row,
                service_account_json_path=args.service_account,
            )
        except Exception as e:
            print(f"Warning: failed to append to Google Sheets: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())