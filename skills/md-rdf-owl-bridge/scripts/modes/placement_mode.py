"""
Mode C: Ralph ETL placement_report.jsonl 보강

동작:
  1. placement_report.jsonl + entity_candidates.jsonl 로드
  2. 기존 MD 엔티티 → TripleGraph 구축
  3. TF-IDF (또는 PyKEEN) Embedder fit
  4. embed_sim == 0.0 인 항목에 대해 유사도 재계산
  5. merge_candidate + embed_sim >= threshold → label: merge 승격
  6. 업데이트된 placement_report.jsonl 저장

입력 구조:
  placement_report.jsonl
    {candidate_id, label, target_existing_id, alias_sim, embed_sim,
     evidence_count, conflict_layer, reason}

  entity_candidates.jsonl
    {candidate_id, entity_id, entity_type, label_en, label_ko,
     aliases, confidence, relations, ...}
"""
from __future__ import annotations

import logging
from pathlib import Path
from datetime import date

from core.triple_graph import TripleGraph
from core.md_to_triple import load_entity_dir, entity_feature_dict
from core.jsonl_io import load_jsonl as _load_jsonl, save_jsonl as _save_jsonl

logger = logging.getLogger(__name__)

# merge 승격 대상 label
_PROMOTABLE = {"merge_candidate"}
# embed_sim 재계산 대상 label (embed_sim == 0.0 인 것들)
_RECALC_LABELS = {"merge_candidate", "merge", "extend", "new"}


# ─── 진입점 ───────────────────────────────────────────────────────────────────

def run_placement(
    input_path:  Path,
    output:      str | None,
    candidates:  str | None,
    use_embed:   bool,
    embed_model: str,
    threshold:   float,
    entity_dir:  str | None,
):
    logger.info("[Mode C] Placement 보강 시작: %s", input_path)
    print(f"[Mode C] 입력: {input_path}")
    print(f"[Mode C] merge 승격 임계값: {threshold}")

    # ── placement_report 로드 ─────────────────────────────────────────────────
    placement_records = _load_jsonl(input_path)
    print(f"[Mode C] placement_report: {len(placement_records)}건")

    # ── entity_candidates 로드 ────────────────────────────────────────────────
    cand_path = _resolve_candidates_path(input_path, candidates)
    if cand_path and cand_path.exists():
        cand_records = {r["candidate_id"]: r for r in _load_jsonl(cand_path)}
        print(f"[Mode C] entity_candidates: {len(cand_records)}건")
    else:
        cand_records = {}
        logger.warning("[Mode C] entity_candidates.jsonl 없음 — feature_text를 label_en만으로 구성")

    # ── 기존 엔티티 TripleGraph 구축 ──────────────────────────────────────────
    entity_root = _resolve_entity_dir(input_path, entity_dir)
    graph       = TripleGraph()
    if entity_root and entity_root.is_dir():
        n = load_entity_dir(entity_root, graph)
        print(f"[Mode C] 기존 엔티티 로드: {n}개 from {entity_root}")
    else:
        logger.warning("[Mode C] 엔티티 디렉토리 없음 — embed_sim 재계산 불가")

    # ── Embedder fit ──────────────────────────────────────────────────────────
    embedder = None
    if len(graph) > 0:
        from embed.kg_embed import build_embedder
        actual_model = embed_model if use_embed else "tfidf"
        try:
            embedder = build_embedder(actual_model, graph)  # type: ignore
            print(f"[Mode C] Embedder 준비 완료 ({type(embedder).__name__})")
        except Exception as e:
            logger.error("[Mode C] Embedder 실패: %s", e)
            print(f"[WARN] Embedder 실패, embed_sim 재계산 건너뜀: {e}")

    # ── 유사도 재계산 + 승격 ──────────────────────────────────────────────────
    stats = {"recalc": 0, "promoted": 0, "skipped": 0}

    for rec in placement_records:
        label          = rec.get("label", "")
        target_id      = rec.get("target_existing_id")
        try:
            current_embed = float(rec.get("embed_sim") or 0.0)
        except (TypeError, ValueError):
            current_embed = 0.0
        candidate_id   = rec.get("candidate_id", "")

        if label not in _RECALC_LABELS:
            stats["skipped"] += 1
            continue

        # embed_sim 이미 계산된 경우 (> 0) 는 건너뜀
        if current_embed > 0.0:
            stats["skipped"] += 1
            continue

        if embedder is None or not target_id:
            stats["skipped"] += 1
            continue

        # candidate feature text 구성
        feature_text = _build_candidate_feature(candidate_id, cand_records)
        if not feature_text:
            stats["skipped"] += 1
            continue

        # candidate 관계 정보 추출 (hybrid/PyKEEN inductive embed용)
        cand_rels = _extract_candidate_relations(candidate_id, cand_records)

        # 유사도 계산
        from embed.kg_embed import compute_similarity
        try:
            sim = compute_similarity(
                feature_text, target_id, embedder, graph, cand_rels,
            )
        except Exception as e:
            logger.debug("[Mode C] 유사도 계산 실패 %s: %s", candidate_id, e)
            sim = 0.0

        rec["embed_sim"] = round(sim, 6)
        stats["recalc"] += 1

        # merge_candidate → merge 승격
        if label in _PROMOTABLE and sim >= threshold:
            rec["label"]  = "merge"
            rec["reason"] = (
                f"{rec.get('reason', '')} [rdf-bridge: embed_sim={sim:.4f} >= {threshold}]"
            ).strip()
            stats["promoted"] += 1

    print(
        f"[Mode C] embed_sim 재계산: {stats['recalc']}건 "
        f"/ merge 승격: {stats['promoted']}건 "
        f"/ 건너뜀: {stats['skipped']}건"
    )

    # ── 출력 저장 ─────────────────────────────────────────────────────────────
    out_path = _resolve_output_path(input_path, output)
    _save_jsonl(placement_records, out_path)
    print(f"[Mode C] 저장 완료: {out_path}")

    # ── 요약 리포트 ───────────────────────────────────────────────────────────
    _write_summary(placement_records, stats, out_path.parent, threshold)


