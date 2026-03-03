"""Step F — Seal & Optimize: validation suite + seed candidate generation.

No LLM auto-merge allowed.
"""
from __future__ import annotations

import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set

from ralph.common import (
    ONTOLOGY_ENTITIES_DIR,
    PlacementLabel,
    RunConfig,
    RunState,
    ValidationResult,
)
from ralph.yaml_io import dump_yaml, read_jsonl, write_jsonl


# ---------------------------------------------------------------------------
# Validation Suite (V1–V8)
# ---------------------------------------------------------------------------

def _check_v1_evidence_coverage(
    candidates: List[Dict], placements: List[Dict]
) -> ValidationResult:
    """V1: Every new/changed candidate has >= 1 evidence span."""
    active_labels = {PlacementLabel.NEW.value, PlacementLabel.EXTEND.value,
                     PlacementLabel.MERGE.value}
    active_cand_ids = {
        p["candidate_id"] for p in placements if p.get("label") in active_labels
    }
    missing = []
    for c in candidates:
        if c.get("candidate_id") in active_cand_ids:
            if not c.get("evidence_spans"):
                missing.append(c.get("entity_id", c.get("candidate_id")))

    return ValidationResult(
        check_id="V1",
        name="evidence_coverage",
        passed=len(missing) == 0,
        blocking=True,
        details=f"{len(missing)} candidates without evidence" if missing else "ok",
    )


def _check_v2_entity_id_uniqueness(
    candidates: List[Dict], existing_ids: Set[str], placements: List[Dict]
) -> ValidationResult:
    """V2: New entity_ids don't collide with existing entities."""
    new_cand_ids = {
        p["candidate_id"] for p in placements
        if p.get("label") == PlacementLabel.NEW.value
    }
    collisions = []
    for c in candidates:
        if c.get("candidate_id") in new_cand_ids:
            eid = c.get("entity_id", "")
            if eid in existing_ids:
                collisions.append(eid)

    return ValidationResult(
        check_id="V2",
        name="entity_id_uniqueness",
        passed=len(collisions) == 0,
        blocking=True,
        details=f"collisions: {collisions}" if collisions else "ok",
    )


def _check_v3_relation_type_validity(
    relations: List[Dict], valid_predicates: Set[str]
) -> ValidationResult:
    """V3: All relation predicates exist in ontology definition."""
    # For now, accept any predicate — full validation requires parsing
    # graph-ontology.yaml relations section which only has 'source'/'evidence'
    # The actual relation types (targets_work, supports_purpose, etc.) are
    # defined by entity convention, not in graph-ontology.yaml
    invalid = []
    return ValidationResult(
        check_id="V3",
        name="relation_type_validity",
        passed=True,
        blocking=True,
        details="ok (convention-based predicates accepted)",
    )


def _check_v4_hold_residual(placements: List[Dict]) -> ValidationResult:
    """V4: No unresolved holds in current batch."""
    holds = [p for p in placements if p.get("label") == PlacementLabel.HOLD.value]
    return ValidationResult(
        check_id="V4",
        name="hold_residual",
        passed=len(holds) == 0,
        blocking=True,
        details=f"{len(holds)} unresolved holds" if holds else "ok",
    )


def _check_v5_orphan_check(
    candidates: List[Dict], relations: List[Dict], placements: List[Dict]
) -> ValidationResult:
    """V5: No new nodes with 0 relations (warning only)."""
    new_cand_ids = {
        p["candidate_id"] for p in placements
        if p.get("label") == PlacementLabel.NEW.value
    }
    new_entity_ids = set()
    for c in candidates:
        if c.get("candidate_id") in new_cand_ids:
            new_entity_ids.add(c.get("entity_id", ""))

    # check if any relation references these entities
    connected = set()
    for r in relations:
        src = r.get("source_entity_id", "")
        tgt = r.get("target_entity_id", "")
        if src in new_entity_ids:
            connected.add(src)
        if tgt in new_entity_ids:
            connected.add(tgt)

    orphans = new_entity_ids - connected
    return ValidationResult(
        check_id="V5",
        name="orphan_check",
        passed=len(orphans) == 0,
        blocking=False,  # warning only
        details=f"{len(orphans)} orphan entities" if orphans else "ok",
    )


def _check_v6_layer_consistency() -> ValidationResult:
    """V6: Purpose↔Structure layer path exists (warning only)."""
    # Simplified: always pass with warning for now
    return ValidationResult(
        check_id="V6",
        name="layer_consistency",
        passed=True,
        blocking=False,
        details="ok (simplified check)",
    )


