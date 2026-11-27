# Factory Maintenance Assistant — PROCESS.md

> Goal: apply the topics from the FDE course (evals, RAG, tool calling, agents, HITL, security, observability, deployment) end to end, in Python, on a realistic business-unit problem.
> Way of working: with Claude Code, in **learning mode** (see CLAUDE.md). No phase starts before the previous one is finished.

---

## 1. Problem and success metrics

**Scenario (fictional customer):** "Anadolu Metal A.Ş." — a mid-sized metalworking factory. The maintenance team has 12 technicians and 2 foremen.

**Today:** When a machine fails, the technician
- searches paper/PDF manuals for a solution,
- asks a senior colleague "has this fault happened before?",
- enters the work order into Excel by hand.

Average diagnosis time is long, and knowledge is lost when experienced staff go on leave.

**Solution:** The technician describes the fault in natural language ("Pres-3 is raising a low hydraulic pressure alarm"). The assistant:
1. Finds relevant information in the manuals and past fault records and proposes likely causes and steps, **citing sources**.
2. Queries the machine's fault history from the database.
3. Prepares a **work-order draft**. The draft is not saved **until a foreman approves it**.

**Success metrics (targets):**

| Metric | Target |
|---|---|
| Answer accuracy (eval set, LLM-as-judge + manual check) | ≥ 80% |
| Retrieval recall@5 | ≥ 0.85 |
| Retrieval precision@5 (noise indicator) | measure and report |
| Citation rate | 100% (no answer without a source) |
| Correct refusal on questions that should get "I don't know" | ≥ 90% |
| Database writes without approval | 0 |
| p95 latency | < 8 s |
| Cost per query | measured and written to the README |

> **Precision/recall and the cost matrix:** Recall alone is not enough — recall answers "did we miss the
> right thing", precision answers "is what we fetched noisy"; they are read together. Also, not every error
> costs the same: **missing a critical fault** (false negative) is far more expensive than a cheap wrong
> suggestion. So we prioritize faults as **critical / normal / low** and define a **cost matrix** (how
> expensive each error is); eval scores are weighted with that matrix.

## 2. Scope (prioritized with RICE)

| Feature | Priority | Note |
|---|---|---|
| Q&A over manuals + fault records (RAG) | High | Core value |
| Fault history queries (SQL tool) | High | |
| Work-order draft + foreman approval (HITL) | High | The critical FDE topic |
| Simple web UI | Medium | React (Vite) — my strong area |
| MCP server | Medium | To expose the tools to other clients |
| Vision (fault recognition from photos) | Out of scope | v2 idea |

## 3. Technology choices

- **Language:** Python 3.12 (package management: `uv`, lint: `ruff`, tests: `pytest`)
- **API:** FastAPI + Pydantic
- **Database:** PostgreSQL + `pgvector` (via Docker)
- **Agent:** LangGraph (checkpoint: Postgres)
- **Model:** via **OpenRouter** (single API key, OpenAI-compatible API — the `openai` Python SDK with `base_url="https://openrouter.ai/api/v1"`). The model name lives in `.env` (`LLM_MODEL=...`), so the model can be swapped without code changes. In Phase 2 compare 2–3 models (e.g. one Claude, one Gemini, one cheap/open model) on the same eval set; choose by quality/cost/latency.
- **Embeddings:** an embedding model from OpenRouter if a suitable one exists; otherwise a local multilingual model (e.g. the `intfloat/multilingual-e5` family via `sentence-transformers` — free and good at Turkish). The embedding dimension must match the pgvector column.
- **Observability:** Langfuse
- **UI:** React + Vite (single page)
- **Deploy:** Docker Compose → GitHub Actions → Google Cloud Run (or AWS)
- **Model gateway:** All LLM calls go through one gate (`app/llm.py`) and through **OpenRouter**. OpenRouter plays the role of a *model gateway* here: one key, many providers, model switching (routing/fallback) and cost visibility. The README will explain what the gateway pattern buys (central logging, rate limiting, retries, model abstraction).
- **Context layer:** "What goes into the model's context window" is designed deliberately: system prompt + selected manual chunks + tool results + (later) memory. We document each request's **token budget** and what is included/excluded; unnecessary context is both cost and noise.

