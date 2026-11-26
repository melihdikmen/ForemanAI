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
import sys
import time
from collections import defaultdict
from pathlib import Path

# Allow `python evals/run.py` to import the `app` package by adding the repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import text  # noqa: E402

from app.agent.loop import run_agent  # noqa: E402
from app.assistant import answer_question  # noqa: E402 — one-shot RAG, for A/B comparison
from app.db import engine  # noqa: E402
from app.rag.retriever import search  # noqa: E402

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
    """Casefold for case-insensitive substring matching."""
    return value.casefold()


def ground_truth_sql(sql: str) -> str:
    """Run a golden SQL query and return its scalar result as a string."""
    with engine.connect() as conn:
        return str(conn.execute(text(sql)).scalar())


def is_refusal(answer: str) -> bool:
    """True if the answer contains a phrase signalling a refusal / 'I don't know'."""
    normalized = _norm(answer)
    return any(hint in normalized for hint in REFUSAL_HINTS)


def retrieval_metrics(item: dict, k: int = 5) -> tuple[bool, float] | None:
    """Return (recall_hit, precision@k) for an item with expected sources, else None.

    recall_hit: did at least one expected source appear in the top-k? (did we find it)
    precision@k: fraction of the top-k chunks from an expected source (how noisy the top-k is).
    """
    expected_sources = set(item["expected"].get("sources", []))
    if not expected_sources:
        return None
    retrieved = [chunk.source for chunk in search(item["question"], k=k)]
    if not retrieved:
        return False, 0.0
    hit = any(source in expected_sources for source in retrieved)
    precision = sum(1 for source in retrieved if source in expected_sources) / len(retrieved)
    return hit, precision


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
        ok = ok and all(_norm(kw) in normalized for kw in expected["must_include"])
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
    args = parser.parse_args()

    # Pick the system under test: the agentic agent or the one-shot RAG baseline.
    answer_fn = run_agent if args.mode == "agent" else answer_question

    items = load_golden(Path(args.file), args.split)
    per_category_pass: dict[str, int] = defaultdict(int)
    per_category_total: dict[str, int] = defaultdict(int)
    total_cost = 0.0
    total_latency = 0.0
    recall_hits = 0
    recall_total = 0
    precision_sum = 0.0
    weighted_pass = 0.0  # cost-weighted correct answers
    weighted_total = 0.0  # cost-weighted question count
    rows: list[tuple[str, str, bool]] = []

    for index, item in enumerate(items, start=1):
        start = time.perf_counter()
        result = answer_fn(item["question"])
        elapsed = time.perf_counter() - start

        passed = score_item(item, result.answer)
        per_category_total[item["category"]] += 1
        per_category_pass[item["category"]] += int(passed)
        total_cost += result.cost_usd or 0.0
        total_latency += elapsed
        rows.append((item["id"], item["category"], passed))

        # Weight each result by the cost matrix (failing a critical question costs more).
        cost = CATEGORY_COST[item["category"]]
        weighted_total += cost
        weighted_pass += cost * int(passed)

        # Retrieval precision/recall only apply to questions with an expected source.
        metrics = retrieval_metrics(item)
        if metrics is not None:
            hit, precision = metrics
            recall_total += 1
            recall_hits += int(hit)
            precision_sum += precision

        print(f"[{index}/{len(items)}] {item['id']:<10} {'PASS' if passed else 'FAIL'}")

    total = len(items)
    summary = {
        "split": args.split,
        "total": total,
        "total_pass": sum(per_category_pass.values()),
        "per_category_pass": per_category_pass,
        "per_category_total": per_category_total,
        "total_cost": total_cost,
        "total_latency": total_latency,
        "recall_hits": recall_hits,
        "recall_total": recall_total,
        "precision_avg": precision_sum / recall_total if recall_total else 0.0,
        "weighted_pass": weighted_pass,
        "weighted_total": weighted_total,
    }
    report = render_report(summary, rows)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{args.tag}.md"
    out_path.write_text(report, encoding="utf-8")

    print("\n" + report)
    print(f"Rapor yazıldı: {out_path}")


def render_report(summary: dict, rows: list[tuple[str, str, bool]]) -> str:
    """Build the markdown report from the summary dict and per-question rows."""
    total = summary["total"]
    total_pass = summary["total_pass"]
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
        f"- Split: `{summary['split']}`  ·  Soru sayısı: {total}",
        f"- **Doğruluk (ham): {total_pass}/{total} = %{accuracy * 100:.0f}**",
        f"- **Doğruluk (maliyet-ağırlıklı): %{weighted_accuracy * 100:.0f}** "
        "(kritik hatalar ağır cezalı)",
        f"- **Retrieval recall@5: {summary['recall_hits']}/{summary['recall_total']} = {recall:.2f}"
        f"  ·  precision@5: {summary['precision_avg']:.2f}** (answerable)",
        f"- Toplam maliyet: ${summary['total_cost']:.4f}  ·  "
        f"Ortalama gecikme: {summary['total_latency'] / total:.1f} sn",
        "",
        "## Kategori bazında (maliyet ağırlığı ile)",
        "",
        "| Kategori | Doğru / Toplam | Hata maliyeti |",
        "|---|---|---|",
    ]
    for category in sorted(per_category_total):
        passed_count = per_category_pass[category]
        weight = CATEGORY_COST.get(category, 1.0)
        lines.append(f"| {category} | {passed_count}/{per_category_total[category]} | ×{weight} |")

    lines += ["", "## Soru bazında", "", "| id | kategori | sonuç |", "|---|---|---|"]
    for item_id, category, passed in rows:
        lines.append(f"| {item_id} | {category} | {'✅' if passed else '❌'} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
