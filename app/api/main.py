"""FastAPI application exposing the maintenance assistant.

Run locally:  uv run uvicorn app.api.main:app --reload
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent.history import ChatTurn
from app.agent.loop import run_agent
from app.api.work_orders import router as work_orders_router
from app.tools.work_orders import WorkOrderDraft
from app.tracing import flush_traces


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hook: flush buffered Langfuse traces when the server stops."""
    yield  # the app serves requests here
    flush_traces()


app = FastAPI(title="Fabrika Bakım Asistanı", version="0.1.0", lifespan=lifespan)


app.include_router(work_orders_router)


class AskRequest(BaseModel):
    """Request body for POST /ask."""

    question: str
    # Previous turns of this chat (oldest first). The server keeps only the last few;
    # see app/agent/history.py. Empty = a fresh conversation.
    history: list[ChatTurn] = []


class AskResponse(BaseModel):
    """Response body for POST /ask."""

    answer: str
    total_tokens: int
    cost_usd: float | None = None
    tool_calls: list[str] = []
    # Work-order drafts the agent proposed; NOT saved. The UI shows them with a
    # "send for approval" button that POSTs a draft to /work-orders.
    drafts: list[WorkOrderDraft] = []
    # Output-guard hits (e.g. "skip_loto"). Non-empty means a safety warning was
    # appended to the answer; the UI can also show a banner.
    guard_flags: list[str] = []
    # Langfuse trace id for this request (None when tracing is disabled).
    trace_id: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness check."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    """Answer a maintenance question using the tool-calling agent."""
    result = run_agent(req.question, history=req.history)
    return AskResponse(
        answer=result.answer,
        total_tokens=result.total_tokens,
        cost_usd=result.cost_usd,
        tool_calls=result.tool_calls,
        drafts=result.drafts,
        guard_flags=result.guard_flags,
        trace_id=result.trace_id,
    )


# Built React UI (ui/dist). Mounted last so API routes above win; anything else
# (index.html, assets) is served as static files. Absent in dev, where Vite serves
# the UI and proxies /api to this server.
UI_DIST_DIR = Path(__file__).resolve().parents[2] / "ui" / "dist"
if UI_DIST_DIR.is_dir():
    app.mount("/", StaticFiles(directory=UI_DIST_DIR, html=True), name="ui")
