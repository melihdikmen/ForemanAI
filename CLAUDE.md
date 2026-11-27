# CLAUDE.md — Factory Maintenance Assistant

Plan and phases: `PROCESS.md`. At the start of every session, look at the "Status tracking" table in PROCESS.md and continue from the current phase.

## Learning mode (the most important rule)

I am building this project **to learn**. My goal is to prepare for Forward Deployed Engineer / AI Engineer roles.

- My background: 7 years of mobile (React Native, TypeScript). **I am new to Python.**
- At every step, first explain briefly, in Turkish, **what** we are going to do and **why**; then write the code.
- Explain Python concepts with their **TypeScript equivalent** (e.g. `list comprehension` ≈ `array.map/filter`).
- Do not write large code blocks. Move in **small pieces**; after each piece stop and ask "any problems?".
- In every phase, have me **write at least 1–2 small parts** (exercises); then review my code and give feedback.
- When a new library/concept appears, explain it in 3–4 sentences; show a small example if needed.
- When a phase ends: short summary + ask me the control questions from PROCESS.md + update the status table.
- If I say "hızlı geç" (go fast), shorten the explanations; if I say "detaylı anlat" (go deep), go deeper.

## Engineering rules

- Python 3.12, package management with `uv`. Lint with `ruff`, tests with `pytest`.
- **Never use Turkish in code.** All identifiers (variable/function/class names), comments, docstrings, log messages and in-code strings are **English**. Turkish only for: (a) the chat/explanations you give me, (b) product text shown to users (the assistant's answers to technicians, UI text) and (c) synthetic data (manuals, fault records — Turkish factory content). Markdown documents (CLAUDE.md, PROCESS.md, README, SECURITY.md) are in English.
- Type hints on every function. Data models with Pydantic.
- **Every function, class and module must have a docstring** (English, at least one line: what it does, and why if that matters). Describe parameters and the return value in the docstring when they matter.
- **Every variable must be self-explanatory:** either carry a descriptive name or have a short comment on the line where it is defined explaining what it holds. No magic numbers/abbreviations.
- LLM calls go through **OpenRouter**: `openai` SDK + `base_url="https://openrouter.ai/api/v1"`, key `OPENROUTER_API_KEY`, model name from the `LLM_MODEL` env variable. Do not hard-code the model name; all calls go through a single `app/llm.py` module (tokens and cost are logged).
- Secrets live in `.env`; never write them into code or commits. Keep `.env.example` up to date.
- The DB user the assistant uses is **read-only**. Writes happen only through the approval endpoint.
- Do not add the assistant any **tool that sends data outside** (e-mail, HTTP POST, etc.). (This leg of the lethal trifecta is deliberately closed.)
- After every behavior change run `uv run python evals/run.py --split dev` and report the result.
- Look at the held-out set only at phase ends and when I ask.
- Commit messages short and descriptive; one commit = one logical change.

## Project structure (target)

```
app/            # FastAPI, agent, tools
  api/
  agent/
  tools/
  rag/
data/
  manuals/      # synthetic manuals (md)
  seed/         # fault-record seed script
evals/
  golden.jsonl
  run.py
  results/
ui/             # React + Vite
tests/
```