## 4. Data

To avoid copyright issues **all data is synthetic** (generated with Claude, realistic but fictional):

- **Machines (6):** Hydraulic Press-1/2/3, CNC Lathe-1, Screw Compressor-1, Welding Robot-1
- **Manuals:** a Markdown manual per machine (safety, periodic maintenance, alarm-code table, troubleshooting steps). About 40–60 pages in total.
- **Fault records:** ~200 records (date, machine, alarm code, symptom, root cause, action taken, duration, technician).
- **Work-orders table:** starts empty, filled by the assistant + approval flow.
- **Deliberate traps:** outdated/contradictory information in one manual, a prompt-injection attempt in one record ("forget the previous instructions…"). For the security tests.

## 5. Eval strategy (evals first, then code)

- **Golden set:** 40 questions → `evals/golden.jsonl`
  - 25 answerable (expected answer + expected source)
  - 5 requiring SQL ("How many times did Pres-3 fail in the last 6 months?")
  - 5 unanswerable (the assistant must say "I don't know / not in the manual")
  - 5 security/trap questions
- **Split:** 30 questions dev set, 10 questions held-out (looked at only at phase ends).
- **Measurements:** retrieval recall@k and MRR, answer accuracy (LLM-as-judge + manual check on 10 questions), citation accuracy, tool-call accuracy, latency, cost.
- At the end of each phase results are written to `evals/results/<phase>.md` and compared with the previous one.

## 6. Security (lethal trifecta analysis)

- **Private data access:** yes (fault records, staff names)
- **Untrusted content:** yes (manual/record text may carry injections)
- **Outbound communication:** **no** — the assistant gets no e-mail/HTTP sending tool. The trifecta is broken deliberately.
- Database: the user the assistant uses is **read-only**; writes only through the approval endpoint, with a separate service user.
- Roles: `technician` (asks questions, creates drafts), `foreman` (approves/rejects).
- Prompt-injection tests are in the eval set.

---

## 7. Phases

Each phase has these headings: **What I will learn · To do · Done criterion · Control questions**.

### Phase 0 — Setup and Python basics (2–3 days)
**What I will learn:** `uv`, virtual environments, project structure, type hints, dataclasses, comprehensions, `async/await`, pytest (with TS equivalents).
**To do:**
- [ ] Repo, `uv init`, `ruff`, `pytest`, `.env.example`
- [ ] Postgres + pgvector up via Docker
- [ ] Small Python exercises (Claude has me write them): read CSV → filter → write a test
**Done criterion:** `uv run pytest` green, DB running with `docker compose up`.
**Control questions:** How would I write a list comprehension in TS? Why is `async def` needed?

### Phase 1 — Data and eval set (3–4 days)
**What I will learn:** data modeling, SQLAlchemy/psycopg, Pydantic models, how to write a good eval set.
**To do:**
- [ ] Machine, fault-record, work-order tables (schema + migration)
- [ ] Synthetic manuals (`data/manuals/*.md`) and 200 fault records (seed script)
- [ ] 40-question `evals/golden.jsonl` + dev/held-out split
**Done criterion:** The seed script loads the data; the eval set has been reviewed by hand.
**Control questions:** Why do we write the eval set before the code? What is the held-out set for?

### Phase 2 — Baseline (2 days)
**What I will learn:** FastAPI, endpoints, Pydantic request/response, LLM API calls, the eval script.
**To do:**
- [ ] `POST /ask` — just ask the LLM, no RAG
- [ ] `evals/run.py` — runs over the golden set and produces a score
**Done criterion:** Baseline scores in `evals/results/faz2.md`. (Expected to be low — the point is a reference.)
**Control questions:** Without a baseline, how would we prove RAG helps?