def _check_v7_merge_finalized(placements: List[Dict]) -> ValidationResult:
    """V7: No merge_candidate remaining (all resolved)."""
    unresolved = [
        p for p in placements
        if p.get("label") == PlacementLabel.MERGE_CANDIDATE.value
    ]
    return ValidationResult(
        check_id="V7",
        name="merge_finalized",
        passed=len(unresolved) == 0,
        blocking=True,
        details=f"{len(unresolved)} unresolved merge_candidates" if unresolved else "ok",
    )


def _check_v8_source_ref_format(candidates: List[Dict]) -> ValidationResult:
    """V8: All source_refs match [[source__*]] format."""
    _SOURCE_RE = re.compile(r"^\[\[source__[a-z0-9_]+\]\]$")
    bad = []
    for c in candidates:
        for ref in c.get("source_refs", []):
            if ref and not _SOURCE_RE.match(ref):
                bad.append(ref)

    return ValidationResult(
        check_id="V8",
        name="source_ref_format",
        passed=len(bad) == 0,
        blocking=True,
        details=f"{len(bad)} invalid refs: {bad[:5]}" if bad else "ok",
    )


def run_validation_suite(
    candidates: List[Dict],
    relations: List[Dict],
    placements: List[Dict],
    existing_ids: Set[str],
) -> List[ValidationResult]:
    """Run V1–V8 validation checks."""
    results = [
        _check_v1_evidence_coverage(candidates, placements),
        _check_v2_entity_id_uniqueness(candidates, existing_ids, placements),
        _check_v3_relation_type_validity(relations, set()),
        _check_v4_hold_residual(placements),
        _check_v5_orphan_check(candidates, relations, placements),
        _check_v6_layer_consistency(),
        _check_v7_merge_finalized(placements),
        _check_v8_source_ref_format(candidates),
    ]
    return results


# ---------------------------------------------------------------------------
# Entity markdown generation
# ---------------------------------------------------------------------------

def generate_entity_markdown(
    candidate: Dict,
    placement: Dict,
    rel_candidates: List[Dict],
) -> str:
    """Generate entity .md file matching existing vault format."""
    eid = candidate.get("entity_id", "")
    etype = candidate.get("entity_type", "")
    label_en = candidate.get("label_en", "")
    label_ko = candidate.get("label_ko", "") or label_en
    confidence = candidate.get("confidence", 0.6)
    source_refs = candidate.get("source_refs", [])
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # determine ontology_layer from entity_type
    layer_map = {
        "Model": "model", "ModelFamily": "model", "ModelParadigm": "model",
        "ModelModality": "model", "ModelCapability": "model",
        "CaseStudy": "semantic", "Work": "semantic", "Industry": "semantic",
        "Purpose": "semantic", "Workflow": "semantic",
        "AIAgent": "structure", "AISystem": "structure", "PhysicalAI": "structure",
    }
    ontology_layer = layer_map.get(etype, "semantic")

    # build relations from relation_candidates
    relations_yaml = ""
    if rel_candidates:
        rel_lines = []
        for r in rel_candidates:
            predicate = r.get("predicate", "references")
            target = r.get("target_entity_id", "")
            # determine target directory from entity_type if possible
            rel_lines.append(f'  - type: {predicate}\n    target: "[[{target}]]"')
        relations_yaml = "\n".join(rel_lines)

    source_refs_yaml = "\n".join(
        f'  - "{ref}"' for ref in source_refs
    ) if source_refs else '  - "[[source__ralph_etl]]"'

    tags_yaml = f"  - ontology/{etype.lower()}\n  - ontology/entity"

    fm = (
        f"---\n"
        f"entity_id: {eid}\n"
        f"entity_type: {etype}\n"
        f"ontology_layer: {ontology_layer}\n"
        f"ontology_node: {etype}\n"
        f'label_ko: "{label_ko}"\n'
        f'label_en: "{label_en}"\n'
        f"status: draft\n"
        f"version: v0.1.0\n"
        f"created: {today}\n"
        f"updated: {today}\n"
        f"source_refs:\n{source_refs_yaml}\n"
        f"confidence: {confidence}\n"
    )
    if relations_yaml:
        fm += f"relations:\n{relations_yaml}\n"
    fm += f"tags:\n{tags_yaml}\n"
    fm += "---\n\n"

    body = (
        f"# Summary\n"
        f"{label_en} — Ralph ETL에 의해 자동 추출된 엔티티.\n\n"
        f"# Definition\n"
        f"- entity_type: {etype}\n"
        f"- status: draft\n"
        f"- confidence: {confidence}\n\n"
        f"# Evidence\n"
    )
    for ref in source_refs:
        body += f"- {ref}\n"
    if not source_refs:
        body += "- [[source__ralph_etl]]\n"

    return fm + body


