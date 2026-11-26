"""Split manual markdown files into heading-based chunks with metadata.

Each chunk is one section (## or ### heading). We prepend the machine title and
heading to the body so the embedding captures context ("which machine, which section").
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Alarm codes look like E-101, A-204, C-301, R-403.
ALARM_CODE_RE = re.compile(r"\b[A-Z]-\d{3}\b")
# Level 2 or 3 markdown headings start a new chunk.
HEADING_RE = re.compile(r"^(#{2,3})\s+(.*)$")


@dataclass
class Chunk:
    """One retrievable piece of a manual, with its source metadata."""

    machine_code: str  # e.g. "PRES-3" (from the file name)
    source: str  # file name, e.g. "PRES-3.md"
    section: str  # heading text, e.g. "4.2 E-102 — Hidrolik yağ sıcaklığı yüksek"
    content: str  # title + heading + body (the text we embed)
    alarm_codes: list[str] = field(default_factory=list)


def chunk_markdown(path: Path) -> list[Chunk]:
    """Split one manual file into heading-based chunks."""
    machine_code = path.stem  # "PRES-3.md" -> "PRES-3"
    lines = path.read_text(encoding="utf-8").splitlines()
    title = next((ln[2:].strip() for ln in lines if ln.startswith("# ")), machine_code)

    chunks: list[Chunk] = []
    section = "Genel bilgi"  # text before the first ## heading
    buffer: list[str] = []

    def flush() -> None:
        body = "\n".join(buffer).strip()
        if not body:
            return
        content = f"{title} — {section}\n{body}"
        codes = sorted(set(ALARM_CODE_RE.findall(content)))
        chunks.append(Chunk(machine_code, path.name, section, content, codes))

    for line in lines:
        if line.startswith("# "):
            continue  # the document title, already captured separately
        heading = HEADING_RE.match(line)
        if heading:
            flush()
            section = heading.group(2).strip()
            buffer = []
        else:
            buffer.append(line)
    flush()
    return chunks


def chunk_all(manuals_dir: Path) -> list[Chunk]:
    """Chunk every *.md manual in a directory, sorted by file name."""
    chunks: list[Chunk] = []
    for path in sorted(manuals_dir.glob("*.md")):
        chunks.extend(chunk_markdown(path))
    return chunks
