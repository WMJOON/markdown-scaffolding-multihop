"""Step D — Entity Parsing: rule + dictionary + pattern based extraction.

LLM is only allowed for type judgment / normalization assist (not used here).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ralph.common import (
    EntityCandidate,
    RelationCandidate,
    RunConfig,
    RunState,
)
from ralph.yaml_io import read_jsonl, write_jsonl


# ---------------------------------------------------------------------------
# Ontology loading
# ---------------------------------------------------------------------------

def load_ontology_node_types(root: Path) -> Dict[str, str]:
    """Load node types from graph-ontology.yaml. Returns {type_key: dir_path}."""
    ontology_path = root / "graph-ontology.yaml"
    types: Dict[str, str] = {}
    if not ontology_path.exists():
        return types

    text = ontology_path.read_text(encoding="utf-8")
    in_nodes = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "nodes:":
            in_nodes = True
            continue
        if stripped == "relations:":
            in_nodes = False
            continue
        if in_nodes and ":" in stripped and not stripped.startswith("-"):
            if "path:" in stripped:
                # "path: data/ontology-entities/Work"
                path_val = stripped.split("path:", 1)[1].strip()
                if types:
                    last_key = list(types.keys())[-1]
                    types[last_key] = path_val
            else:
                key = stripped.rstrip(":").strip()
                types[key] = ""
    return types


def load_existing_entities(root: Path) -> Dict[str, Dict]:
    """Load all existing entity IDs, labels, and aliases.

    Returns {entity_id: {label_en, label_ko, aliases, entity_type, relpath}}.
    """
    entities_dir = root / "data" / "ontology-entities"
    if not entities_dir.exists():
        return {}

    entities: Dict[str, Dict] = {}
    for md_file in entities_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue

        # quick frontmatter extraction
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        fm = parts[1]

        eid = ""
        etype = ""
        label_en = ""
        label_ko = ""
        aliases: List[str] = []

        for line in fm.splitlines():
            line = line.strip()
            if line.startswith("entity_id:"):
                eid = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("entity_type:"):
                etype = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("label_en:"):
                label_en = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("label_ko:"):
                label_ko = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("- ") and aliases is not None:
                # crude alias extraction (only within aliases block)
                pass

        if eid:
            entities[eid] = {
                "label_en": label_en,
                "label_ko": label_ko,
                "aliases": aliases,
                "entity_type": etype,
                "relpath": str(md_file.relative_to(root)),
            }
    return entities


_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")


def extract_wikilink_mentions(text: str) -> List[str]:
    """Extract wikilink targets from text."""
    return _WIKILINK_RE.findall(text)


# ---------------------------------------------------------------------------
# Entity ID generation
# ---------------------------------------------------------------------------

def generate_entity_id(
    entity_type: str,
    label: str,
    existing_ids: Set[str],
) -> str:
    """Generate entity_id: {entity_type_lower}__{slug}.

    Follows existing codebase convention.
    """
    type_prefix = entity_type.lower()
    # convert CamelCase to snake_case
    type_prefix = re.sub(r"([a-z])([A-Z])", r"\1_\2", type_prefix).lower()

    slug = label.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = slug.strip("_")[:80]

    eid = f"{type_prefix}__{slug}"
    if eid not in existing_ids:
        return eid

    # collision: append counter
    for n in range(2, 100):
        candidate = f"{eid}__{n}"
        if candidate not in existing_ids:
            return candidate
    return eid


# ---------------------------------------------------------------------------
# Entity extraction patterns — per entity type
# ---------------------------------------------------------------------------

# Model name patterns
_MODEL_PATTERN = re.compile(
    r"(?:uses?|based on|trained with|employs?|leverag\w+|"
    r"utiliz\w+|powered by|fine.?tun\w+)\s+"
    r"([A-Z][a-zA-Z0-9\-]+(?:\s+[A-Z][a-zA-Z0-9\-]+){0,3})",
    re.IGNORECASE,
)

# Task/capability patterns
_TASK_PATTERN = re.compile(
    r"(?:for|applied to|performs?|enables?|supports?)\s+"
    r"([\w\s]+?(?:detection|classification|forecasting|optimization|"
    r"recognition|generation|retrieval|segmentation|translation|"
    r"summarization|prediction|estimation|planning))",
    re.IGNORECASE,
)

# Dataset patterns
_DATASET_PATTERN = re.compile(
    r"(?:dataset|benchmark|corpus|trained on|evaluated on|tested on)\s+"
    r"([A-Z][a-zA-Z0-9\-]+(?:\s+[A-Z][a-zA-Z0-9\-]+){0,3})",
    re.IGNORECASE,
)

# Metric patterns
_METRIC_PATTERN = re.compile(
    r"(?:accuracy|precision|recall|F1|BLEU|ROUGE|perplexity|AUC|"
    r"mAP|IoU|FID|IS|SSIM|PSNR|WER|CER|latency|throughput)"
    r"\s*(?:of|=|:)?\s*([0-9]+\.?[0-9]*\s*%?)",
    re.IGNORECASE,
)

# ModelFamily patterns
_FAMILY_PATTERN = re.compile(
    r"(?:family of|class of|type of|category of|architecture:?)\s+"
    r"([\w\s\-]+?(?:model|network|architecture|framework)s?)",
    re.IGNORECASE,
)

# Patterns registry: maps entity type → (regex, predicate, new_entity_type)
_PATTERN_REGISTRY = {
    "Model": (_MODEL_PATTERN, "targets_model", "Model"),
    "Work": (_TASK_PATTERN, "targets_work", "Work"),
    "Dataset": (_DATASET_PATTERN, "uses_dataset", "Dataset"),
    "ModelFamily": (_FAMILY_PATTERN, "belongs_to_family", "ModelFamily"),
}


def extract_entity_candidates_from_chunk(
    chunk: Dict,
    existing_entities: Dict[str, Dict],
    existing_ids: Set[str],
    scope_targets: Optional[List[str]] = None,
) -> Tuple[List[EntityCandidate], List[RelationCandidate]]:
    """Extract entity and relation candidates from a single chunk.

    scope_targets controls which entity types to extract. If None, all types.
    """
    text = chunk.get("text", "")
    doc_id = chunk.get("doc_id", "")
    chunk_id = chunk.get("chunk_id", "")
    section = chunk.get("section_path", "")

    entity_cands: List[EntityCandidate] = []
    relation_cands: List[RelationCandidate] = []

    span_ref = f"{chunk_id}:{section}"

    # 1. Wikilink-based detection (always active)
    wikilinks = extract_wikilink_mentions(text)
    for ref in wikilinks:
        basename = ref.split("/")[-1] if "/" in ref else ref
        if basename in existing_entities:
            relation_cands.append(RelationCandidate(
                candidate_id=hashlib.sha256(
                    f"rel:{doc_id}:{basename}:{chunk_id}".encode()
                ).hexdigest()[:16],
                source_entity_id=doc_id,
                predicate="references",
                target_entity_id=basename,
                evidence_spans=[span_ref],
                confidence=0.9,
            ))

    # 2. Pattern-based extraction — filtered by scope_targets
    active_types = set(scope_targets) if scope_targets else set(_PATTERN_REGISTRY.keys())
    # Always include Model and Work as they're commonly cross-referenced
    active_types.update({"Model", "Work"})

    for target_type, (pattern, predicate, new_type) in _PATTERN_REGISTRY.items():
        if target_type not in active_types:
            continue
        for m in pattern.finditer(text):
            name = m.group(1).strip()
            if len(name) < 2:
                continue
            matched_eid = _match_existing(name, existing_entities, target_type)
            if matched_eid:
                relation_cands.append(RelationCandidate(
                    candidate_id=hashlib.sha256(
                        f"rel:{target_type}:{doc_id}:{matched_eid}:{chunk_id}".encode()
                    ).hexdigest()[:16],
                    source_entity_id=doc_id,
                    predicate=predicate,
                    target_entity_id=matched_eid,
                    evidence_spans=[span_ref],
                    confidence=0.8,
                ))
            elif target_type in (scope_targets or list(_PATTERN_REGISTRY.keys())):
                # only create new entities for explicitly targeted types
                eid = generate_entity_id(new_type, name, existing_ids)
                entity_cands.append(EntityCandidate(
                    candidate_id=hashlib.sha256(
                        f"ent:{new_type}:{name}:{chunk_id}".encode()
                    ).hexdigest()[:16],
                    entity_id=eid,
                    entity_type=new_type,
                    label_en=name,
                    label_ko="",
                    evidence_spans=[span_ref],
                    source_doc_id=doc_id,
                    confidence=0.6,
                ))
                existing_ids.add(eid)

    # 3. Metric extraction (if Metric in scope or always as metadata)
    for m in _METRIC_PATTERN.finditer(text):
        metric_name = m.group(0).split("=")[0].split(":")[0].strip()
        value = m.group(1).strip()
        # store as relation metadata, not as entity candidate
        relation_cands.append(RelationCandidate(
            candidate_id=hashlib.sha256(
                f"rel:metric:{doc_id}:{metric_name}:{chunk_id}".encode()
            ).hexdigest()[:16],
            source_entity_id=doc_id,
            predicate="reports_metric",
            target_entity_id=f"metric__{metric_name.lower().replace(' ', '_')}",
            evidence_spans=[f"{span_ref}:value={value}"],
            confidence=0.7,
        ))

    return entity_cands, relation_cands


def _match_existing(
    name: str,
    existing: Dict[str, Dict],
    entity_type: str,
) -> Optional[str]:
    """Try to match a name against existing entities of given type."""
    name_lower = name.lower().replace("-", "_").replace(" ", "_")

    for eid, info in existing.items():
        if info.get("entity_type") != entity_type:
            continue
        # exact match on entity_id suffix
        eid_suffix = eid.split("__", 1)[-1] if "__" in eid else eid
        if name_lower == eid_suffix:
            return eid
        # label match
        label = (info.get("label_en") or "").lower()
        if label and name_lower == label.lower().replace(" ", "_"):
            return eid
    return None


# ---------------------------------------------------------------------------
# Step handler
# ---------------------------------------------------------------------------

def run_parse(
    root: Path,
    state: RunState,
    config: RunConfig,
    run_dir: Path,
    apply: bool,
) -> RunState:
    """Step D: Entity Parsing — extract candidates from chunks."""
    chunks_path = run_dir / "evidence_corpus" / "chunks" / "all_chunks.jsonl"
    if not chunks_path.exists():
        print("[Ralph] Parse: no chunks found")
        return state

    chunks = read_jsonl(chunks_path)
    existing = load_existing_entities(root)
    existing_ids = set(existing.keys())

    # load scope targets
    scope_targets: Optional[List[str]] = None
    meta_path = run_dir / ".run_meta.json"
    if meta_path.exists():
        import json
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        scope_targets = meta.get("scope_targets")
    if config.scope_targets:
        scope_targets = list(config.scope_targets)

    all_entity_cands: List[Dict] = []
    all_relation_cands: List[Dict] = []

    for chunk in chunks:
        ent_cands, rel_cands = extract_entity_candidates_from_chunk(
            chunk, existing, existing_ids, scope_targets
        )
        all_entity_cands.extend([asdict(c) for c in ent_cands])
        all_relation_cands.extend([asdict(c) for c in rel_cands])

    # deduplicate entity candidates by entity_id
    seen_eids: Set[str] = set()
    deduped_entities: List[Dict] = []
    for ec in all_entity_cands:
        eid = ec["entity_id"]
        if eid not in seen_eids:
            seen_eids.add(eid)
            deduped_entities.append(ec)
        else:
            # merge evidence spans
            for existing_ec in deduped_entities:
                if existing_ec["entity_id"] == eid:
                    existing_ec["evidence_spans"].extend(ec["evidence_spans"])
                    break

    write_jsonl(run_dir / "entity_candidates.jsonl", deduped_entities)
    write_jsonl(run_dir / "relation_candidates.jsonl", all_relation_cands)

    state.metrics.entities_processed = len(deduped_entities)
    state.metrics.relations_processed = len(all_relation_cands)

    print(
        f"[Ralph] Parse: {len(deduped_entities)} entity candidates, "
        f"{len(all_relation_cands)} relation candidates"
    )
    return state
