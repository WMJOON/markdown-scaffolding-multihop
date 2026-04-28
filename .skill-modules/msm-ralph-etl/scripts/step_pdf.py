"""PDF 다운로드, MD 변환, ollama sidecar 생성 유틸리티.

변환 우선순위:
  1. opendataloader-pdf  (Java 11+ 필요, 품질 최상)
  2. pymupdf4llm         (순수 Python fallback, pip install pymupdf4llm)

sidecar 생성 우선순위:
  (a) ollama HTTP 직접 호출 → .summary.md + .concepts.jsonl 생성
  (b) ollama 미실행 시 → .sidecar_pending.json 기록 (Claude MCP fallback 신호)

원문 보존 원칙: clean_markdown() 적용 없이 변환 출력을 그대로 저장.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from ralph.common import URLEntry

# ---------------------------------------------------------------------------
# PDF URL 감지
# ---------------------------------------------------------------------------

_PDF_PATH_PATTERNS = (
    "/pdf/",          # arxiv.org/pdf/xxxx, semanticscholar.org/paper/.../pdf
    "/pdfs/",
    ".pdf",
)

_PDF_HOSTS = frozenset({
    "arxiv.org",
    "ar5iv.labs.arxiv.org",
})


def is_pdf_url(url: str) -> bool:
    """URL이 PDF 문서를 가리키는지 휴리스틱으로 판단."""
    lower = url.lower()
    parsed = urlparse(lower)

    if parsed.netloc in _PDF_HOSTS and "/pdf/" in parsed.path:
        return True
    for pat in _PDF_PATH_PATTERNS:
        if parsed.path.endswith(pat) or parsed.path.endswith(pat.rstrip("/")):
            return True
        if lower.endswith(pat):
            return True
    return False


def sniff_pdf_bytes(path: Path) -> bool:
    """파일 첫 4바이트가 %PDF인지 확인."""
    try:
        return path.read_bytes()[:4] == b"%PDF"
    except Exception:
        return False


# ---------------------------------------------------------------------------
# PDF 다운로드
# ---------------------------------------------------------------------------

def download_pdf(
    url: str,
    dest: Path,
    timeout: int = 60,
) -> Tuple[int, str]:
    """PDF를 dest 경로에 다운로드.

    Returns:
        (status_code, resolved_url)
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; RalphETL/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            resolved = resp.url
            status = resp.status

        if status < 400:
            if data[:4] != b"%PDF":
                return 422, resolved  # Content-Type 불일치
            dest.write_bytes(data)
        return status, resolved

    except urllib.error.HTTPError as exc:
        return exc.code, url
    except Exception as exc:
        print(f"  [pdf] download error: {exc}")
        return 500, url


# ---------------------------------------------------------------------------
# PDF → Markdown 변환
# ---------------------------------------------------------------------------

def _convert_opendataloader(pdf_path: Path) -> Optional[str]:
    """opendataloader-pdf로 변환. Java 11+ 필요."""
    try:
        import opendataloader_pdf
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            opendataloader_pdf.convert(
                input_path=str(pdf_path),
                output_dir=str(tmp_dir),
                format="markdown",
                quiet=True,
            )
            md_files = sorted(tmp_dir.glob("*.md"))
            if md_files:
                return md_files[0].read_text(encoding="utf-8")
        return None
    except subprocess.CalledProcessError as exc:
        if "Unable to locate a Java Runtime" in (exc.stderr or ""):
            print("  [pdf] opendataloader-pdf: Java 11+ 미설치, pymupdf4llm으로 fallback")
        else:
            print(f"  [pdf] opendataloader-pdf 오류: {exc.stderr or exc}")
        return None
    except ImportError:
        return None
    except Exception as exc:
        print(f"  [pdf] opendataloader-pdf 예외: {exc}")
        return None


def _convert_pymupdf4llm(pdf_path: Path) -> Optional[str]:
    """pymupdf4llm으로 변환. 순수 Python fallback."""
    try:
        import pymupdf4llm
        return pymupdf4llm.to_markdown(str(pdf_path))
    except ImportError:
        print("  [pdf] pymupdf4llm 미설치: pip install pymupdf4llm")
        return None
    except Exception as exc:
        print(f"  [pdf] pymupdf4llm 예외: {exc}")
        return None