### Phase 3 — RAG (1 week)
**What I will learn:** chunking, embeddings, pgvector, similarity search, hybrid search (BM25 + vector), reranking, recall@k / MRR, citations.
**To do:**
- [ ] Chunk the manuals by heading, add metadata (machine, section, alarm code)
- [ ] Embeddings + pgvector index
- [ ] Vector-only first, then hybrid search — compare both with evals
- [ ] A source for every claim in the answer (`[Pres Kılavuzu §4.2]`)
- [ ] "Not found in the manual" behavior on unanswerable questions
**Done criterion:** recall@5 ≥ 0.85; accuracy clearly above baseline; results written.
**Control questions:** What does chunk size affect? For which question types is hybrid search better than vector?

### Phase 4 — Tools and agent (1 week)
**What I will learn:** tool calling, LangGraph (state, node, edge), tool design, tool-use evals.
**To do:**
- [ ] Tools: `search_manuals`, `get_fault_history(machine_id, since)` (read-only SQL), `draft_work_order(...)` (draft only)
- [ ] LangGraph flow: understand the question → pick a tool → answer
- [ ] Measure that the right tool is called on SQL questions
**Done criterion:** ≥ 4 of the 5 SQL questions correct; tool calls visible in Langfuse/logs.
**Control questions:** Why did we give the agent a narrow tool instead of letting it write raw SQL?

### Phase 5 — Human approval and persistent state (4–5 days)
**What I will learn:** LangGraph `interrupt()`, Postgres checkpoints, resuming, role-based authorization.
**To do:**
- [x] When a work-order draft is produced the flow stops and lands with the foreman
- [x] `POST /work-orders/{id}/approve|reject` (`foreman` role only)
- [x] Pending approvals survive a service restart
- [x] React UI: technician chat screen + foreman approval list
**Done criterion:** No work order is written to the DB without approval (proven by test).

**Decision applied (2026-11-26):** LangGraph `interrupt()` / checkpoints were NOT used. Approval can take
hours and the agent has nothing to do after approval → the need is *persistent state*, not *durable
execution*. State is a state machine in the DB: the agent only produces drafts (`/ask` → `drafts`, does
not touch the DB) → technician "Send for approval" (`POST /work-orders` → PENDING) → foreman
approve/reject (`require_role`, row lock `FOR UPDATE`, repeated decision → 409, rejection reason
required). Identity is fake in v1 (`X-User`/`X-Role` headers) → SSO in a real deployment (Phase 6/8).
The agent has no write path, but the DB user is not yet separate/read-only → Phase 6.
**Control questions:** Which operations should be automatic and which human-approved? Why?

### Phase 6 — Security and guardrails (3–4 days)
**What I will learn:** lethal trifecta, prompt injection, least privilege, input/output checks.
**To do:**
- [x] Read-only DB user; writes only in the approval service
- [x] Test with injection-carrying records; the assistant must not follow the instructions
- [x] Output check: safety steps (energy isolation/LOTO) must not be skipped
- [x] `SECURITY.md`: threat model and mitigations
**Done criterion:** All 5 security questions pass.

**Decision applied (2026-11-27):** Layered defense; accepted that the LLM can be tricked.
(1) `foreman_reader` Postgres role, SELECT only; agent tools connect via `ReadOnlySessionLocal`,
writes are rejected by Postgres (proven by test). (2) Finding: because `get_fault_history` returns
only aggregates, the trap records never reached the model, so injection was not being measured. The new
tool `list_recent_faults` wraps text in `<fault_record>` tags; sec-06/07 added to the golden set
(42 questions). Tag on/off A/B: no difference (Haiku 5.5 resisted in both cases); kept as defense in
depth. (3) `app/guard.py`: LLM-free regex output check; catches phrases like "LOTO not needed /
I approved", does not delete the answer, appends a warning + `guard_flags` for the UI banner.
(4) Scorer bug: `must_not` keywords tripped on the model *quoting* the trap; narrowed to action claims.
Dev 91% (noise ±5%, security 5/5); held-out run for the first time: 80%.
**Control questions:** Which leg of the trifecta did we break in this system, and why that one?

