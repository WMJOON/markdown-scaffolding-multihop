"""Step C — Preprocess: heading-boundary chunking + metadata prefix.

No LLM calls allowed (embedding is TF-IDF, computed in placement step).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict
from pathlib import Path
from typing import List, Tuple

from ralph.common import Chunk, RunConfig, RunState
from ralph.yaml_io import read_jsonl, write_jsonl


# ---------------------------------------------------------------------------
# Section splitting
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$")


class Section:
    __slots__ = ("heading", "level", "path", "content", "start_line", "end_line")

    def __init__(
        self,
        heading: str,
        level: int,
        path: str,
        content: str,
        start_line: int,
        end_line: int,
    ):
        self.heading = heading
        self.level = level
        self.path = path
        self.content = content
        self.start_line = start_line
        self.end_line = end_line


def split_into_sections(md_text: str) -> List[Section]:
    """Split markdown text at H1-H3 boundaries."""
    lines = md_text.splitlines()
    sections: List[Section] = []
    # Stack of (level, heading) for building ancestor path
    path_stack: List[Tuple[int, str]] = []
    cur_heading = "(preamble)"
    cur_level = 0
    cur_start = 0
    cur_lines: List[str] = []

    def _build_path() -> str:
        return " > ".join(h for _, h in path_stack) if path_stack else ""

    def _flush(end_line: int) -> None:
        if cur_lines or cur_heading != "(preamble)":
            content = "\n".join(cur_lines).strip()
            if content:
                sections.append(Section(
                    heading=cur_heading,
                    level=cur_level,
                    path=_build_path(),
                    content=content,
                    start_line=cur_start,
                    end_line=end_line,
                ))

    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if m:
            _flush(i - 1)
            level = len(m.group(1))
            heading = m.group(2).strip()
            # update path stack
            while path_stack and path_stack[-1][0] >= level:
                path_stack.pop()
            path_stack.append((level, heading))
            cur_heading = heading
            cur_level = level
            cur_start = i
            cur_lines = []
        else:
            cur_lines.append(line)

    _flush(len(lines) - 1)
    return sections


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_section(
    section: Section,
    doc_id: str,
    max_words: int,
    overlap_words: int,
    min_words: int,
) -> List[Chunk]:
    """Split a section into word-counted chunks with overlap."""
    words = section.content.split()
    if not words:
        return []

    chunks: List[Chunk] = []
    pos = 0
    chunk_idx = 0

    while pos < len(words):
        end = min(pos + max_words, len(words))
        chunk_words = words[pos:end]

        # if remaining fragment is too small, merge with previous
        remaining = len(words) - end
        if 0 < remaining < min_words:
            chunk_words = words[pos:]
            end = len(words)

        text = " ".join(chunk_words)
        chunk_id_raw = f"{doc_id}:{section.path or section.heading}:{chunk_idx}"
        chunk_id = hashlib.sha256(
            chunk_id_raw.encode("utf-8")
        ).hexdigest()[:16]

        chunks.append(Chunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            section_path=section.path or section.heading,
            text=text,
            word_count=len(chunk_words),
            start_line=section.start_line,
            end_line=section.end_line,
        ))

        chunk_idx += 1
        if end >= len(words):
            break
        pos = end - overlap_words
        if pos <= 0:
            pos = end

    return chunks


def add_metadata_prefix(chunk: Chunk, doc_type: str) -> Chunk:
    """Prepend [doc_type | section_path] metadata prefix."""
    prefix = f"[{doc_type} | {chunk.section_path}]"
    chunk.metadata_prefix = prefix
    chunk.text = f"{prefix} {chunk.text}"
    return chunk


# ---------------------------------------------------------------------------
# Step handler
# ---------------------------------------------------------------------------

def run_preprocess(
    root: Path,
    state: RunState,
    config: RunConfig,
    run_dir: Path,
    apply: bool,
) -> RunState:
    """Step C: Preprocess — chunk raw documents."""
    corpus_dir = run_dir / "evidence_corpus"
    raw_dir = corpus_dir / "raw"
    chunks_dir = corpus_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # load doc index to know what was crawled
    index_path = corpus_dir / "index" / "doc_index.jsonl"

    # find all raw .md files — check evidence_corpus/raw first,
    # then fall back to local paths from intake manifest (local/directory mode)
    md_files = sorted(raw_dir.glob("*.md")) if raw_dir.exists() else []

    if not md_files:
        # local mode: resolve file paths from intake manifest
        from ralph.yaml_io import load_yaml
        manifest_path = run_dir / "intake_manifest.yaml"
        if manifest_path.exists():
            d = load_yaml(manifest_path.read_text(encoding="utf-8"))
            intake = d.get("intake_manifest", d)
            raw_dir.mkdir(parents=True, exist_ok=True)
            for entry in intake.get("entries", []):
                if entry.get("skip_reason"):
                    continue
                norm_url = entry.get("normalized_url", "")
                if norm_url.startswith("file://"):
                    src = Path(norm_url[7:])
                    if src.exists():
                        dst = raw_dir / f"{entry.get('case_id', src.stem)}.md"
                        if not dst.exists():
                            import shutil
                            shutil.copy2(src, dst)
            md_files = sorted(raw_dir.glob("*.md"))

    if not md_files:
        # also try .txt and .html
        md_files = sorted(raw_dir.glob("*.txt")) + sorted(raw_dir.glob("*.html"))

    if not md_files:
        print("[Ralph] Preprocess: no raw documents found")
        return state

    all_chunks: List[dict] = []
    total_docs = 0
    total_chunks = 0

    for md_path in md_files:
        doc_id = md_path.stem
        md_text = md_path.read_text(encoding="utf-8")

        # skip frontmatter for chunking
        if md_text.startswith("---"):
            parts = md_text.split("---", 2)
            if len(parts) >= 3:
                md_text = parts[2]

        # determine doc_type from filename or content
        doc_type = "document"
        if "paper__" in doc_id:
            doc_type = "paper"
        elif "report__" in doc_id:
            doc_type = "report"
        elif "tech_blog__" in doc_id:
            doc_type = "tech_blog"

        sections = split_into_sections(md_text)
        doc_chunks: List[Chunk] = []

        for section in sections:
            sec_chunks = chunk_section(
                section,
                doc_id,
                max_words=config.chunk_max_words,
                overlap_words=config.chunk_overlap_words,
                min_words=config.chunk_min_words,
            )
            for c in sec_chunks:
                c = add_metadata_prefix(c, doc_type)
                doc_chunks.append(c)

        total_docs += 1
        total_chunks += len(doc_chunks)
        all_chunks.extend([asdict(c) for c in doc_chunks])

    # write chunks
    write_jsonl(chunks_dir / "all_chunks.jsonl", all_chunks)
    print(f"[Ralph] Preprocess: {total_chunks} chunks from {total_docs} documents")

    return state
