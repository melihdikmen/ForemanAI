"""Run the golden eval set against the assistant and report scores.

Usage:
    uv run python evals/run.py --split dev
    uv run python evals/run.py --split all

Scoring is intentionally simple string-matching for now; phase 7 adds LLM-as-judge.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

# Allow `python evals/run.py` to import the `app` package by adding the repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import text  # noqa: E402

from app.agent.history import ChatTurn  # noqa: E402
from app.agent.loop import run_agent  # noqa: E402
from app.assistant import answer_question  # noqa: E402 — one-shot RAG, for A/B comparison
from app.db import engine  # noqa: E402
from app.rag.retriever import search  # noqa: E402
from app.tracing import flush_traces  # noqa: E402

GOLDEN_PATH = REPO_ROOT / "evals" / "golden.jsonl"
RESULTS_DIR = REPO_ROOT / "evals" / "results"

# Phrases that signal the assistant correctly declined / admitted it does not know.
REFUSAL_HINTS = [
    "bilmiyorum",
    "bilgi yok",
    "bilgim yok",
    "bulamadım",
    "elimde yok",
    "kılavuzda yok",
    "veri yok",
    "sahip değilim",
    "bende yok",
    "kaynaklarda yok",
    "kaynaklarımda yok",
    "bilgisi yok",
    "yardımcı olamam",
    "paylaşamam",
    "erişimim yok",
    "erişemiyorum",
    "ulaşamıyorum",
    "yer almıyor",
    "bulunmuyor",
    "bunların dışında",
    "kapsamı dışında",
    "kapsamında değil",
]


def _strip_digit_separators(text: str) -> str:
    """Remove thousands separators between digits so '6.697' matches '6697'."""
    return re.sub(r"(?<=\d)[.,\s](?=\d)", "", text)


# Cost matrix: how expensive it is to get each category wrong. Failing a safety/security
# question (e.g. skipping LOTO, obeying an injection) is far costlier than a normal lookup.
CATEGORY_COST = {"security": 3.0, "unanswerable": 1.5, "sql": 1.0, "answerable": 1.0}


def load_golden(path: Path, split: str) -> list[dict]:
    """Load eval items from a jsonl file, optionally filtered to a split."""
    lines = path.read_text(encoding="utf-8").splitlines()
    items = [json.loads(line) for line in lines if line.strip()]
    if split == "all":
        return items
    return [item for item in items if item["split"] == split]


def _norm(value: str) -> str:
    """Turkish-aware lowercasing for case-insensitive substring matching.

    str.casefold() maps "I" to "i" (English rule), so "Işık" would never match "ışık".
    Map the two Turkish capitals explicitly before folding (found via LLM-as-judge).
    """
    return value.replace("İ", "i").replace("I", "ı").casefold()


def ground_truth_sql(sql: str) -> str:
    """Run a golden SQL query and return its scalar result as a string."""
    with engine.connect() as conn:
        return str(conn.execute(text(sql)).scalar())


def _any_alternative(keyword: str, normalized_answer: str) -> bool:
    """True if any '|'-separated alternative of the keyword occurs in the answer.

    "yön valfi|yön kontrol valfi" passes when either phrasing is present. Found via
    LLM-as-judge: the model says the same thing with different words run to run.
    """
    return any(_norm(alt.strip()) in normalized_answer for alt in keyword.split("|"))


# "<bilgi|veri|kayıt> ... yok" within one sentence, e.g. "fiyat bilgisi kılavuzda ve
# araçlarda yok". Catches refusals whose exact wording is not in REFUSAL_HINTS (found via
# unans-02 in phase 11: a correct refusal the hint list missed).
_REFUSAL_PATTERN = re.compile(r"\b(bilgi\w*|veri\w*|kayıt|kayd\w*)\b[^.\n]{0,60}\byok(tur)?\b")


def is_refusal(answer: str) -> bool:
    """True if the answer contains a phrase signalling a refusal / 'I don't know'."""
    normalized = _norm(answer)
    if any(hint in normalized for hint in REFUSAL_HINTS):
        return True
    return _REFUSAL_PATTERN.search(normalized) is not None


def retrieval_metrics(item: dict, k: int = 5) -> tuple[bool, float, float] | None:
    """Return (recall_hit, precision@k, reciprocal_rank) for an item with expected sources.

    recall_hit: did at least one expected source appear in the top-k? (did we find it)
    precision@k: fraction of the top-k chunks from an expected source (how noisy the top-k is).
    reciprocal_rank: 1/position of the first expected source (1.0 = top hit, 0 = not in top-k).
        Averaged over items this is MRR: "how high does the right chunk usually land?"
    Returns None when the item has no expected sources, or when it is a multi-turn item:
    a follow-up like "bunun giderme adımları neler?" is meaningless as a raw vector query;
    the agent resolves it from the conversation, so single-query retrieval is not measured.
    """
    if item.get("history"):
        return None
    expected_sources = set(item["expected"].get("sources", []))
    if not expected_sources:
        return None
    retrieved = [chunk.source for chunk in search(item["question"], k=k)]
    if not retrieved:
        return False, 0.0, 0.0
    hit = any(source in expected_sources for source in retrieved)
    precision = sum(1 for source in retrieved if source in expected_sources) / len(retrieved)
    first_hit_position = next(
        (pos for pos, source in enumerate(retrieved, start=1) if source in expected_sources),
        None,
    )
    reciprocal_rank = 1.0 / first_hit_position if first_hit_position else 0.0
    return hit, precision, reciprocal_rank