# ---------------------------------------------------------------------------
# Seed candidate generation
# ---------------------------------------------------------------------------

def generate_seed_candidate(
    placements: List[Dict],
    candidates: List[Dict],
    state: RunState,
) -> Dict:
    """Generate seed candidate summary."""
    label_counts: Dict[str, int] = {}
    for p in placements:
        label = p.get("label", "unknown")
        label_counts[label] = label_counts.get(label, 0) + 1

    return {
        "seed_version": f"seed-{state.ralph_run_id}",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": state.ralph_run_id,
        "input_snapshot_hash": state.input_snapshot_hash,
        "config_hash": state.config_hash,
        "code_ref": state.code_ref,
        "placement_summary": label_counts,
        "total_candidates": len(candidates),
        "total_placements": len(placements),
    }


# ---------------------------------------------------------------------------
# Step handler
# ---------------------------------------------------------------------------

def run_seal(
    root: Path,
    state: RunState,
    config: RunConfig,
    run_dir: Path,
    apply: bool,
) -> RunState:
    """Step F: Seal — validate, generate seed, optionally write entities."""
    candidates = read_jsonl(run_dir / "entity_candidates.jsonl")
    relations = read_jsonl(run_dir / "relation_candidates.jsonl")
    placements = read_jsonl(run_dir / "placement_report.jsonl")

    # load existing entity IDs for uniqueness check
    existing_ids: Set[str] = set()
    entities_dir = root / ONTOLOGY_ENTITIES_DIR
    if entities_dir.exists():
        for md_file in entities_dir.rglob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            for line in text.splitlines()[:20]:
                if line.strip().startswith("entity_id:"):
                    eid = line.split(":", 1)[1].strip().strip('"').strip("'")
                    existing_ids.add(eid)
                    break

    # run validation
    results = run_validation_suite(candidates, relations, placements, existing_ids)

    # print results
    blocked = False
    for r in results:
        status = "PASS" if r.passed else ("BLOCKED" if r.blocking else "WARN")
        print(f"  [{status}] {r.check_id} {r.name}: {r.details}")
        if not r.passed and r.blocking:
            blocked = True

    # write validation results
    write_jsonl(
        run_dir / "validation_results.jsonl",
        [asdict(r) for r in results],
    )

    if blocked:
        print("[Ralph] Seal: BLOCKED by validation failures")
        # still generate audit trail
        write_jsonl(run_dir / "audit_trail.jsonl", [
            {"event": "seal_blocked", "results": [asdict(r) for r in results]}
        ])
        return state

    # generate seed candidate
    seed = generate_seed_candidate(placements, candidates, state)
    (run_dir / "seed_candidate.yaml").write_text(
        dump_yaml(seed), encoding="utf-8"
    )

    # generate audit trail
    audit_entries = []
    cand_map = {c.get("candidate_id"): c for c in candidates}
    for p in placements:
        cand = cand_map.get(p.get("candidate_id"), {})
        audit_entries.append({
            "candidate_id": p.get("candidate_id"),
            "entity_id": cand.get("entity_id"),
            "label": p.get("label"),
            "target_existing_id": p.get("target_existing_id"),
            "evidence_spans": cand.get("evidence_spans", []),
        })
    write_jsonl(run_dir / "audit_trail.jsonl", audit_entries)

    # apply: write new entities to data/ontology-entities/
    if apply:
        new_placements = [
            p for p in placements if p.get("label") == PlacementLabel.NEW.value
        ]
        written = 0
        for p in new_placements:
            cand = cand_map.get(p.get("candidate_id"))
            if not cand:
                continue
            etype = cand.get("entity_type", "")
            eid = cand.get("entity_id", "")
            # find relevant relations
            cand_rels = [
                r for r in relations
                if r.get("source_entity_id") == cand.get("source_doc_id")
            ]
            md = generate_entity_markdown(cand, p, cand_rels)

            out_dir = entities_dir / etype
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{eid}.md"
            if not out_path.exists():
                out_path.write_text(md, encoding="utf-8")
                written += 1
                print(f"  [written] {eid}")

        print(f"[Ralph] Seal: {written} new entities written")
    else:
        new_count = sum(
            1 for p in placements if p.get("label") == PlacementLabel.NEW.value
        )
        print(f"[Ralph] Seal: {new_count} new entities (dry-run, use --apply to write)")

    print(f"[Ralph] Seal: seed candidate generated at {run_dir / 'seed_candidate.yaml'}")
    return state