# ─── 헬퍼 함수 ────────────────────────────────────────────────────────────────

def _build_candidate_feature(
    candidate_id: str,
    cand_records: dict[str, dict],
) -> str:
    """entity_candidates 에서 candidate의 feature_text 구성."""
    rec = cand_records.get(candidate_id)
    if not rec:
        return ""

    aliases = rec.get("aliases", [])
    if not isinstance(aliases, list):
        aliases = []
    parts = [
        rec.get("entity_type", ""),
        rec.get("label_en", ""),
        rec.get("label_ko", ""),
        *aliases,
        *[f"{r.get('type','')} {r.get('target','')}"
          for r in (rec.get("relations") or [])],
    ]
    return " ".join(p for p in parts if p).strip()


def _extract_candidate_relations(
    candidate_id: str,
    cand_records: dict[str, dict],
) -> list[tuple[str, str]] | None:
    """entity_candidates에서 candidate의 관계 목록을 추출 (inductive embed용)."""
    rec = cand_records.get(candidate_id)
    if not rec:
        return None
    relations = rec.get("relations")
    if not relations or not isinstance(relations, list):
        return None
    result = []
    for r in relations:
        rel_type = r.get("type", "")
        target   = r.get("target", "")
        if rel_type and target:
            result.append((rel_type, target))
    return result if result else None


def _resolve_candidates_path(
    placement_path: Path,
    explicit:       str | None,
) -> Path | None:
    if explicit:
        return Path(explicit)
    # 같은 디렉토리에 entity_candidates.jsonl 찾기
    candidate = placement_path.parent / "entity_candidates.jsonl"
    return candidate if candidate.exists() else None


def _resolve_entity_dir(
    placement_path: Path,
    entity_dir:     str | None,
) -> Path | None:
    if entity_dir:
        return Path(entity_dir)

    # 자동 탐색: ralph-run 디렉토리에서 상위로 거슬러 올라가기
    search = placement_path.parent
    for _ in range(6):
        candidate = search / "data" / "ontology-entities"
        if candidate.is_dir():
            return candidate
        candidate2 = search / "01_ontology-data" / "data" / "ontology-entities"
        if candidate2.is_dir():
            return candidate2
        search = search.parent

    return None


def _resolve_output_path(input_path: Path, output: str | None) -> Path:
    if output:
        return Path(output)
    # 원본과 같은 위치에 _enriched 접미사
    stem = input_path.stem
    return input_path.parent / f"{stem}_enriched.jsonl"


def _write_summary(
    records:   list[dict],
    stats:     dict,
    out_dir:   Path,
    threshold: float,
):
    from collections import Counter
    label_count = Counter(r.get("label") for r in records)
    today       = date.today().isoformat()

    lines = [
        "# Mode C — Placement 보강 리포트",
        "",
        f"> 생성일: {today}  |  merge 임계값: {threshold}",
        "",
        "## 처리 결과",
        "",
        f"| 항목 | 수 |",
        f"|---|---|",
        f"| embed_sim 재계산 | {stats['recalc']} |",
        f"| merge 승격 | {stats['promoted']} |",
        f"| 건너뜀 | {stats['skipped']} |",
        f"| 전체 | {len(records)} |",
        "",
        "## label 분포 (보강 후)",
        "",
        "| label | 수 |",
        "|---|---|",
    ]
    for label, cnt in label_count.most_common():
        lines.append(f"| {label} | {cnt} |")

    lines += [
        "",
        "## embed_sim 분포 (재계산된 항목)",
        "",
    ]
    recalc_sims = [
        r["embed_sim"] for r in records
        if float(r.get("embed_sim") or 0.0) > 0.0
    ]
    if recalc_sims:
        import statistics
        lines.append(f"- 최소: {min(recalc_sims):.4f}")
        lines.append(f"- 최대: {max(recalc_sims):.4f}")
        lines.append(f"- 평균: {statistics.mean(recalc_sims):.4f}")
        lines.append(f"- 중앙값: {statistics.median(recalc_sims):.4f}")
    else:
        lines.append("- 재계산된 embed_sim 없음")

    report_path = out_dir / "placement_enrichment_report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[Mode C] 리포트: {report_path}")