def percentile(values: list[float], fraction: float) -> float:
    """Nearest-rank percentile, e.g. fraction=0.95 -> p95. Empty input -> 0."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(fraction * len(ordered)) - 1))
    return ordered[index]


def score_item(item: dict, answer: str) -> bool:
    """Return True if the assistant's answer satisfies the item's expectation."""
    expected = item["expected"]
    normalized = _norm(answer)
    category = item["category"]

    if category == "sql":
        # Correct if the ground-truth value appears in the answer (ignoring 1.000-style separators).
        ground_truth = _norm(ground_truth_sql(expected["golden_sql"]))
        return ground_truth in _strip_digit_separators(normalized)

    if category == "unanswerable":
        return is_refusal(answer)

    # Keyword / behavior based (answerable and security).
    ok = True
    if "must_include" in expected:
        ok = ok and all(_any_alternative(kw, normalized) for kw in expected["must_include"])
    if "must_not" in expected:
        ok = ok and not any(_norm(kw) in normalized for kw in expected["must_not"])
    if expected.get("behavior") == "refuse":
        ok = ok and is_refusal(answer)
    return ok


def main() -> None:
    """Run the eval, print a summary, and write a markdown report."""
    # Windows consoles default to cp1254; force UTF-8 so Turkish text and emoji print.
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run the golden eval set.")
    parser.add_argument("--split", default="dev", choices=["dev", "heldout", "all"])
    parser.add_argument("--tag", default="latest", help="output file name (results/<tag>.md)")
    parser.add_argument("--file", default=str(GOLDEN_PATH), help="jsonl eval file to run")
    parser.add_argument(
        "--mode",
        default="agent",
        choices=["agent", "rag"],
        help="agent = tool-calling agentic RAG; rag = one-shot RAG (for A/B comparison)",
    )
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=None,
        help="exit with code 1 if raw accuracy falls below this fraction (CI gate, e.g. 0.85)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="answer every question N times; reports mean pass rate and per-item stability",
    )
    args = parser.parse_args()

    # Pick the system under test: the agentic agent or the one-shot RAG baseline.
    answer_fn = run_agent if args.mode == "agent" else answer_question

    items = load_golden(Path(args.file), args.split)
    runs = max(1, args.runs)
    # Pass counts are fractional when runs > 1: an item that passed 2 of 3 runs adds 2/3.
    per_category_pass: dict[str, float] = defaultdict(float)
    per_category_total: dict[str, int] = defaultdict(int)
    total_cost = 0.0
    latencies: list[float] = []  # one entry per answered question-run, for p50/p95
    recall_hits = 0
    recall_total = 0
    precision_sum = 0.0
    reciprocal_rank_sum = 0.0
    weighted_pass = 0.0  # cost-weighted correct answers
    weighted_total = 0.0  # cost-weighted question count
    rows: list[tuple[str, str, int, int]] = []  # (id, category, passes, runs)
    answer_records: list[dict] = []  # every answer, saved for the judge / manual review

    for index, item in enumerate(items, start=1):
        passes = 0
        for run_number in range(1, runs + 1):
            # Multi-turn items carry earlier turns; only the agent understands them
            # (the one-shot RAG baseline has no conversation memory).
            history = [ChatTurn(**turn) for turn in item.get("history", [])]
            start = time.perf_counter()
            if args.mode == "agent":
                result = answer_fn(item["question"], history=history)
            else:
                result = answer_fn(item["question"])
            latencies.append(time.perf_counter() - start)

            passed = score_item(item, result.answer)
            passes += int(passed)
            total_cost += result.cost_usd or 0.0
            answer_records.append(
                {
                    "id": item["id"],
                    "run": run_number,
                    "category": item["category"],
                    "question": item["question"],
                    "history": item.get("history", []),
                    "expected": item["expected"],
                    "answer": result.answer,
                    "keyword_pass": passed,
                    "tool_calls": getattr(result, "tool_calls", []),
                }
            )

        pass_rate = passes / runs
        per_category_total[item["category"]] += 1
        per_category_pass[item["category"]] += pass_rate
        rows.append((item["id"], item["category"], passes, runs))

        # Weight each result by the cost matrix (failing a critical question costs more).
        cost = CATEGORY_COST[item["category"]]
        weighted_total += cost
        weighted_pass += cost * pass_rate

        # Retrieval metrics are deterministic (no LLM), so computed once per item.
        metrics = retrieval_metrics(item)
        if metrics is not None:
            hit, precision, reciprocal_rank = metrics
            recall_total += 1
            recall_hits += int(hit)
            precision_sum += precision
            reciprocal_rank_sum += reciprocal_rank

        status = "PASS" if passes == runs else ("FLAKY" if passes else "FAIL")
        print(f"[{index}/{len(items)}] {item['id']:<10} {status} ({passes}/{runs})")

    total = len(items)
    summary = {
        "split": args.split,
        "runs": runs,
        "total": total,
        "total_pass": sum(per_category_pass.values()),
        "per_category_pass": per_category_pass,
        "per_category_total": per_category_total,
        "total_cost": total_cost,
        "cost_per_query": total_cost / len(latencies) if latencies else 0.0,
        "latency_mean": statistics.fmean(latencies) if latencies else 0.0,
        "latency_p50": percentile(latencies, 0.50),
        "latency_p95": percentile(latencies, 0.95),
        "recall_hits": recall_hits,
        "recall_total": recall_total,
        "precision_avg": precision_sum / recall_total if recall_total else 0.0,
        "mrr": reciprocal_rank_sum / recall_total if recall_total else 0.0,
        "weighted_pass": weighted_pass,
        "weighted_total": weighted_total,
    }
    report = render_report(summary, rows)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{args.tag}.md"
    out_path.write_text(report, encoding="utf-8")
    answers_path = RESULTS_DIR / f"{args.tag}.answers.jsonl"
    answers_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in answer_records),
        encoding="utf-8",
    )

    flush_traces()  # Langfuse batches in the background; push everything before exit
    print("\n" + report)
    print(f"Rapor yazıldı: {out_path}")
    print(f"Cevaplar yazıldı: {answers_path}")

    # CI gate: a regression below the threshold fails the job (and the PR check).
    accuracy = summary["total_pass"] / total if total else 0.0
    if args.min_accuracy is not None and accuracy < args.min_accuracy:
        print(f"EVAL GATE FAILED: accuracy {accuracy:.2f} < required {args.min_accuracy:.2f}")
        sys.exit(1)


def render_report(summary: dict, rows: list[tuple[str, str, int, int]]) -> str:
    """Build the markdown report from the summary dict and per-question rows.

    rows: (id, category, passes, runs) — with runs > 1 an item can be partially passing.
    """
    total = summary["total"]
    total_pass = summary["total_pass"]
    runs = summary["runs"]
    per_category_total = summary["per_category_total"]
    per_category_pass = summary["per_category_pass"]

    accuracy = total_pass / total if total else 0.0
    recall = summary["recall_hits"] / summary["recall_total"] if summary["recall_total"] else 0.0
    weighted_accuracy = (
        summary["weighted_pass"] / summary["weighted_total"] if summary["weighted_total"] else 0.0
    )

    lines = [
        "# Eval sonuçları",
        "",
        f"- Split: `{summary['split']}`  ·  Soru sayısı: {total}  ·  Koşu/soru: {runs}",
        f"- **Doğruluk (ham): {total_pass:.1f}/{total} = %{accuracy * 100:.0f}**"
        + ("  (koşu ortalaması)" if runs > 1 else ""),
        f"- **Doğruluk (maliyet-ağırlıklı): %{weighted_accuracy * 100:.0f}** "
        "(kritik hatalar ağır cezalı)",
        f"- **Retrieval recall@5: {summary['recall_hits']}/{summary['recall_total']} = {recall:.2f}"
        f"  ·  precision@5: {summary['precision_avg']:.2f}  ·  MRR: {summary['mrr']:.2f}**"
        " (answerable)",
        f"- Maliyet: toplam ${summary['total_cost']:.4f}  ·  "
        f"sorgu başı ${summary['cost_per_query']:.4f}",
        f"- Gecikme: ortalama {summary['latency_mean']:.1f} sn  ·  "
        f"p50 {summary['latency_p50']:.1f} sn  ·  p95 {summary['latency_p95']:.1f} sn",
        "",
        "## Kategori bazında (maliyet ağırlığı ile)",
        "",
        "| Kategori | Doğru / Toplam | Hata maliyeti |",
        "|---|---|---|",
    ]
    for category in sorted(per_category_total):
        passed_count = per_category_pass[category]
        weight = CATEGORY_COST.get(category, 1.0)
        lines.append(
            f"| {category} | {passed_count:.1f}/{per_category_total[category]} | ×{weight} |"
        )

    lines += ["", "## Soru bazında", "", "| id | kategori | sonuç |", "|---|---|---|"]
    for item_id, category, passes, item_runs in rows:
        if passes == item_runs:
            status = "✅"
        elif passes == 0:
            status = "❌"
        else:
            status = f"⚠️ {passes}/{item_runs}"  # flaky: passed some runs, failed others
        lines.append(f"| {item_id} | {category} | {status} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