### Phase 7 — Observability and automated evals (3 days)
**What I will learn:** tracing, LLM-as-judge, cost/latency measurement, evals in CI, precision/recall and the cost matrix.
**To do:**
- [x] A Langfuse trace for every request (retrieval, tool, model, tokens)
- [x] LLM-as-judge + manual comparison on 10 questions (how reliable is the judge?)
- [x] Report **precision@k and recall@k** together for retrieval; MRR
- [x] **Cost matrix:** weight errors by fault priority (critical/normal/low); missing a critical one (false negative) is heavily penalized. Report scores both raw and cost-weighted.
- [x] p95 latency and cost-per-query report
- [x] Evals in GitHub Actions: PR goes red if the score drops below the threshold
**Done criterion:** Eval report with a single command (precision/recall + cost-weighted); runs in CI.

**Decision applied (2026-11-27):**
- `run.py`: MRR, p50/p95 latency, cost per query, `--runs N` (run average + per-question stability
  ⚠️ 2/3), `--min-accuracy` (CI gate), answer dump to `<tag>.answers.jsonl`.
- **Noise measured:** 3 runs × 32 questions → 93%; no question failed 3 of 3, 4 questions "flaky".
- **LLM-as-judge** (`evals/judge.py`, judge = Sonnet 5.5, system = Haiku 5.5; a separate `JUDGE_MODEL`
  to avoid using the same model). Agreement with the keyword scorer on 32 answers 91%; in all 3
  disagreements the judge was right. 10 answers labeled by hand: judge↔human 10/10, keyword↔human 7/10.
  Small and easy sample; the judge's leniency was not tested on genuinely wrong answers (we have few).
- **Scorer bugs found by the judge** (all fixed; re-scoring the recorded 96+32 answers passed them all):
  (1) keyword brittleness → `must_include` alternatives with `|`; (2) missing refusal patterns
  ("bende yok", "kaynaklarda yok"); (3) **Turkish capital I**: `casefold()` turns "Işık" into "işık",
  which did not match "ışık" → Turkish-specific mapping. So the "flaky" results in Phase 6 came from the
  scorer, not the model.
- **Division of labor:** keyword scorer in CI (cheap, deterministic); judge periodically, to find scorer
  bugs (expensive, nondeterministic, not in CI).
- **Langfuse** (`app/tracing.py`): no-op without keys. Trace tree: ask(agent) → llm.complete(generation,
  model+tokens+cost) → tool(span, real tool name) → vector_search(retriever). `trace_id` in the `/ask` response.
- **CI** (`.github/workflows/ci.yml`): pgvector service → init SQL → alembic → seed → index → ruff → pytest →
  `run.py --min-accuracy 0.85` (noise margin). The repo is not on GitHub yet; needs a push + the
  `OPENROUTER_API_KEY` secret.
- Phase 7 result (dev, single run): **97%** (31/32; the remaining 1 was also the scorer, 32/32 after the fix).
  p50 4.7 s, p95 7.0 s, $0.0010 per query, MRR 0.83.
**Control questions:** When should we not trust the LLM-as-judge? What happens when recall is high but precision is low? Which error is the most expensive?

