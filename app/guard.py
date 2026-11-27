"""Deterministic output guard: checks the assistant's final answer before it reaches
the technician.

We do not trust the LLM to always keep safety steps or to describe its own powers
honestly (a prompt injection may have talked it into either). This layer has no LLM
in it: plain pattern matching, so it is predictable and testable. A flagged answer
is NOT suppressed (the technician still gets the information); a fixed safety
warning is appended and the flags are returned so the API/UI can show a banner.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from app.tools.work_orders import WorkOrderDraft

# Phrases that tell the technician to skip or shorten a safety step.
# Each pattern is a regex matched case-insensitively against the normalized text.
UNSAFE_PATTERNS: dict[str, str] = {
    "skip_loto": r"loto(?:'ya|ya)?\s+gerek\s+(?:yok|kalmaz)|loto\s+(?:gereksiz|atlan)",
    "skip_energy_isolation": r"enerji(?:yi)?\s+kesme(?:den|ye\s+gerek\s+yok)",
    "skip_pressure_relief": (
        r"tahliye(?:sine|ye)?\s+gerek\s+(?:yok|kalmaz)|tahliye\s+(?:etmeden|yapmadan)"
    ),
    "skip_safety_steps": r"güvenlik\s+adım(?:ı|ları)nı\s+atla(?!ma)",
    "skip_approval": r"onay(?:sız|\s+gerektirmeden|\s+beklemeden)\s+(?:iş\s+emri|oluştur|kaydet)",
}

# The assistant claiming an action it cannot perform (it only drafts).
FALSE_ACTION_PATTERNS: dict[str, str] = {
    "claims_approved": r"\b(?:onayladım|onaylandı|onaylıyorum)\b",
    "claims_saved": r"\b(?:kaydettim|veritabanına\s+kaydedildi|kayıt\s+altına\s+aldım)\b",
    "claims_sent": r"\b(?:gönderdim|ustabaşına\s+ilettim)\b",
}

SAFETY_WARNING = (
    "\n\n⚠️ Güvenlik uyarısı: Bu cevapta güvenlik adımlarının atlanmasını veya "
    "yapılmamış bir işlemin yapıldığını ima eden ifade tespit edildi. Enerji kesme / "
    "LOTO ve basınç tahliyesi hiçbir koşulda atlanmaz; iş emirleri yalnızca ustabaşı "
    "onayıyla geçerlidir."
)


class GuardResult(BaseModel):
    """Outcome of the guard: the (possibly annotated) answer plus what was flagged."""

    answer: str
    flags: list[str] = []  # names of the matched patterns, empty when clean

    @property
    def flagged(self) -> bool:
        """True if at least one pattern matched."""
        return bool(self.flags)


def _normalize(text: str) -> str:
    """Lowercase (Turkish-aware for İ/I) and collapse whitespace for matching."""
    lowered = text.replace("İ", "i").replace("I", "ı").lower()
    return re.sub(r"\s+", " ", lowered)


def _find_flags(text: str, patterns: dict[str, str]) -> list[str]:
    """Return the names of all patterns that match the text."""
    normalized = _normalize(text)
    return [name for name, pattern in patterns.items() if re.search(pattern, normalized)]


def check_answer(answer: str, drafts: list[WorkOrderDraft] | None = None) -> GuardResult:
    """Scan the answer (and any draft work orders) and append a warning if flagged.

    Args:
        answer: the assistant's final text for the technician.
        drafts: work-order drafts proposed in the same run; their action text is
            checked too, since a draft is what the foreman will approve.
    """
    flags = _find_flags(answer, UNSAFE_PATTERNS) + _find_flags(answer, FALSE_ACTION_PATTERNS)
    for draft in drafts or []:
        draft_text = f"{draft.title}\n{draft.description}\n{draft.proposed_actions}"
        flags += [f"draft:{flag}" for flag in _find_flags(draft_text, UNSAFE_PATTERNS)]

    if not flags:
        return GuardResult(answer=answer)
    return GuardResult(answer=answer + SAFETY_WARNING, flags=flags)
