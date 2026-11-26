"""FastAPI application exposing the maintenance assistant.

Run locally:  uv run uvicorn app.api.main:app --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel

from app.agent.loop import run_agent

app = FastAPI(title="Fabrika Bakım Asistanı", version="0.1.0")


class AskRequest(BaseModel):
    """Request body for POST /ask."""

    question: str


class AskResponse(BaseModel):
    """Response body for POST /ask."""

    answer: str
    total_tokens: int
    cost_usd: float | None = None
    tool_calls: list[str] = []


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness check."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    """Answer a maintenance question using the tool-calling agent."""
    result = run_agent(req.question)
    return AskResponse(
        answer=result.answer,
        total_tokens=result.total_tokens,
        cost_usd=result.cost_usd,
        tool_calls=result.tool_calls,
    )