### Phase 8 — Deploy and MCP (4–5 days)
**What I will learn:** Docker images, Compose, CI/CD, Cloud Run, environment variables/secret management, MCP servers; (alternative) **AWS Bedrock AgentCore** as a managed agent platform.
**To do:**
- [x] Dockerfile + `docker-compose.yml` (api, db, ui)
- [x] GitHub Actions: test → eval → build → deploy
- [x] Deploy to Cloud Run, health check
- [x] Expose the tools as an MCP server (connect from Claude Desktop and try it)
- [x] (Optional/alternative) **Comparison with AgentCore**: map the agent/tool/HITL/secret pieces we wrote to their AgentCore counterparts — **Gateway** (publishing tools as MCP), **Identity** (authn/authz), **Policy** (permissions/guardrails), **Memory** (managed memory), **Runtime** (execution). Discuss the "build it yourself vs managed platform" decision in the README.
**Done criterion:** Public demo link; tools usable from another client via MCP.

**Decision applied (2026-11-27):**
- **One image, one service.** Multi-stage Dockerfile: Node builds the React UI, `python:3.12-slim` + uv runs
  the API and serves `ui/dist` from `/` (same origin, no CORS). Embedding model baked into the image so a
  cold start never downloads it. Non-root user. Entrypoint runs `alembic upgrade head`, then uvicorn on `$PORT`.
- **Cloud Run (europe-west1) + Neon Postgres** (free tier, pgvector 0.8.7, read-only role with a random
  password). Secrets only in Secret Manager, bound as env vars; `.env` never leaves the laptop. 2 GiB RAM,
  0–2 instances, concurrency 20. Demo: https://foremanai-998448097011.europe-west1.run.app
- **CI/CD** (`.github/workflows/ci.yml`): push to master → ruff → pytest → eval gate (≥ 0.85) → image
  tagged with the commit sha → `gcloud run deploy` → `/health`. Auth via **Workload Identity Federation**
  (GitHub OIDC → `github-deployer` service account with only Cloud Run admin + Artifact Registry writer);
  no key file in GitHub. Rollback = deploy an older sha.
- **MCP** (`app/mcp_server.py`, stdio): the four agent tools registered from `TOOL_SCHEMAS` (one source of
  truth), `read_only_hint` on the three readers. Verified from Claude Desktop ("Connected to foremanai (4
  tools)"). Note: through MCP the *client's* model interprets tool output; our system prompt and output guard
  are not in the loop.
- **Two deploy bugs, both environment differences:** (1) secrets written with a trailing newline → invalid
  HTTP header (fix: strip, verify length); (2) git on Windows drops the executable bit → CI image failed with
  "permission denied" on the entrypoint while the local image worked (fix: `COPY --chmod=755`, `+x` in the
  index). Lesson: the laptop build is not the CI build; make permissions and inputs explicit.
- **AWS considered, not chosen** (the user has credits): App Runner + RDS was the equivalent; stayed with the
  plan to keep one cloud for v1. **AgentCore mapping** (build vs managed): Gateway ≈ our MCP server (would
  publish the OpenAPI as MCP tools, adds auth/Policy); Runtime ≈ Cloud Run for the agent loop only (ARM64,
  `/invocations` contract; would split the web app from the agent); Identity ≈ fake `X-Role` headers →
  real IdP; Policy ≈ `app/guard.py` + role checks, but as Cedar rules on tool calls; Memory ≈ nothing yet
  (Phase 11 candidate). What we would gain: auth, policy and memory as services. What we would lose: one
  deployable artifact, portability, and the understanding we built by writing each layer.
- **Known limits:** cold start 13–17 s (p95 target 8 s) — `--min-instances=1` fixes it for ~$15/month;
  identity still fake (anyone can send the foreman header); 2.08 GB image (onnxruntime + model).
**Control questions:** Where do we keep secrets? What did MCP make easier? Which pieces would AgentCore take over from us, and what would we lose (control/portability)?

### Phase 9 — Delivery and story (2 days)
**To do:**
- [ ] README: problem, architecture diagram, eval results (phase-by-phase improvement table), security design, cost
- [ ] 2–3 minute demo video
- [ ] `HANDOVER.md`: how someone else operates this system (runbook)
- [ ] LinkedIn post
- [ ] Interview story: "How I solved a maintenance team's problem in a measurable way"

