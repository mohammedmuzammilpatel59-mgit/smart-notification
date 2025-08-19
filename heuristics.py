from __future__ import annotations

import re
from typing import Any, Dict, List

CATEGORIES = ["Academic", "HR", "Finance", "IT", "General"]
URGENCY_LEVELS = ["Critical", "High", "Normal"]


def _guess_category(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["professor", "syllabus", "course", "assignment", "university", "campus", "exam", "grade"]):
        return "Academic"
    if any(k in t for k in ["payroll", "benefit", "vacation", "leave", "hiring", "recruit", "offer letter", "onboarding", "policy", "hr"]):
        return "HR"
    if any(k in t for k in ["invoice", "receipt", "payment", "refund", "expense", "budget", "billing", "accounting", "tax"]):
        return "Finance"
    if any(k in t for k in ["server", "outage", "deploy", "bug", "error", "database", "network", "vpn", "support ticket", "reset password", "authentication", "it"]):
        return "IT"
    return "General"


def _guess_urgency(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["urgent", "immediately", "asap", "today", "within 1 hour", "security incident", "breach", "deadline today", "production down"]):
        return "Critical"
    if any(k in t for k in ["tomorrow", "this week", "by end of day", "soon", "time-sensitive", "follow up", "reminder"]):
        return "High"
    return "Normal"


def _detect_action_required(text: str) -> str:
    imperative_patterns = [
        r"\bplease\s+(review|respond|reply|confirm|approve|sign|submit|update|schedule|complete|attend)\b",
        r"\baction\s+required\b",
        r"\bkindly\s+(review|respond|reply|confirm|approve|sign|submit|update|schedule|complete|attend)\b",
        r"\bfill out\b",
        r"\bclick\s+the\s+link\b",
        r"\bsend\s+us\b",
        r"\bprovide\s+\w+\b",
    ]
    for pat in imperative_patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            return "Yes"
    return "No"


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _top_sentences(text: str, n: int = 5) -> List[str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    subject = lines[0] if lines else ""
    # Body is all lines after the first
    body_text = " ".join(lines[1:]) if len(lines) > 1 else ""
    # Normalize whitespace
    subject_norm = re.sub(r"\s+", " ", subject).strip()
    body_sentences = [re.sub(r"\s+", " ", s).strip() for s in _split_sentences(body_text)]
    combined: List[str] = []
    if subject_norm:
        combined.append(subject_norm)
    combined.extend(body_sentences)
    # Deduplicate while preserving order
    seen = set()
    unique: List[str] = []
    for s in combined:
        if s and s not in seen:
            seen.add(s)
            unique.append(s)
    selected = unique[:n]
    while len(selected) < n:
        selected.append(selected[-1] if selected else "")
    return selected[:n]


def analyze_with_heuristics(email_text: str) -> Dict[str, Any]:
    category = _guess_category(email_text)
    urgency = _guess_urgency(email_text)
    action_required = _detect_action_required(email_text)
    summary_lines = _top_sentences(email_text, 5)
    cleaned = [re.sub(r"^[\-\*\d\.\)\s]+", "", s).strip() for s in summary_lines]
    deduped: List[str] = []
    for s in cleaned:
        if s and (not deduped or s != deduped[-1]) and s not in deduped:
            deduped.append(s)
    while len(deduped) < 5:
        deduped.append("")
    deduped = deduped[:5]
    return {
        "summary_lines": deduped,
        "category": category,
        "urgency": urgency,
        "action_required": action_required,
    }