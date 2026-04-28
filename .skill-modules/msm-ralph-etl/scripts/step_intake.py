"""Step A — Intake: multi-format input loading, normalization, batch creation.

Supports:
  - TSV manifest (기존 case-study-source-manifest.tsv 호환)
  - JSONL manifest (범용: url, title, source_type, tags 등)
  - Local directory scan (로컬 .md/.txt/.html 파일)

No LLM calls allowed in this step.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from ralph.common import RunConfig, RunState, URLEntry
from ralph.yaml_io import dump_yaml

# Tracking query params to strip
_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid",
    "ref", "ref_src", "ref_url",
})


# ---------------------------------------------------------------------------
# URL normalization (shared across all modes)
# ---------------------------------------------------------------------------

def normalize_url(url: str, preserve_fragment: bool = False) -> str:
    """Normalize a URL per v0.0.3 rules."""
    p = urlparse(url)
    scheme = "https"
    netloc = p.netloc.lower()
    path = p.path.rstrip("/") if p.path != "/" else ""
    qs = parse_qs(p.query, keep_blank_values=True)
    qs_clean = {k: v for k, v in qs.items() if k.lower() not in _TRACKING_PARAMS}
    query = urlencode(qs_clean, doseq=True) if qs_clean else ""
    fragment = p.fragment if preserve_fragment else ""
    return urlunparse((scheme, netloc, path, "", query, fragment))


def compute_url_fingerprint(normalized_url: str) -> str:
    return "sha256:" + hashlib.sha256(
        normalized_url.encode("utf-8")
    ).hexdigest()


def compute_path_fingerprint(file_path: Path) -> str:
    return "sha256:" + hashlib.sha256(
        str(file_path.resolve()).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Input loaders — one per format
# ---------------------------------------------------------------------------

def _load_tsv_entries(manifest_path: Path) -> List[Dict]:
    """Load TSV manifest (existing case-study-source-manifest.tsv format)."""
    try:
        import collect_case_study_raw_data as ccsrd
        items = ccsrd.load_manifest(manifest_path)
        return [
            {
                "case_id": it.case_id,
                "source_type": it.source_type,
                "industry_mapping": it.industry_mapping,
                "title": it.title,
                "url": it.url,
                "start_marker": it.start_marker,
            }
            for it in items
        ]
    except ImportError:
        import csv
        entries = []
        with open(manifest_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                cid = (row.get("case_id") or "").strip()
                if not cid or cid.startswith("#"):
                    continue
                entries.append({
                    "case_id": cid,
                    "source_type": (row.get("source_type") or "paper").strip(),
                    "industry_mapping": (row.get("industry_mapping") or "").strip(),
                    "title": (row.get("title") or cid).strip(),
                    "url": (row.get("url") or "").strip(),
                    "start_marker": (row.get("start_marker") or "").strip(),
                })
        return entries


def _load_jsonl_entries(manifest_path: Path) -> List[Dict]:
    """Load JSONL manifest. Each line is a JSON object with at least 'url' or 'path'.

    Supported fields:
      url, title, source_type, case_id, tags, industry_mapping,
      start_marker, license_hint, priority, path (for local files)
    """
    entries = []
    with open(manifest_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            obj = json.loads(line)
            url = obj.get("url", "")
            local_path = obj.get("path", "")
            title = obj.get("title", "") or url or local_path
            case_id = obj.get("case_id", "")
            if not case_id:
                # auto-generate from title or url
                slug = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_").lower()[:60]
                case_id = f"doc__{slug}"
            entries.append({
                "case_id": case_id,
                "source_type": obj.get("source_type", "document"),
                "industry_mapping": obj.get("industry_mapping", ""),
                "title": title,
                "url": url,
                "start_marker": obj.get("start_marker", ""),
                "tags": obj.get("tags", []),
                "license_hint": obj.get("license_hint", ""),
                "priority": obj.get("priority", 0),
                "local_path": local_path,
            })
    return entries


def _load_directory_entries(input_dir: Path, extensions: List[str]) -> List[Dict]:
    """Scan a local directory for files matching extensions."""
    entries = []
    for ext in extensions:
        for file_path in sorted(input_dir.rglob(f"*{ext}")):
            if file_path.is_file():
                rel = file_path.relative_to(input_dir)
                slug = re.sub(r"[^a-zA-Z0-9]+", "_", rel.stem).strip("_").lower()[:60]
                entries.append({
                    "case_id": f"local__{slug}",
                    "source_type": ext.lstrip("."),
                    "industry_mapping": "",
                    "title": rel.stem.replace("_", " ").replace("-", " "),
                    "url": "",
                    "start_marker": "",
                    "local_path": str(file_path.resolve()),
                })
    return entries


def _detect_input_format(manifest_path: Path) -> str:
    """Auto-detect input format from file extension or content."""
    suffix = manifest_path.suffix.lower()
    if suffix == ".tsv":
        return "tsv"
    if suffix == ".jsonl":
        return "jsonl"
    if suffix == ".json":
        return "jsonl"
    if manifest_path.is_dir():
        return "directory"
    # peek at first line
    try:
        first_line = manifest_path.read_text(encoding="utf-8").split("\n", 1)[0]
        if first_line.strip().startswith("{"):
            return "jsonl"
    except Exception:
        pass
    return "tsv"


# ---------------------------------------------------------------------------
# Entry building (unified across all formats)
# ---------------------------------------------------------------------------

def build_entries(
    manifest_path: Path,
    root: Path,
    config: RunConfig,
) -> List[URLEntry]:
    """Load entries from any supported format, normalize, deduplicate."""
    input_format = config.input_format
    if input_format == "auto":
        input_format = _detect_input_format(manifest_path)

    if input_format == "directory":
        raw_entries = _load_directory_entries(manifest_path, config.file_extensions)
    elif input_format == "jsonl":
        raw_entries = _load_jsonl_entries(manifest_path)
    else:
        raw_entries = _load_tsv_entries(manifest_path)

    seen_fps: Dict[str, int] = {}
    entries: List[URLEntry] = []

    for raw in raw_entries:
        url = raw.get("url", "")
        local_path = raw.get("local_path", "")

        # compute fingerprint
        if url:
            has_frag = raw.get("start_marker", "").startswith("#")
            norm = normalize_url(url, preserve_fragment=has_frag)
            fp = compute_url_fingerprint(norm)
        elif local_path:
            norm = f"file://{local_path}"
            fp = compute_path_fingerprint(Path(local_path))
        else:
            continue

        if fp in seen_fps:
            continue
        seen_fps[fp] = len(entries)

        entries.append(URLEntry(
            url=url or norm,
            normalized_url=norm,
            url_fingerprint=fp,
            source_type=raw.get("source_type", "document"),
            case_id=raw.get("case_id", ""),
            title=raw.get("title", ""),
            industry_mapping=raw.get("industry_mapping", ""),
            start_marker=raw.get("start_marker", ""),
            tags=raw.get("tags", []),
            license_hint=raw.get("license_hint", ""),
            priority=raw.get("priority", 0),
            collected_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        ))

    # apply batch_size limit
    active = [e for e in entries if e.skip_reason is None]
    if len(active) > config.batch_size:
        for e in active[config.batch_size:]:
            e.skip_reason = "batch_size_exceeded"

    return entries


def _entries_to_dict(entries: List[URLEntry]) -> Dict:
    from dataclasses import asdict
    return {
        "intake_manifest": {
            "total": len(entries),
            "active": sum(1 for e in entries if e.skip_reason is None),
            "skipped": sum(1 for e in entries if e.skip_reason is not None),
            "entries": [asdict(e) for e in entries],
        }
    }


# ---------------------------------------------------------------------------
# Step handler
# ---------------------------------------------------------------------------

def run_intake(
    root: Path,
    state: RunState,
    config: RunConfig,
    run_dir: Path,
    apply: bool,
) -> RunState:
    """Step A: Intake — multi-format input loading."""
    mp_file = run_dir / ".manifest_path"
    if mp_file.exists():
        manifest_path = Path(mp_file.read_text(encoding="utf-8").strip())
    else:
        manifest_path = root / "data/raw-data/case-study/case-study-source-manifest.tsv"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest/input not found: {manifest_path}")

    entries = build_entries(manifest_path, root, config)

    active_entries = [e for e in entries if e.skip_reason is None]
    if state.batch:
        state.batch.urls = [e.url for e in active_entries]
        state.batch.url_fingerprints = [e.url_fingerprint for e in active_entries]

    # scope targets: user-specified or auto-detected
    if config.scope_targets:
        scope_targets = list(config.scope_targets)
    else:
        scope_targets = []
        for e in active_entries:
            if e.source_type in ("paper", "report", "tech_blog"):
                if "CaseStudy" not in scope_targets:
                    scope_targets.append("CaseStudy")
            elif e.source_type in ("model_card", "model_doc"):
                if "Model" not in scope_targets:
                    scope_targets.append("Model")
            elif e.source_type in ("api_doc", "spec"):
                if "Work" not in scope_targets:
                    scope_targets.append("Work")
        if not scope_targets:
            scope_targets = ["CaseStudy"]

    if state.batch:
        state.batch.scope_targets = scope_targets

    manifest_out = run_dir / "intake_manifest.yaml"
    content = dump_yaml(_entries_to_dict(entries))
    manifest_out.write_text(content, encoding="utf-8")

    # store run mode and input format for downstream steps
    meta = {
        "run_mode": config.run_mode,
        "input_format": config.input_format,
        "scope_targets": scope_targets,
    }
    (run_dir / ".run_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8"
    )

    n_active = len(active_entries)
    n_skip = len(entries) - n_active
    mode_label = config.run_mode.upper()
    print(f"[Ralph] Intake ({mode_label}): {n_active} active, {n_skip} skipped, "
          f"targets={scope_targets}")
    return state