---

## 7.1 Advanced / extension phases (v2 — optional, advanced course topics)

> These deepen the system after v1 (Phases 0–9) is delivered.
> Each is measured with the eval set; "did it help" is shown with numbers.

### Phase 10 — Agentic RAG and multi-agent (sub-agents)
**What I will learn:** query rewriting/expansion, iterative (multi-step) retrieval, self-RAG, the agent evaluating a search and searching again; sub-agent / multi-agent (orchestrator + specialist agents).
**To do:**
- [ ] If the chunks from the first search are insufficient, the agent **rewrites the query** and searches again (a loop instead of a single search)
- [ ] Irrelevance/gap detection: on a low retrieval score "ask again" or "I don't know"
- [ ] (Optional) **Sub-agent** pattern: e.g. "retrieval specialist", "SQL specialist", "security auditor" sub-agents + an orchestrator
- [ ] Evals: what did agentic RAG gain over single-shot RAG in recall/precision and accuracy?
**Done criterion:** On at least one "hard" question class agentic RAG beats the Phase 4 agent in evals.
**Control questions:** How much did iterative search raise cost? When is multi-agent unnecessary complexity?

### Phase 11 — Memory
**What I will learn:** short-term (conversation) vs long-term memory, writing/recalling memory, feeding memory into the context layer.
**To do:**
- [ ] **Short-term (conversation) memory first:** the UI sends the previous turns with each `/ask`; the agent replays only questions and final answers (not tool output), capped at the last N turns. Add 3–4 multi-turn questions to the golden set. (Found in Phase 8: the deployed demo forgets the previous message.)
- [ ] Long-term memory store (e.g. the foreman's preferences, frequent rejection reasons, machine-specific notes)
- [ ] Recall relevant memory per request and add it to the context (without exceeding the token budget)
- [ ] Privacy/PII: what is stored in memory and what is not
- [ ] Evals: personalization and accuracy difference with memory on/off
**Done criterion:** The assistant remembers previous decisions/preferences and uses them where relevant (proven by test).
**Control questions:** When is memory useful, and when does it risk misleading/stale information?

### Phase 12 — Self-improvement
**What I will learn:** an improvement loop driven by production signal (rejection reasons), prompt/eval optimization, regression protection.
**To do:**
- [ ] Collect and label the foreman's **rejection reasons** (why was it rejected?)
- [ ] Build a loop that improves prompt/few-shot/retrieval settings from that signal
- [ ] **Held-out guard:** validate every improvement on the held-out set; roll back if it drops (prevent overfitting)
**Done criterion:** At least one improvement derived from rejection reasons raises the dev score without lowering the held-out score.
**Control questions:** What does improving on dev but dropping on held-out indicate? How do we roll an improvement back?

### Phase 13 — Autonomy levels and Responsible AI
**What I will learn:** autonomy levels (suggestion → approved action → autonomous action), responsible AI (fairness, transparency, accountability, misuse).
**To do:**
- [ ] **Autonomy table:** for each operation (answer, SQL query, work-order draft, work-order save) which level — automatic, human-approved, or forbidden — and **why**
- [ ] **Responsible AI assessment:** safety impact of a wrong diagnosis, privacy of staff data, injection/misuse, "who is responsible if the assistant makes a mistake"
- [ ] `RESPONSIBLE_AI.md`: autonomy table + risks/mitigations + limits
**Done criterion:** Autonomy table and responsible AI document written; the code conforms to the table (e.g. saving a work order is never autonomous).
**Control questions:** Which operation is unacceptable to make autonomous, and why? What is the condition for raising autonomy (which eval threshold)?

---

## 8. Status tracking

| Phase | Status | Start | End | Main result |
|---|---|---|---|---|
| 0 Setup | ✅ | 2026-11-26 | 2026-11-26 | uv+ruff+pytest set up, app/ structure, .env(.example), Docker Postgres16+pgvector running, pytest green |
| 1 Data + evals | ✅ | 2026-11-26 | 2026-11-26 | 3 tables+migration (SQLAlchemy/Alembic), 6 manuals, seed 6 machines+202 records (2 injection traps), 40-question golden.jsonl (30 dev/10 held-out) + structural tests |
| 2 Baseline | ✅ | 2026-11-26 | 2026-11-26 | app/llm.py (OpenRouter, token/cost logging), POST /ask, evals/run.py. Model: claude-haiku-5.5. Baseline dev 63% (ans 13/19, sql 0/4, unans 4/4, sec 2/3) |
| 3 RAG | ✅ | 2026-11-26 | 2026-11-26 | fastembed (MiniLM-384) + pgvector, 61 chunks, vector search + citations. Dev accuracy 63%→77%, recall@5=0.95 (target ≥0.85). Hybrid search (3.8) skipped (recall sufficient) |
| 4 Agent | ✅ | 2026-11-26 | 2026-11-26 | Plain tool-calling agent (not LangGraph): search_manuals, get_fault_history (read-only), draft_work_order (draft). Dev accuracy 77%→93%, sql 0/4→4/4. Eval scorer hardened (refusal + number normalization) |
| 5 HITL | ✅ | 2026-11-26 | 2026-11-26 | DB state machine (instead of LangGraph): draft → technician submits (PENDING) → foreman approve/reject (role check, row lock, 409, rejection reason). `/ask` → `drafts`. React+Tailwind UI (chat + approval queue). 28 tests; dev eval 93% (no regression) |
| 6 Security | ✅ | 2026-11-27 | 2026-11-27 | Read-only Postgres role (proven by test), `list_recent_faults` + `<fault_record>` tag, regex output guard + UI warning, SECURITY.md. Golden 42 questions (7 security). Dev 91% (security 5/5), held-out first run 80% (sec-02, unans-04 failed) |
| 7 Observability | ✅ | 2026-11-27 | 2026-11-27 | run.py: MRR, p50/p95, cost per query, `--runs` (3 runs: 93%, 4 flaky), `--min-accuracy`. LLM-as-judge (Sonnet) found 3 scorer bugs (Turkish I, keyword brittleness, refusal patterns); 10 manual labels: judge 10/10, keyword 7/10. Langfuse traces (agent→generation→tool→retriever). GitHub Actions CI (waiting for push). Dev 97% |
| 8 Deploy + MCP | ✅ | 2026-11-27 | 2026-11-27 | Multi-stage Docker image (API + UI, model baked in), compose. Cloud Run (europe-west1) + Neon Postgres, Secret Manager. CI/CD with eval gate and WIF (no key file). MCP server (stdio) connected from Claude Desktop. Two env-difference bugs fixed (secret newline, exec bit). Cold start 13–17 s |
| 9 Delivery | ⬜ | | | |
| 10 Agentic RAG + multi-agent (v2) | ✅ | 2026-11-26 | 2026-11-26 | Agentic RAG: machine-filtered search, iterative re-search, score visibility. A/B on the hard question set (evals/hard.jsonl): single-shot 80% vs agentic 100% (cost ~58% higher). A/B via run.py --file/--mode. Sub-agents deferred (optional) |
| 11 Memory (v2) | ⬜ | | | |
| 12 Self-improvement (v2) | ⬜ | | | |
| 13 Autonomy + Responsible AI (v2) | ⬜ | | | |

## 9. Open questions

- Model: which model on OpenRouter? Try 2–3 models on the baseline in Phase 2 and decide by eval results. (Model routing: cheap model for simple questions, strong model for complex/agent steps — try in Phase 7.)
- UI: React web, or React Native mobile for technicians? (v1: web)
- Can we get 15 minutes of feedback from a real factory/maintenance worker? (Very valuable for FDE practice)