def convert_pdf_to_md(pdf_path: Path) -> Optional[str]:
    """PDF를 Markdown 텍스트로 변환. opendataloader → pymupdf4llm 순서로 시도."""
    md = _convert_opendataloader(pdf_path)
    if md is not None:
        return md
    md = _convert_pymupdf4llm(pdf_path)
    return md


# ---------------------------------------------------------------------------
# MD 조합 (원문 보존 — clean_markdown 우회)
# ---------------------------------------------------------------------------

def build_pdf_md(
    entry: URLEntry,
    resolved_url: str,
    status_code: int,
    body_md: str,
) -> str:
    """frontmatter + PDF 변환 본문을 결합. 본문은 가공 없이 그대로."""
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [
        "---",
        f"case_id: {entry.case_id}",
        f"source_type: {entry.source_type}",
        f"title: {entry.title}",
        f"url: {entry.url}",
        f"resolved_url: {resolved_url}",
        f"status_code: {status_code}",
        f"fetched_at: {fetched_at}",
        f"doc_type: pdf",
        "---",
        "",
        body_md.strip(),
        "",
    ]
    if entry.industry_mapping:
        lines.insert(5, f"industry_mapping: {entry.industry_mapping}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sidecar 생성 (ollama 위임) — 청크 단위 요약 + 메타 요약
# ---------------------------------------------------------------------------

_CHUNK_MAX_CHARS  = 3_000  # 청크당 최대 문자
_CHUNK_MIN_CHARS  = 200    # 이 미만 청크는 요약 없이 원문 그대로
_MAX_CHUNKS       = 20     # 논문당 최대 청크 수 (초과분은 앞부분 우선)


def _split_sections_simple(md_text: str) -> List[Dict]:
    """H1-H3 경계로 섹션 분할. step_preprocess의 경량 버전."""
    import re
    heading_re = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    sections = []
    last_end = 0
    last_heading = "(preamble)"

    for m in heading_re.finditer(md_text):
        content = md_text[last_end:m.start()].strip()
        if content:
            sections.append({"heading": last_heading, "content": content})
        last_heading = m.group(2).strip()
        last_end = m.end()

    tail = md_text[last_end:].strip()
    if tail:
        sections.append({"heading": last_heading, "content": tail})
    return sections


def _make_chunks(sections: List[Dict]) -> List[Dict]:
    """섹션 목록을 _CHUNK_MAX_CHARS 이하 청크로 분할. _MAX_CHUNKS 초과 시 앞부분 우선."""
    chunks = []
    for sec in sections:
        content = sec["content"]
        if len(content) <= _CHUNK_MAX_CHARS:
            chunks.append({
                "heading": sec["heading"],
                "content": content,
                "idx": len(chunks),
            })
        else:
            parts = [
                content[i:i + _CHUNK_MAX_CHARS]
                for i in range(0, len(content), _CHUNK_MAX_CHARS)
            ]
            for j, part in enumerate(parts):
                chunks.append({
                    "heading": f"{sec['heading']} ({j + 1}/{len(parts)})",
                    "content": part,
                    "idx": len(chunks),
                })

    if len(chunks) > _MAX_CHUNKS:
        skipped = len(chunks) - _MAX_CHUNKS
        print(f"  [sidecar] 청크 {len(chunks)}개 → {_MAX_CHUNKS}개 제한 ({skipped}개 스킵)")
        chunks = chunks[:_MAX_CHUNKS]
        for i, c in enumerate(chunks):
            c["idx"] = i
    return chunks


def generate_sidecar(
    doc_id: str,
    body_md: str,
    raw_dir: Path,
    model: str = "gemma4:e4b",
) -> Dict:
    """PDF 변환 후 sidecar 파일 생성.

    산출물 (raw_dir 기준):
      {doc_id}-overview.md          — 메타 요약 (요약들의 요약)
      {doc_id}.concepts.jsonl       — 개념 목록
      splited/{idx:03d}.{doc_id}-overview.md — 청크별 요약
      chunked/{idx:03d}.{doc_id}.md          — 청크 원문

    (a) ollama HTTP 직접 → 위 파일 모두 생성
    (b) ollama 미실행   → .sidecar_pending.json 기록 (Claude MCP fallback 신호)

    Returns:
        {"status": "ok"|"pending", "files": [...]}
    """
    from ralph.ollama_http import (
        OllamaUnavailableError,
        extract_concepts,
        is_available,
        summarize_text,
    )

    overview_path = raw_dir / f"{doc_id}-overview.md"
    concepts_path = raw_dir / f"{doc_id}.concepts.jsonl"
    pending_path  = raw_dir / f"{doc_id}.sidecar_pending.json"
    splited_dir   = raw_dir / "splited"
    chunked_dir   = raw_dir / "chunked"

    # 이미 완성된 경우 skip
    if overview_path.exists() and concepts_path.exists():
        return {"status": "ok", "files": [str(overview_path), str(concepts_path)]}

    if not is_available():
        return _write_pending(doc_id, body_md, raw_dir, pending_path, model, "ollama unavailable")

    splited_dir.mkdir(exist_ok=True)
    chunked_dir.mkdir(exist_ok=True)

    sections = _split_sections_simple(body_md)
    chunks   = _make_chunks(sections)

    # ── 1. 청크별 요약 + 원문 저장 ──────────────────────────────────────────
    chunk_summaries: List[str] = []
    ok_count = 0

    for chunk in chunks:
        idx_str = f"{chunk['idx']:03d}"
        heading = chunk["heading"]
        content = chunk["content"]

        # 청크 원문 → chunked/
        (chunked_dir / f"{idx_str}.{doc_id}.md").write_text(
            f"# {heading}\n\n{content}\n", encoding="utf-8"
        )

        # 청크 요약 → splited/
        if len(content) >= _CHUNK_MIN_CHARS:
            try:
                summary = summarize_text(content, heading, model)
                ok_count += 1
            except OllamaUnavailableError:
                summary = content[:300] + ("..." if len(content) > 300 else "")
        else:
            summary = content  # 짧으면 원문 그대로

        chunk_summaries.append(f"## {heading}\n\n{summary}")
        (splited_dir / f"{idx_str}.{doc_id}-overview.md").write_text(
            f"# {heading}\n\n{summary}\n", encoding="utf-8"
        )

    # ── 2. 메타 요약 (요약들의 요약) ────────────────────────────────────────
    all_summaries_text = "\n\n---\n\n".join(chunk_summaries)
    try:
        meta = summarize_text(
            all_summaries_text,
            f"Overview of {doc_id}",
            model,
            max_input_chars=8_000,
        )
    except OllamaUnavailableError:
        meta = all_summaries_text[:800] + "..."

    overview_md = (
        f"---\ndoc_id: {doc_id}\ngenerated_by: ollama/{model}\n"
        f"chunks: {len(chunks)}\n---\n\n"
        f"# Overview: {doc_id}\n\n{meta}\n\n"
        f"---\n\n## Section Summaries\n\n{all_summaries_text}\n"
    )
    overview_path.write_text(overview_md, encoding="utf-8")

    # ── 3. 개념 추출 ────────────────────────────────────────────────────────
    try:
        concepts = extract_concepts(body_md, model)
    except OllamaUnavailableError:
        concepts = []

    with concepts_path.open("w", encoding="utf-8") as f:
        for item in concepts:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    pending_path.unlink(missing_ok=True)

    print(
        f"  [sidecar:ok] {doc_id} — "
        f"{len(chunks)} chunks ({ok_count} summarized), {len(concepts)} concepts"
    )
    return {"status": "ok", "files": [str(overview_path), str(concepts_path)]}


def _write_pending(
    doc_id: str,
    body_md: str,
    raw_dir: Path,
    pending_path: Path,
    model: str,
    reason: str,
) -> Dict:
    pending = {
        "doc_id": doc_id,
        "md_path": str(raw_dir / f"{doc_id}.md"),
        "pending": ["overview", "concepts"],
        "model": model,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reason": reason,
        "mcp_tools": {"overview": "ollama_summarize", "concepts": "ollama_extract_concepts"},
    }
    pending_path.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [sidecar:pending] {doc_id} → {pending_path.name} (Claude MCP fallback 필요)")
    return {"status": "pending", "files": [str(pending_path)]}
