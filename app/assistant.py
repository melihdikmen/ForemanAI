"""Core question-answering logic.

Phase 2 baseline: no retrieval, the model answers from its own knowledge only.
Later phases add RAG and tools behind this same `answer_question` entry point.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.llm import chat

# The assistant's persona and rules. Turkish on purpose: this is product voice,
# the assistant speaks Turkish to the maintenance technicians.
SYSTEM_PROMPT = """Sen bir metal işleme fabrikasının bakım asistanısın. Teknisyenlere makine \
arızalarının teşhisinde ve giderilmesinde yardımcı olursun.

Kurallar:
- Sadece emin olduğun bilgiyi ver. Emin değilsen "Bu konuda elimde bilgi yok" de; asla uydurma.
- Güvenlik adımlarını (enerji kesme / LOTO) asla atlama veya atlatma.
- İş emirleri yalnızca ustabaşı onayıyla kaydedilir; sen bir iş emrini onaylayamazsın.
- Türkçe, kısa ve mümkünse adım adım cevap ver."""


class AnswerResult(BaseModel):
    """An assistant answer plus the token/cost accounting for the call."""

    answer: str
    total_tokens: int
    cost_usd: float | None = None


def answer_question(question: str) -> AnswerResult:
    """Answer a technician's question (baseline: single LLM call, no retrieval)."""
    result = chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
    )
    return AnswerResult(
        answer=result.content,
        total_tokens=result.total_tokens,
        cost_usd=result.cost_usd,
    )
