"""Step B — Crawl: fetch raw HTML, convert to markdown, extract minimal index.

No LLM calls allowed. Wraps existing collect_case_study_raw_data.py functions.
"""
from __future__ import annotations

import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from ralph.common import DocIndex, RunConfig, RunState, URLEntry
from ralph.yaml_io import dump_yaml, load_yaml, read_jsonl, write_jsonl


def _import_crawl_tools():
    """Import functions from existing crawl module."""
    import collect_case_study_raw_data as ccsrd
    return ccsrd


def parse_headings(md_text: str) -> List[str]:
    """Extract heading lines from markdown."""
    headings = []
    for line in md_text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            headings.append(f"H{level}: {text}")
    return headings


def extract_outbound_links(md_text: str) -> List[str]:
    """Extract HTTP(S) links from markdown."""
    links = re.findall(r"https?://[^\s\)>\]]+", md_text)
    return list(dict.fromkeys(links))  # deduplicate, preserve order


def build_doc_index(
    doc_id: str,
    title: str,
    md_text: str,
    source_type: str,
) -> DocIndex:
    """Build a minimal document index from crawled content."""
    headings = parse_headings(md_text)
    links = extract_outbound_links(md_text)
    return DocIndex(
        doc_id=doc_id,
        title=title,
        organization="",
        date="",
        headings=headings,
        doc_type=source_type,
        length=len(md_text),
        outbound_links=links[:50],  # cap at 50
    )


def _load_intake_entries(run_dir: Path) -> List[URLEntry]:
    """Load active entries from intake_manifest.yaml."""
    manifest_path = run_dir / "intake_manifest.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Intake manifest not found: {manifest_path}")

    d = load_yaml(manifest_path.read_text(encoding="utf-8"))
    intake = d.get("intake_manifest", d)
    raw_entries = intake.get("entries", [])

    entries = []
    for e in raw_entries:
        if e.get("skip_reason"):
            continue
        entries.append(URLEntry(
            url=str(e.get("url", "")),
            normalized_url=str(e.get("normalized_url", "")),
            url_fingerprint=str(e.get("url_fingerprint", "")),
            source_type=str(e.get("source_type", "")),
            case_id=str(e.get("case_id", "")),
            title=str(e.get("title", "")),
            industry_mapping=str(e.get("industry_mapping", "")),
            start_marker=str(e.get("start_marker", "")),
        ))
    return entries


# ---------------------------------------------------------------------------
# Step handler
# ---------------------------------------------------------------------------

def run_crawl(
    root: Path,
    state: RunState,
    config: RunConfig,
    run_dir: Path,
    apply: bool,
) -> RunState:
    """Step B: Crawl — fetch, convert, index."""
    entries = _load_intake_entries(run_dir)
    if not entries:
        print("[Ralph] Crawl: no active entries to process")
        return state

    ccsrd = _import_crawl_tools()

    corpus_dir = run_dir / "evidence_corpus"
    raw_dir = corpus_dir / "raw"
    index_dir = corpus_dir / "index"
    raw_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = 0
    doc_indexes: List[Dict] = []

    for entry in entries:
        doc_id = entry.case_id
        md_path = raw_dir / f"{doc_id}.md"
        html_path = raw_dir / f"{doc_id}.html"

        # handle local files (file:// URLs from local/directory mode)
        if entry.normalized_url.startswith("file://"):
            local_src = Path(entry.normalized_url[7:])
            if local_src.exists() and not md_path.exists():
                import shutil
                shutil.copy2(local_src, md_path)
                print(f"  [local] {doc_id}")
            md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
            if md_text:
                idx = build_doc_index(doc_id, entry.title, md_text, entry.source_type)
                from dataclasses import asdict
                doc_indexes.append(asdict(idx))
                success += 1
            continue

        # skip if already crawled (idempotency)
        if md_path.exists() and html_path.exists():
            print(f"  [cached] {doc_id}")
            # still build index
            md_text = md_path.read_text(encoding="utf-8")
            idx = build_doc_index(doc_id, entry.title, md_text, entry.source_type)
            from dataclasses import asdict
            doc_indexes.append(asdict(idx))
            success += 1
            continue

        if not apply:
            print(f"  [dry-run] would fetch: {entry.url}")
            success += 1
            continue

        try:
            # fetch
            status_code, resolved_url, html_body = ccsrd.fetch_html(
                entry.url, config.http_timeout
            )
            if status_code >= 400:
                print(f"  [skip] {doc_id}: HTTP {status_code}")
                failed += 1
                continue

            # save HTML
            html_path.write_text(html_body, encoding="utf-8")

            # convert to markdown via pandoc
            md_text = ccsrd.pandoc_to_markdown(html_path)
            md_text = ccsrd.clean_markdown(md_text, entry.start_marker)

            # write markdown with frontmatter
            fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            html_rel = str(html_path.relative_to(run_dir))
            full_md = ccsrd.write_markdown(
                ccsrd.SourceItem(
                    case_id=entry.case_id,
                    source_type=entry.source_type,
                    industry_mapping=entry.industry_mapping,
                    title=entry.title,
                    url=entry.url,
                    start_marker=entry.start_marker,
                ),
                html_rel,
                entry.url,
                resolved_url,
                status_code,
                fetched_at,
                md_text,
            )
            md_path.write_text(full_md, encoding="utf-8")

            # build index
            idx = build_doc_index(doc_id, entry.title, md_text, entry.source_type)
            from dataclasses import asdict
            idx_dict = asdict(idx)
            doc_indexes.append(idx_dict)

            idx_path = index_dir / f"{doc_id}.yaml"
            idx_path.write_text(dump_yaml(idx_dict), encoding="utf-8")

            print(f"  [ok] {doc_id} ({len(md_text)} chars)")
            success += 1

        except Exception as exc:
            print(f"  [error] {doc_id}: {exc}")
            failed += 1

    # write consolidated index
    if doc_indexes:
        write_jsonl(index_dir / "doc_index.jsonl", doc_indexes)

    print(f"[Ralph] Crawl: {success} ok, {failed} failed")
    return state
