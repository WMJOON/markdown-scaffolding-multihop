"""ralph archive → KB evidence 폴더 publish.

archive/history/ralph-runs/{run_id}/evidence_corpus/raw/ 의 sidecar 결과물을
KB evidence 폴더에 아래 구조로 복사한다:

  evidence/[수집일]_[doc-name]/
  ├── [doc-name]-overview.md          # 메타 요약
  ├── [doc-name].concepts.jsonl       # 개념 목록
  ├── splited/
  │   └── [chunk-id].[doc-name]-overview.md
  ├── raw/
  │   ├── [doc-name].pdf
  │   └── [doc-name].md
  └── chunked/
      └── [chunk-id].[doc-name].md

사용:
  python3 publish_evidence.py --run-id R-20260424-0002 \\
      --evidence-dir /path/to/KB/evidence/

  또는 ralph_cli.py publish 서브커맨드로 호출.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import date
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _doc_name_from_id(doc_id: str) -> str:
    """paper__mteb_2210_07316 → mteb-2210-07316"""
    name = re.sub(r"^(paper|report|doc)__", "", doc_id)
    return name.replace("_", "-")


def _collect_date(raw_dir: Path, doc_id: str) -> str:
    """MD frontmatter의 fetched_at에서 날짜 추출. 없으면 오늘."""
    md_path = raw_dir / f"{doc_id}.md"
    if md_path.exists():
        for line in md_path.read_text(encoding="utf-8").splitlines()[:15]:
            if line.startswith("fetched_at:"):
                val = line.split(":", 1)[1].strip()
                return val[:10]  # YYYY-MM-DD
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# 단일 문서 publish
# ---------------------------------------------------------------------------

def publish_doc(
    doc_id: str,
    run_raw_dir: Path,
    evidence_dir: Path,
    overwrite: bool = False,
) -> Optional[Path]:
    """단일 doc_id를 evidence_dir 하위에 publish.

    Returns: 생성된 문서 디렉토리 경로, 또는 None(스킵).
    """
    doc_name   = _doc_name_from_id(doc_id)
    collect_dt = _collect_date(run_raw_dir, doc_id)
    dest_dir   = evidence_dir / f"{collect_dt}_{doc_name}"

    if dest_dir.exists() and not overwrite:
        print(f"  [skip] {dest_dir.name} 이미 존재 (--overwrite로 덮어쓰기)")
        return None

    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "raw").mkdir(exist_ok=True)
    (dest_dir / "splited").mkdir(exist_ok=True)
    (dest_dir / "chunked").mkdir(exist_ok=True)

    copied: List[str] = []

    # ── overview.md ─────────────────────────────────────────────────────────
    src_overview = run_raw_dir / f"{doc_id}-overview.md"
    if src_overview.exists():
        shutil.copy2(src_overview, dest_dir / f"{doc_name}-overview.md")
        copied.append("overview")

    # ── concepts.jsonl ──────────────────────────────────────────────────────
    src_concepts = run_raw_dir / f"{doc_id}.concepts.jsonl"
    if src_concepts.exists():
        shutil.copy2(src_concepts, dest_dir / f"{doc_name}.concepts.jsonl")
        copied.append("concepts")

    # ── raw/ (원문 MD + PDF) ─────────────────────────────────────────────────
    for ext in (".md", ".pdf"):
        src = run_raw_dir / f"{doc_id}{ext}"
        if src.exists():
            shutil.copy2(src, dest_dir / "raw" / f"{doc_name}{ext}")
            copied.append(f"raw/{doc_name}{ext}")

    # ── splited/ ─────────────────────────────────────────────────────────────
    src_splited = run_raw_dir / "splited"
    if src_splited.exists():
        for f in sorted(src_splited.glob(f"*.{doc_id}-overview.md")):
            dest_name = f.name.replace(doc_id, doc_name)
            shutil.copy2(f, dest_dir / "splited" / dest_name)
            copied.append(f"splited/{dest_name}")

    # ── chunked/ ─────────────────────────────────────────────────────────────
    src_chunked = run_raw_dir / "chunked"
    if src_chunked.exists():
        for f in sorted(src_chunked.glob(f"*.{doc_id}.md")):
            dest_name = f.name.replace(doc_id, doc_name)
            shutil.copy2(f, dest_dir / "chunked" / dest_name)
            copied.append(f"chunked/{dest_name}")

    # ── sidecar_pending → pending.json 그대로 복사 (미완 신호) ───────────────
    src_pending = run_raw_dir / f"{doc_id}.sidecar_pending.json"
    if src_pending.exists():
        shutil.copy2(src_pending, dest_dir / "sidecar_pending.json")
        copied.append("sidecar_pending.json")

    status = "ok" if "overview" in copied else "partial"
    print(f"  [{status}] {dest_dir.name} — {len(copied)} files")
    return dest_dir


# ---------------------------------------------------------------------------
# run 단위 publish
# ---------------------------------------------------------------------------

def publish_run(
    run_id: str,
    runs_archive_dir: Path,
    evidence_dir: Path,
    overwrite: bool = False,
) -> List[Path]:
    """run의 모든 문서를 evidence_dir에 publish.

    Returns: 생성된 문서 디렉토리 목록.
    """
    run_dir  = runs_archive_dir / run_id
    raw_dir  = run_dir / "evidence_corpus" / "raw"

    if not raw_dir.exists():
        raise FileNotFoundError(f"raw dir 없음: {raw_dir}")

    # doc_id 수집: .md 파일 stem (보조 파일 제외)
    doc_ids = sorted({
        p.stem for p in raw_dir.glob("*.md")
        if not p.stem.endswith("-overview")
        and not p.stem.endswith(".sidecar_pending")
    })

    if not doc_ids:
        print(f"[Publish] {run_id}: 발행할 문서 없음")
        return []

    print(f"[Publish] {run_id}: {len(doc_ids)}개 문서 → {evidence_dir}")
    published = []
    for doc_id in doc_ids:
        dest = publish_doc(doc_id, raw_dir, evidence_dir, overwrite=overwrite)
        if dest:
            published.append(dest)

    print(f"[Publish] 완료: {len(published)}/{len(doc_ids)} 발행")
    return published


# ---------------------------------------------------------------------------
# CLI (직접 실행 시)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="ralph archive → KB evidence publish")
    p.add_argument("--run-id", required=True)
    p.add_argument("--evidence-dir", required=True, help="KB evidence 폴더 경로")
    p.add_argument("--archive-dir", default="archive/history/ralph-runs",
                   help="ralph-runs 아카이브 루트 (기본: archive/history/ralph-runs)")
    p.add_argument("--overwrite", action="store_true", help="기존 디렉토리 덮어쓰기")
    args = p.parse_args()

    publish_run(
        run_id=args.run_id,
        runs_archive_dir=Path(args.archive_dir),
        evidence_dir=Path(args.evidence_dir),
        overwrite=args.overwrite,
    )
