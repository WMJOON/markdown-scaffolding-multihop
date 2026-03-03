"""Step E — Graph Placement: 3-tier similarity judgment.

Tier 1: Lexical (Levenshtein) for merge/extend filtering
Tier 2: Sparse Semantic (TF-IDF cosine) — fallback
Tier 3: Dense Semantic (BERT) — opt-in via --embed-mode bert|auto

No LLM auto-merge allowed. Ambiguous cases → hold.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from ralph.common import (
    HoldEntry,
    PlacementLabel,
    PlacementResult,
    RunConfig,
    RunState,
)
from ralph.similarity import SimilarityEngine, alias_similarity
from ralph.step_parse import load_existing_entities
from ralph.yaml_io import dump_yaml, read_jsonl, write_jsonl


def _build_label_list(entity: Dict) -> List[str]:
    """Build all labels for comparison."""
    labels = []
    if entity.get("label_en"):
        labels.append(entity["label_en"])
    if entity.get("label_ko"):
        labels.append(entity["label_ko"])
    labels.extend(entity.get("aliases", []))
    eid = entity.get("entity_id", "")
    if "__" in eid:
        slug = eid.split("__", 1)[1].replace("_", " ")
        labels.append(slug)
    return labels


def place_entity(
    candidate: Dict,
    existing_entities: Dict[str, Dict],
    sim_engine: SimilarityEngine,
    config: RunConfig,
) -> PlacementResult:
    """Apply placement decision tree (v0.0.3 Section 7.2)."""
    cand_id = candidate.get("candidate_id", "")
    cand_eid = candidate.get("entity_id", "")
    cand_type = candidate.get("entity_type", "")
    evidence_spans = candidate.get("evidence_spans", [])

    # 1. Check evidence
    if not evidence_spans:
        return PlacementResult(
            candidate_id=cand_id,
            label=PlacementLabel.REJECT.value,
            reason="no evidence spans",
        )

    cand_labels = _build_label_list(candidate)

    # 2. Find best alias match among same-type entities
    best_alias_sim = 0.0
    best_match_id: Optional[str] = None

    for eid, einfo in existing_entities.items():
        if einfo.get("entity_type") != cand_type:
            continue
        existing_labels = _build_label_list({"entity_id": eid, **einfo})
        sim = alias_similarity(cand_labels, existing_labels)
        if sim > best_alias_sim:
            best_alias_sim = sim
            best_match_id = eid

    # 3. Merge threshold
    if best_alias_sim >= config.merge_alias_sim_threshold and best_match_id:
        return PlacementResult(
            candidate_id=cand_id,
            label=PlacementLabel.MERGE_CANDIDATE.value,
            target_existing_id=best_match_id,
            alias_sim=best_alias_sim,
            evidence_count=len(evidence_spans),
            reason=f"alias_sim {best_alias_sim:.3f} >= {config.merge_alias_sim_threshold}",
        )

    # 4. Extend threshold
    if best_alias_sim >= config.extend_alias_sim_threshold and best_match_id:
        return PlacementResult(
            candidate_id=cand_id,
            label=PlacementLabel.EXTEND.value,
            target_existing_id=best_match_id,
            alias_sim=best_alias_sim,
            evidence_count=len(evidence_spans),
            reason=f"alias_sim {best_alias_sim:.3f} >= {config.extend_alias_sim_threshold}",
        )

    # 5. Semantic similarity for relation-only (BERT or TF-IDF)
    if best_match_id:
        cand_text = " ".join(cand_labels)
        existing_text = " ".join(
            _build_label_list({"entity_id": best_match_id,
                               **existing_entities[best_match_id]})
        )
        existing_summary = existing_entities[best_match_id].get("summary", "")
        if existing_summary:
            existing_text += " " + existing_summary

        embed_sim = sim_engine.compute_similarity(cand_text, existing_text)

        if (embed_sim >= config.relation_embed_sim_threshold
                and best_alias_sim < config.extend_alias_sim_threshold):
            return PlacementResult(
                candidate_id=cand_id,
                label=PlacementLabel.RELATION_ONLY.value,
                target_existing_id=best_match_id,
                alias_sim=best_alias_sim,
                embed_sim=embed_sim,
                evidence_count=len(evidence_spans),
                reason=f"embed_sim {embed_sim:.3f} >= {config.relation_embed_sim_threshold}",
            )

    # 6. Check ambiguity (simplified: if multiple close matches exist)
    close_matches = sum(
        1 for eid, einfo in existing_entities.items()
        if einfo.get("entity_type") == cand_type
        and alias_similarity(cand_labels, _build_label_list({"entity_id": eid, **einfo}))
        >= config.extend_alias_sim_threshold * 0.9
    )
    if close_matches > 1:
        return PlacementResult(
            candidate_id=cand_id,
            label=PlacementLabel.HOLD.value,
            alias_sim=best_alias_sim,
            evidence_count=len(evidence_spans),
            reason=f"ambiguous: {close_matches} close matches",
        )

    # 7. Default: new entity
    return PlacementResult(
        candidate_id=cand_id,
        label=PlacementLabel.NEW.value,
        alias_sim=best_alias_sim,
        evidence_count=len(evidence_spans),
        reason="no close match found",
    )


# ---------------------------------------------------------------------------
# Step handler
# ---------------------------------------------------------------------------

def run_placement(
    root: Path,
    state: RunState,
    config: RunConfig,
    run_dir: Path,
    apply: bool,
) -> RunState:
    """Step E: Graph Placement — judge where each candidate belongs."""
    ent_path = run_dir / "entity_candidates.jsonl"
    if not ent_path.exists():
        print("[Ralph] Placement: no entity candidates found")
        return state

    candidates = read_jsonl(ent_path)
    if not candidates:
        print("[Ralph] Placement: empty entity candidates")
        return state

    existing = load_existing_entities(root, include_summary=True)

    # Build similarity engine (auto: BERT if available, else TF-IDF)
    sim_engine = SimilarityEngine(
        embed_mode=config.embed_mode,
        bert_model=config.bert_model,
    )

    corpus_texts = []
    for eid, einfo in existing.items():
        text = " ".join(_build_label_list({"entity_id": eid, **einfo}))
        summary = einfo.get("summary", "")
        if summary:
            text += " " + summary
        corpus_texts.append(text)
    for cand in candidates:
        corpus_texts.append(" ".join(_build_label_list(cand)))

    if corpus_texts:
        sim_engine.fit(corpus_texts)

    # Place each candidate
    results: List[Dict] = []
    holds: List[Dict] = []

    label_counts: Dict[str, int] = {}
    for cand in candidates:
        result = place_entity(cand, existing, sim_engine, config)
        results.append(asdict(result))
        label_counts[result.label] = label_counts.get(result.label, 0) + 1

        if result.label == PlacementLabel.HOLD.value:
            from datetime import datetime, timezone
            holds.append(asdict(HoldEntry(
                hold_id=f"H-{state.ralph_run_id[2:]}-{len(holds)+1:04d}",
                entity_candidate_id=cand.get("candidate_id", ""),
                reason=result.reason,
                ambiguity_ratio=0.0,
                created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                source_batch=state.batch.batch_id if state.batch else "",
            )))

    write_jsonl(run_dir / "placement_report.jsonl", results)
    if holds:
        (run_dir / "hold_registry.yaml").write_text(
            dump_yaml({"holds": holds}), encoding="utf-8"
        )

    # update metrics
    total = len(results)
    hold_count = label_counts.get(PlacementLabel.HOLD.value, 0)
    state.metrics.hold_count = hold_count
    state.metrics.hold_ratio = hold_count / total if total else 0.0

    summary_parts = [f"{label}: {count}" for label, count in sorted(label_counts.items())]
    engine = sim_engine.engine_name.upper()
    print(f"[Ralph] Placement ({engine}): {total} candidates — {', '.join(summary_parts)}")
    return state
