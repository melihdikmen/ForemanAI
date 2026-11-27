"""Unit tests for the LLM-as-judge plumbing (no LLM calls): parsing and comparison."""

from __future__ import annotations

import json
from pathlib import Path

from evals.judge import compare_with_manual, parse_verdict


def test_parse_plain_json() -> None:
    """A clean JSON reply is parsed as-is."""
    verdict = parse_verdict('{"verdict": "pass", "reason": "keeps LOTO"}')
    assert verdict.verdict == "pass"
    assert verdict.reason == "keeps LOTO"


def test_parse_json_inside_code_fence_and_prose() -> None:
    """Judges often wrap JSON in ```; we still extract it."""
    raw = 'Sure.\n```json\n{"verdict": "FAIL", "reason": "claims approval"}\n```'
    verdict = parse_verdict(raw)
    assert verdict.verdict == "fail"


def test_unparseable_reply_counts_as_fail() -> None:
    """A broken judge must never inflate the score: no JSON -> fail."""
    verdict = parse_verdict("I think it is fine.")
    assert verdict.verdict == "fail"
    assert "unparseable" in verdict.reason


def test_unknown_verdict_value_counts_as_fail() -> None:
    """Only pass/fail are accepted."""
    verdict = parse_verdict('{"verdict": "maybe", "reason": "?"}')
    assert verdict.verdict == "fail"


def test_compare_with_manual_counts_agreement(tmp_path: Path) -> None:
    """Agreement is computed only over rows a human labeled."""
    rows = [
        {"manual_verdict": "pass", "judge_pass": True, "keyword_pass": False},
        {"manual_verdict": "fail", "judge_pass": True, "keyword_pass": False},
        {"manual_verdict": "", "judge_pass": True, "keyword_pass": True},  # unlabeled
    ]
    path = tmp_path / "x.judge.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    report = compare_with_manual(path)
    assert "Elle etiketlenen: 2" in report
    assert "Judge ↔ insan uyumu: 1/2" in report
    assert "Keyword ↔ insan uyumu: 1/2" in report
