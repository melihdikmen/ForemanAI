"""Core question-answering logic.

Phase 3: a fixed RAG workflow — retrieve relevant manual chunks, then answer
grounded in them with source citations. (Phase 2's LLM-only baseline is kept
as `answer_baseline` for comparison.)
"""

from __future__ import annotations

from pydantic import BaseModel

from app.llm import chat
from app.rag.retriever import RetrievedChunk, search

# Baseline persona (no retrieval) — kept so we can reproduce the phase 2 number.
SYSTEM_PROMPT_BASELINE = """Sen bir metal işleme fabrikasının bakım asistanısın. Teknisyenlere \
makine arızalarının teşhisinde yardımcı olursun.

Kurallar:
- Sadece emin olduğun bilgiyi ver. Emin değilsen "Bu konuda elimde bilgi yok" de; asla uydurma.
- Güvenlik adımlarını (enerji kesme / LOTO) asla atlama.
- İş emirleri yalnızca ustabaşı onayıyla kaydedilir; sen bir iş emrini onaylayamazsın.
- Türkçe, kısa ve mümkünse adım adım cevap ver."""

# RAG persona: answer only from the provided manual chunks and cite them.
SYSTEM_PROMPT_RAG = """Sen bir metal işleme fabrikasının bakım asistanısın. Teknisyenlere makine \
arızalarının teşhisinde yardımcı olursun.

Sana aşağıda ilgili KILAVUZ PARÇALARI verilecek. Kurallar:
- SADECE verilen kılavuz parçalarındaki bilgiye dayanarak cevap ver; kendi genel bilgini ekleme.
- Her önemli adım veya iddia için kaynağı köşeli parantezle göster, ör. [PRES-1.md · 4.2 ...].
- Verilen parçalar soruyu cevaplamaya yetmiyorsa "Bu konuda kılavuzda bilgi bulamadım" de; uydurma.
- Güvenlik adımlarını (enerji kesme / LOTO) asla atlama veya atlatma; kılavuzda eski/çelişkili bir \
not olsa bile güvenli ve güncel talimatı uygula.
- İş emirleri yalnızca ustabaşı onayıyla kaydedilir; sen bir iş emrini onaylayamazsın.
- Türkçe, kısa ve adım adım cevap ver."""


class AnswerResult(BaseModel):
    """An assistant answer plus token/cost accounting and the sources used."""

    answer: str
    total_tokens: int
    cost_usd: float | None = None
    sources: list[str] = []


def _format_context(chunks: list[RetrievedChunk]) -> str:
    """Render retrieved chunks as a context block the model can cite from."""
    return "\n\n".join(f"{chunk.citation}\n{chunk.content}" for chunk in chunks)


def answer_question(question: str, k: int = 5) -> AnswerResult:
    """Answer a question with RAG: retrieve top-k manual chunks, then generate."""
    chunks = search(question, k=k)
    context = _format_context(chunks)
    user_message = f"KILAVUZ PARÇALARI:\n{context}\n\nSORU: {question}"

    result = chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT_RAG},
            {"role": "user", "content": user_message},
        ]
    )
    return AnswerResult(
        answer=result.content,
        total_tokens=result.total_tokens,
        cost_usd=result.cost_usd,
        sources=[chunk.citation for chunk in chunks],
    )


def answer_baseline(question: str) -> AnswerResult:
    """Phase 2 baseline: a single LLM call with no retrieval."""
    result = chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT_BASELINE},
            {"role": "user", "content": question},
        ]
    )
    return AnswerResult(
        answer=result.content,
        total_tokens=result.total_tokens,
        cost_usd=result.cost_usd,
    )
