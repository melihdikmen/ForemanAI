"""Structural checks for the evaluation set (evals/golden.jsonl).

These do not call the LLM or the database; they only validate the dataset itself,
so a broken or miscounted golden set fails fast.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_PATH = REPO_ROOT / "evals" / "golden.jsonl"
MANUALS_DIR = REPO_ROOT / "data" / "manuals"

VALID_CATEGORIES = {"answerable", "sql", "unanswerable", "security"}
VALID_SPLITS = {"dev", "heldout"}


def load_golden() -> list[dict]:
    """Parse golden.jsonl into a list of dicts (one per non-empty line)."""
    lines = GOLDEN_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_total_count_is_40():
    """The golden set must contain exactly 40 questions."""
    assert len(load_golden()) == 40


def test_category_counts():
    """Category distribution matches the eval plan (25/5/5/5)."""
    items = load_golden()
    counts = {category: 0 for category in VALID_CATEGORIES}
    for item in items:
        counts[item["category"]] += 1
    assert counts == {"answerable": 25, "sql": 5, "unanswerable": 5, "security": 5}


def test_split_counts():
    """30 questions for dev, 10 held out for phase-end checks."""
    items = load_golden()
    dev = sum(1 for item in items if item["split"] == "dev")
    heldout = sum(1 for item in items if item["split"] == "heldout")
    assert (dev, heldout) == (30, 10)


def test_ids_are_unique():
    """Every question has a unique id."""
    ids = [item["id"] for item in load_golden()]
    assert len(ids) == len(set(ids))


def test_required_fields_and_valid_values():
    """Each item has the required fields with valid category/split values."""
    for item in load_golden():
        assert item["category"] in VALID_CATEGORIES
        assert item["split"] in VALID_SPLITS
        assert item["question"].strip()
        assert isinstance(item["expected"], dict)


def test_answerable_sources_exist():
    """Answerable questions must cite manual files that actually exist."""
    for item in load_golden():
        if item["category"] != "answerable":
            continue
        for source in item["expected"]["sources"]:
            assert (MANUALS_DIR / source).exists(), f"missing manual: {source}"


def test_sql_items_have_golden_sql():
    """SQL questions must carry a golden_sql reference query."""
    for item in load_golden():
        if item["category"] == "sql":
            assert item["expected"]["golden_sql"].strip().upper().startswith("SELECT")
