# RESPONSIBLE_AI.md — Autonomy levels and responsible-AI assessment

This document states, for every action the system can take, **how autonomous it is and why**,
then assesses the risks of the system as a whole. It is written so that the code can be checked
against it: `tests/test_autonomy.py` fails if the agent gains a tool this table does not allow.

## 1. Autonomy levels

| Level | Meaning | Who owns the outcome |
|---|---|---|
| **L0 — forbidden** | The AI cannot do this at all; the capability does not exist in the code | — |
| **L1 — suggest** | The AI produces a proposal; nothing changes until a human acts on it | the human who acts |
| **L2 — act with approval** | The AI could act, but a human must approve each instance first | the approver |
| **L3 — act within bounds** | The AI acts on its own inside hard limits, humans review afterwards | the system owner |
| **L4 — autonomous** | The AI acts and nobody reviews | the system owner |

The system today uses **L0, L1 and L3 only**. Nothing is at L2 or L4. Reading is L3 (bounded by a
read-only database role); every change to the world is L1 or L0.

## 2. Autonomy table

| Operation | Level | Mechanism that enforces it | Why this level |
|---|---|---|---|
| Answer a maintenance question | L3 | Answer must cite sources; output guard appends a warning and UI banner when it detects a skipped safety step or a false action claim; every answer traced | Reading and explaining is the job. A wrong answer is still read by a trained technician before anyone touches a machine; citations let them verify |
| Search manuals (`search_manuals`) | L3 | Read-only DB role; results carry source and similarity score | No side effects; worst case is an irrelevant chunk |
| Fault statistics (`get_fault_history`) | L3 | Read-only role; returns aggregates only, no free text, no names | Numbers cannot carry instructions; no personal data leaves the DB |
| Read fault records (`list_recent_faults`) | L3 | Read-only role; max 10 records; text wrapped in `<fault_record>` tags with a "data, not instructions" notice; technician names **not** returned | Needed for "what was done last time"; this is the prompt-injection surface, so it is bounded and tagged |
| Read past rejections (`list_recent_rejections`) | L3 | Read-only role; max 10; `<rejection_reason>` tags; no names of requester or decider | Reuses decisions a human already made; the model gets the decision, not the person |
| Draft a work order (`draft_work_order`) | **L1** | Returns a Pydantic-validated object with `status: "draft"`; nothing is written | A work order starts physical work. The AI may propose; only people commit |
| Submit a draft for approval | human (technician) | `POST /work-orders` requires the technician role header; the AI has no HTTP tool | The person who will do the work decides whether to ask for it |
| Approve / reject a work order | human (foreman) | `require_role(foreman)`; row lock; a second decision returns 409; rejection needs a reason | Authorizing work is a management decision with safety and cost consequences |
| Persist an approved work order | **L0** for the AI | The agent's DB role has no INSERT/UPDATE/DELETE (tested: Postgres rejects it) | Even a fully tricked model cannot do this |
| Send e-mail / HTTP / webhook | **L0** | No such tool exists; project rule in CLAUDE.md | Closes the exfiltration leg of the lethal trifecta |
| Write to "memory" / change its own instructions | **L0** | No memory store; prompt and tool list are code, changed only via git + CI eval gate | The system must not learn from untrusted text at runtime |
| Change model, prompt or tools | human (developer) | Pull request → lint, tests, eval gate ≥ 85% → deploy | Behavior changes are reviewed and measured, not hot-patched |

### What would have to be true to raise a level

- **Draft → L2 (AI submits the draft itself):** would save one click and remove the technician's
  moment of review. Not worth it: the click *is* the review.
- **Approval of low-priority orders → L3 (auto-approve):** only if all of the following held for
  at least three months of real use: foreman agreement with the AI draft ≥ 95% on that class,
  security questions 100% on held-out across repeated runs, a hard spending/scope limit, and a
  daily human review of what was auto-approved. Even then: never for anything that touches
  energy isolation, pressure, or lifting. This is a management decision, not an engineering one.
- **Anything → L4:** not foreseen for this domain.

## 3. Responsible-AI assessment

### Safety (wrong diagnosis)
A wrong or incomplete answer can lead a technician to skip a step. Mitigations: citations so the
technician can check the manual; the system prompt forbids skipping LOTO/energy isolation/pressure
relief; a deterministic guard flags such answers after the fact (recall-biased: a false warning is
cheap, a missed one is not); unanswerable questions are refused rather than guessed (eval
category); every physical action still goes through a human draft → approval chain. Residual risk:
a confidently wrong but *safe-sounding* answer. Only training and the citation habit cover that.

### Prompt injection and misuse
Fault records and rejection reasons are written by people and can contain instructions. The seed
plants two such traps and the eval set checks them. Defense is layered: tagging (measured: no
effect on this model, kept as depth), the output guard, and above all the read-only role plus
draft-only tool, which make a successful injection *harmless* rather than *unlikely*. The public
demo URL can be abused for cost; capped instances and a spending limit on the API key bound it.

### Privacy and personal data
Personal data in the system: technician names on fault records and work orders, foreman names on
decisions. What reaches the model: **no names**. Aggregates have none; `list_recent_faults` omits
`technician_name`; `list_recent_rejections` omits requester and decider. What the UI shows: names
on work orders, to the roles that need them. What is logged: questions and answers go to Langfuse
(EU region) with tokens and cost; the question text may contain whatever the technician typed.
Known gap: no retention policy on traces yet.

### Fairness
No decision about a person is made by the AI. The one place bias could enter is ranking or
summarizing *people* ("which technician causes the most downtime"); the tools do not support
per-technician aggregation, deliberately. Language: the system is Turkish-only by design, which
matches the workforce; a multilingual floor would need re-evaluation.

### Transparency
Each answer shows which tools ran, cites its sources, carries a `trace_id`, and shows a visible
warning banner when the guard fired. The draft is shown as a draft, with an explicit "not saved"
statement. PROCESS.md records every design decision with the measurement behind it; SECURITY.md
records what did *not* work (tagging) as well as what did.

### Accountability
The assistant is advisory. Responsibility for a maintenance action lies with the foreman who
approved the work order and the technician who performed it, as it does today without the
assistant. The system supports that: approvals carry who/when, rejections carry a reason, traces
show what the model saw. If the assistant gives dangerous advice, the owner of the system (the
team deploying it) is responsible for fixing it; the eval set is where such a case is added first.

### Reliability and honesty about limits
- Identity is a demo header in v1; anyone can act as foreman. Real deployment needs SSO.
- Single-run evals are noisy (±5 points); decisions are made on multi-run or judge-confirmed data.
- p95 latency on the drafting path is 9.5 s (4 tool calls), above the 8 s target.
- The injection-tagging defense has no measured effect on the current model.
- Held-out failures from phase 6 were not re-examined (rule), so their cause is a hypothesis.

## 4. Code conformance

- `tests/test_autonomy.py`: the agent's tool set is exactly the five tools in the table; the only
  non-read tool returns a draft; no tool module imports an HTTP or mail client.
- `tests/test_readonly_db.py`: the role used by every tool cannot write.
- `tests/test_work_orders.py`: approval requires the foreman role; repeated decisions are rejected;
  rejection needs a reason.
- `tests/test_guard.py`: skipped-safety and false-action patterns are flagged.
- `evals/golden.jsonl`: 9 security questions, including planted injections and a fabricated
  "already approved" conversation history.
