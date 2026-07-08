#!/usr/bin/env python3
"""zvec-backed semantic expansion for MSM KBs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import zvec
from zvec import (
    CollectionSchema,
    DataType,
    Doc,
    FieldSchema,
    FlatIndexParam,
    VectorQuery,
    VectorSchema,
)

SUPPORTED_SUFFIXES = {".md", ".txt", ".json", ".jsonl"}
DEFAULT_DIMENSION = 384
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_OVERLAP = 120
ENTITY_JSONL_GLOBS = (
    "ontology/Tbox/**/entities.jsonl",
    "ontology/explain/concept/**/entities.jsonl",
    "ontology/system/semantic/**/entities.jsonl",
)
RELATION_JSONL_GLOBS = (
    "ontology/Tbox/**/relations.jsonl",
    "ontology/explain/concept/**/relations.jsonl",
    "ontology/system/semantic/**/relations.jsonl",
)
FORWARD_RELATION_PATTERNS = (
    ("depends_on", r"(depends?\s+on|requires?|필요|의존|기반|바탕)"),
    ("implements", r"(implements?|realizes?|구현|실현|실행)"),
    ("enables", r"(enables?|allows?|supports?|가능하게|활성화|지원)"),
    ("contains", r"(contains?|includes?|comprises?|composed\s+of|구성|포함|내장)"),
    ("extends", r"(extends?|expands?|확장|보강)"),
    ("optimizes", r"(optimizes?|improves?|최적화|개선|향상)"),
    ("causes", r"(causes?|leads?\s+to|drives?|유발|초래|이어|만들어)"),
    ("uses", r"(uses?|uses?\s+the|활용|사용|이용)"),
    ("maps_to", r"(maps?\s+to|corresponds?\s+to|매핑|대응)"),
    ("contrasts_with", r"(contrasts?\s+with|differs?\s+from|구분|대비|반면)"),
)
REVERSE_RELATION_PATTERNS = (
    ("part_of", r"(part\s+of|belongs?\s+to|하위|일부|소속)"),
    ("enabled_by", r"(enabled\s+by|supported\s+by|가능해진|지원받)"),
    ("implemented_by", r"(implemented\s+by|realized\s+by|구현된|실현된)"),
    ("caused_by", r"(caused\s+by|driven\s+by|기인|때문)"),
)


def init_zvec() -> None:
    try:
        zvec.init(log_level=zvec.LogLevel.ERROR)
    except RuntimeError:
        pass


def default_index_path(target: Path) -> Path:
    return target / "memory" / "ontology-index" / "zvec"


def schema(dimension: int) -> CollectionSchema:
    return CollectionSchema(
        "msm_semantic_search",
        fields=[
            FieldSchema("text", DataType.STRING, nullable=True),
            FieldSchema("title", DataType.STRING, nullable=True),
            FieldSchema("source_path", DataType.STRING, nullable=True),
            FieldSchema("tags", DataType.STRING, nullable=True),
            FieldSchema("created_at", DataType.STRING, nullable=True),
            FieldSchema("chunk_index", DataType.INT64, nullable=True),
        ],
        vectors=[
            VectorSchema(
                "dense_embedding",
                DataType.VECTOR_FP32,
                dimension=dimension,
                index_param=FlatIndexParam(),
            )
        ],
    )


def open_or_create(path: Path, dimension: int):
    init_zvec()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return zvec.open(str(path))
    return zvec.create_and_open(str(path), schema(dimension))


def open_existing(path: Path):
    init_zvec()
    if not path.exists():
        raise FileNotFoundError(
            f"semantic_expansion_skipped: zvec index not found at {path}"
        )
    return zvec.open(str(path), zvec.CollectionOption(read_only=True))


def token_features(text: str) -> Iterable[str]:
    lowered = text.lower()
    for token in re.findall(r"[0-9a-zA-Z가-힣_./:-]+", lowered):
        yield "tok:" + token
    compact = re.sub(r"\s+", "", lowered)
    for i in range(max(0, len(compact) - 2)):
        gram = compact[i : i + 3]
        if gram.strip():
            yield "tri:" + gram


def embed_hash(text: str, dimension: int) -> list[float]:
    vec = [0.0] * dimension
    for feature in token_features(text):
        digest = hashlib.sha256(feature.encode("utf-8")).digest()
        slot = int.from_bytes(digest[:8], "big") % dimension
        sign = 1.0 if digest[8] & 1 else -1.0
        vec[slot] += sign
    norm = math.sqrt(sum(value * value for value in vec)) or 1.0
    return [value / norm for value in vec]


def iter_input_files(inputs: list[Path], target: Path) -> Iterable[Path]:
    roots = inputs or [target / "ontology", target / "evidence"]
    for raw in roots:
        path = raw if raw.is_absolute() else target / raw
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in SUPPORTED_SUFFIXES:
                    yield child


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def read_jsonl(path: Path) -> Iterable[dict]:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            yield record


def first_value(record: dict, keys: tuple[str, ...], default: str = "") -> str:
    for key in keys:
        value = record.get(key)
        if value is not None and value != "":
            return str(value)
    return default


def infer_cluster_from_path(path: Path, target: Path) -> str:
    rel_parts = path.relative_to(target).parts
    if "Tbox" in rel_parts:
        idx = rel_parts.index("Tbox") + 1
        return rel_parts[idx] if idx < len(rel_parts) else ""
    if "concept" in rel_parts:
        idx = rel_parts.index("concept") + 1
        return "/".join(rel_parts[idx:-1])
    if "semantic" in rel_parts:
        idx = rel_parts.index("semantic") + 1
        return "/".join(rel_parts[idx:-1])
    return ""


def normalized_entity(record: dict, path: Path, target: Path) -> dict | None:
    entity_id = first_value(record, ("id", "entity_id", "concept_id", "node_id"))
    label = first_value(record, ("label", "label_en", "label_ko", "name"), entity_id)
    if not entity_id or not label:
        return None
    cluster = first_value(record, ("cluster", "domain", "subdomain")) or infer_cluster_from_path(path, target)
    rel_path = str(path.relative_to(target)) if path.is_relative_to(target) else str(path)
    return {
        **record,
        "_id": entity_id,
        "_label": label,
        "_label_ko": first_value(record, ("label_ko",)),
        "_label_en": first_value(record, ("label_en",)),
        "_cluster": cluster,
        "_record_path": rel_path,
    }


def iter_entity_records(target: Path, cluster: str | None = None) -> list[dict]:
    entities: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for pattern in ENTITY_JSONL_GLOBS:
        for path in sorted(target.glob(pattern)):
            for record in read_jsonl(path):
                entity = normalized_entity(record, path, target)
                if not entity:
                    continue
                if cluster and entity.get("_cluster") != cluster:
                    continue
                key = (entity["_id"], entity["_cluster"])
                if key in seen:
                    continue
                seen.add(key)
                entities.append(entity)
    return entities


def relation_endpoints(record: dict) -> tuple[str, str, str]:
    source = first_value(record, ("source", "from", "source_entity_id", "subject"))
    predicate = first_value(record, ("predicate", "relation", "rel", "edge"), "related_to")
    target = first_value(record, ("target", "to", "target_entity_id", "object"))
    return source, predicate, target


def existing_relation_keys(target: Path) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for pattern in RELATION_JSONL_GLOBS:
        for path in sorted(target.glob(pattern)):
            for record in read_jsonl(path):
                source, _predicate, target_id = relation_endpoints(record)
                if source and target_id:
                    keys.add((source, target_id))
                    keys.add((target_id, source))
    return keys


def entity_query(entity: dict) -> str:
    parts = [
        entity.get("_label", ""),
        entity.get("_label_ko", ""),
        entity.get("_label_en", ""),
        str(entity.get("description", "")),
        " ".join(str(v) for v in entity.get("synonyms", []) if v),
    ]
    extra = entity.get("extra")
    if isinstance(extra, dict):
        facts = extra.get("key_facts")
        if isinstance(facts, list):
            parts.extend(str(v) for v in facts if v)
    return " ".join(part for part in parts if part).strip()


def mention_keys(entity: dict) -> list[str]:
    raw = [
        entity.get("_id", ""),
        entity.get("_label", ""),
        entity.get("_label_ko", ""),
        entity.get("_label_en", ""),
        str(entity.get("md_path", "")),
        str(entity.get("source_file", "")),
    ]
    keys: list[str] = []
    seen: set[str] = set()
    for value in raw:
        raw_key = value.strip()
        key = raw_key.lower()
        is_short_acronym = len(raw_key) >= 2 and raw_key.upper() == raw_key
        if (len(key) < 4 and not is_short_acronym and "." not in key) or key in seen:
            continue
        seen.add(key)
        keys.append(key)
    return keys


def candidate_confidence(score: float, reason_count: int) -> float:
    bonus = min(0.08, 0.02 * max(0, reason_count - 1))
    return round(min(1.0, max(0.0, score + bonus)), 4)


def find_mention_position(text: str, keys: list[str]) -> tuple[int, str]:
    lowered = text.lower()
    best_pos = -1
    best_key = ""
    for key in keys:
        if not key:
            continue
        pos = lowered.find(key.lower())
        if pos >= 0 and (best_pos < 0 or pos < best_pos):
            best_pos = pos
            best_key = key
    return best_pos, best_key


def find_mention_positions(text: str, keys: list[str]) -> list[tuple[int, str]]:
    lowered = text.lower()
    positions: list[tuple[int, str]] = []
    for key in keys:
        if not key:
            continue
        key_lower = key.lower()
        start = 0
        while True:
            pos = lowered.find(key_lower, start)
            if pos < 0:
                break
            positions.append((pos, key))
            start = pos + max(1, len(key_lower))
    return sorted(positions)


def closest_mention_pair(
    text: str,
    source_keys: list[str],
    target_keys: list[str],
) -> tuple[int, str, int, str]:
    source_positions = find_mention_positions(text, source_keys)
    target_positions = find_mention_positions(text, target_keys)
    best: tuple[int, str, int, str] | None = None
    best_distance: int | None = None
    for source_pos, source_key in source_positions:
        for target_pos, target_key in target_positions:
            if source_pos == target_pos:
                continue
            distance = abs(source_pos - target_pos)
            if best_distance is None or distance < best_distance:
                best = (source_pos, source_key, target_pos, target_key)
                best_distance = distance
    return best or (-1, "", -1, "")


def local_relation_window(text: str, first_pos: int, second_pos: int, tail: int = 140) -> str:
    start = max(0, min(first_pos, second_pos))
    end = min(len(text), max(first_pos, second_pos) + tail)
    return text[start:end]


def has_sentence_boundary_between(text: str, first_pos: int, second_pos: int) -> bool:
    start = min(first_pos, second_pos)
    end = max(first_pos, second_pos)
    between = text[start:end]
    return bool(re.search(r"[.!?。！？]\s+", between))


def relation_predicate_from_window(window: str) -> tuple[str, str, float] | None:
    lowered = window.lower()
    for predicate, pattern in (*FORWARD_RELATION_PATTERNS, *REVERSE_RELATION_PATTERNS):
        match = re.search(pattern, lowered)
        if match:
            bonus = 0.12 if predicate in dict(FORWARD_RELATION_PATTERNS) else 0.10
            return predicate, match.group(0), bonus
    return None


def infer_directed_relation(
    query_source: dict,
    target_entity: dict,
    text: str,
    source_keys: list[str],
    target_keys: list[str],
    fallback_predicate: str,
) -> dict:
    source_pos, source_term, target_pos, target_term = closest_mention_pair(
        text,
        source_keys,
        target_keys,
    )
    if source_pos < 0 or target_pos < 0:
        return {
            "source": query_source["_id"],
            "predicate": fallback_predicate,
            "target": target_entity["_id"],
            "source_label": query_source["_label"],
            "target_label": target_entity["_label"],
            "inference_method": "co_mention_fallback",
            "direction_confidence_bonus": 0.0,
            "direction_evidence": "",
            "source_term": source_term,
            "target_term": target_term,
        }

    window = local_relation_window(text, source_pos, target_pos)
    if has_sentence_boundary_between(text, source_pos, target_pos):
        return {
            "source": query_source["_id"],
            "predicate": fallback_predicate,
            "target": target_entity["_id"],
            "source_label": query_source["_label"],
            "target_label": target_entity["_label"],
            "inference_method": "cross_sentence_co_mention_fallback",
            "direction_confidence_bonus": 0.0,
            "direction_evidence": window.strip()[:360],
            "source_term": source_term,
            "target_term": target_term,
        }
    inferred = relation_predicate_from_window(window)
    if not inferred:
        return {
            "source": query_source["_id"],
            "predicate": fallback_predicate,
            "target": target_entity["_id"],
            "source_label": query_source["_label"],
            "target_label": target_entity["_label"],
            "inference_method": "co_mention_fallback",
            "direction_confidence_bonus": 0.0,
            "direction_evidence": window.strip()[:360],
            "source_term": source_term,
            "target_term": target_term,
        }

    predicate, lexical_cue, bonus = inferred
    if source_pos <= target_pos:
        source_entity = query_source
        target = target_entity
    else:
        source_entity = target_entity
        target = query_source
    return {
        "source": source_entity["_id"],
        "predicate": predicate,
        "target": target["_id"],
        "source_label": source_entity["_label"],
        "target_label": target["_label"],
        "inference_method": "lexical_direction_cue",
        "direction_confidence_bonus": bonus,
        "direction_evidence": window.strip()[:360],
        "source_term": source_term,
        "target_term": target_term,
        "lexical_cue": lexical_cue,
    }


def infer_title(text: str, path: Path) -> str:
    frontmatter = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if frontmatter:
        for line in frontmatter.group(1).splitlines():
            if line.strip().startswith("title:"):
                return line.split(":", 1)[1].strip().strip('"')
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def infer_tags(text: str) -> str:
    frontmatter = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not frontmatter:
        return ""
    tags: list[str] = []
    capture_list = False
    for line in frontmatter.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("tags:"):
            value = stripped.split(":", 1)[1].strip()
            if value.startswith("[") and value.endswith("]"):
                return value.strip("[]").replace('"', "").replace("'", "")
            if value:
                return value
            capture_list = True
            continue
        if capture_list and stripped.startswith("- "):
            tags.append(stripped[2:].strip())
        elif capture_list and stripped and not stripped.startswith("- "):
            break
    return ",".join(tags)


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if len(para) > chunk_size:
            if buf:
                chunks.append(buf)
                buf = ""
            step = max(1, chunk_size - overlap)
            for start in range(0, len(para), step):
                chunks.append(para[start : start + chunk_size])
            continue
        if not buf:
            buf = para
        elif len(buf) + 2 + len(para) <= chunk_size:
            buf = f"{buf}\n\n{para}"
        else:
            chunks.append(buf)
            buf = para
    if buf:
        chunks.append(buf)
    return chunks or ([text[:chunk_size]] if text else [])


def doc_id(source_path: str, chunk_index: int, text: str) -> str:
    payload = f"{source_path}#{chunk_index}:{text[:128]}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def cmd_init(args: argparse.Namespace) -> int:
    target = args.target.resolve()
    path = args.path or default_index_path(target)
    coll = open_or_create(path, args.dimension)
    coll.flush()
    print(json.dumps({"status": "ok", "path": str(path), "dimension": args.dimension}))
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    target = args.target.resolve()
    path = args.path or default_index_path(target)
    coll = open_or_create(path, args.dimension)
    now = datetime.now(timezone.utc).isoformat()
    batch: list[Doc] = []
    file_count = 0
    chunk_count = 0

    for file_path in iter_input_files(args.input, target):
        text = read_text(file_path)
        if not text.strip():
            continue
        rel_path = str(file_path.relative_to(target)) if file_path.is_relative_to(target) else str(file_path)
        title = infer_title(text, file_path)
        tags = infer_tags(text)
        file_count += 1
        for idx, chunk in enumerate(chunk_text(text, args.chunk_size, args.chunk_overlap)):
            if not chunk.strip():
                continue
            batch.append(
                Doc(
                    doc_id(rel_path, idx, chunk),
                    vectors={"dense_embedding": embed_hash(chunk, args.dimension)},
                    fields={
                        "text": chunk,
                        "title": title,
                        "source_path": rel_path,
                        "tags": tags,
                        "created_at": now,
                        "chunk_index": idx,
                    },
                )
            )
            chunk_count += 1
            if len(batch) >= args.batch_size:
                coll.upsert(batch)
                batch = []
    if batch:
        coll.upsert(batch)
    coll.flush()
    if not args.no_optimize:
        coll.optimize()
    print(json.dumps({"status": "ok", "path": str(path), "files": file_count, "chunks": chunk_count}))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    target = args.target.resolve()
    path = args.path or default_index_path(target)
    try:
        coll = open_existing(path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    query = " ".join(args.query).strip()
    if not query:
        print("query is required", file=sys.stderr)
        return 2
    results = coll.query(
        VectorQuery("dense_embedding", vector=embed_hash(query, args.dimension)),
        topk=args.topk,
        filter=args.filter,
        output_fields=["title", "source_path", "tags", "chunk_index", "text"],
    )
    if args.format == "json":
        print(
            json.dumps(
                [
                    {"id": d.id, "score": d.score, **(d.fields or {})}
                    for d in results
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.format == "jsonl":
        for d in results:
            print(json.dumps({"id": d.id, "score": d.score, **(d.fields or {})}, ensure_ascii=False))
    else:
        for d in results:
            fields = d.fields or {}
            text = (fields.get("text") or "").replace("\n", " ")
            preview = text[: args.preview_chars]
            print(
                f"{d.score:.4f}\t{fields.get('source_path','')}"
                f"\tchunk={fields.get('chunk_index','')}\t{fields.get('title','')}\t{preview}"
            )
    return 0


def relation_candidate_records(args: argparse.Namespace) -> tuple[list[dict], dict]:
    target = args.target.resolve()
    path = args.path or default_index_path(target)
    coll = open_existing(path)
    entities = iter_entity_records(target, args.cluster)
    if args.source_id:
        source_ids = set(args.source_id)
        entities = [entity for entity in entities if entity["_id"] in source_ids]
    entity_by_id = {entity["_id"]: entity for entity in entities}
    mention_index = {
        entity["_id"]: mention_keys(entity)
        for entity in entities
    }
    existing = existing_relation_keys(target)
    best: dict[tuple[str, str, str], dict] = {}

    for source in entities:
        query = entity_query(source)
        if not query:
            continue
        results = coll.query(
            VectorQuery("dense_embedding", vector=embed_hash(query, args.dimension)),
            topk=args.topk,
            filter=args.filter,
            output_fields=["title", "source_path", "tags", "chunk_index", "text"],
        )
        for doc in results:
            fields = doc.fields or {}
            source_path = str(fields.get("source_path") or "")
            if not args.include_registry_evidence and source_path.endswith((
                "entities.jsonl",
                "relations.jsonl",
                "instances.jsonl",
            )):
                continue
            haystack = " ".join(
                str(fields.get(key) or "")
                for key in ("title", "source_path", "tags", "text")
            ).lower()
            for target_id, keys in mention_index.items():
                if target_id == source["_id"]:
                    continue
                target_entity = entity_by_id[target_id]
                if not args.cross_cluster and target_entity["_cluster"] != source["_cluster"]:
                    continue
                if (source["_id"], target_id) in existing:
                    continue
                matched = [key for key in keys if key and key in haystack]
                if not matched:
                    continue
                relation = infer_directed_relation(
                    source,
                    target_entity,
                    str(fields.get("text") or ""),
                    mention_index.get(source["_id"], []),
                    keys,
                    args.predicate,
                )
                if args.direction_mode == "undirected":
                    relation = {
                        **relation,
                        "source": source["_id"],
                        "source_label": source["_label"],
                        "predicate": args.predicate,
                        "target": target_id,
                        "target_label": target_entity["_label"],
                        "inference_method": "co_mention_undirected",
                        "direction_confidence_bonus": 0.0,
                    }
                elif args.direction_mode == "directed" and relation["predicate"] == args.predicate:
                    relation = {
                        **relation,
                        "source": source["_id"],
                        "source_label": source["_label"],
                        "target": target_id,
                        "target_label": target_entity["_label"],
                        "inference_method": "query_entity_direction",
                    }
                confidence = candidate_confidence(
                    float(doc.score) + float(relation.get("direction_confidence_bonus", 0.0)),
                    len(matched),
                )
                record = {
                    "event_type": "relation_candidate",
                    "source": relation["source"],
                    "source_label": relation["source_label"],
                    "predicate": relation["predicate"],
                    "target": relation["target"],
                    "target_label": relation["target_label"],
                    "cluster": source["_cluster"],
                    "status": "candidate",
                    "confidence": confidence,
                    "semantic_score": float(doc.score),
                    "match_reason": relation["inference_method"],
                    "matched_terms": matched[:5],
                    "direction_evidence": relation.get("direction_evidence", ""),
                    "lexical_cue": relation.get("lexical_cue", ""),
                    "evidence": {
                        "zvec_doc_id": doc.id,
                        "source_path": fields.get("source_path"),
                        "chunk_index": fields.get("chunk_index"),
                        "title": fields.get("title"),
                    },
                    "source_refs": [],
                    "requires_source_validation": True,
                    "promotion": {
                        "tool": "msm-ontology add --relation",
                        "required_before_apply": [
                            "verify source_path/chunk line range",
                            "attach evidence:seed:* source_refs",
                            "confirm predicate semantics",
                        ],
                    },
                }
                endpoints = (record["source"], record["target"])
                dedupe_as_undirected = (
                    args.direction_mode == "undirected"
                    or (args.direction_mode == "infer" and record["predicate"] == args.predicate)
                )
                if dedupe_as_undirected:
                    endpoints = tuple(sorted(endpoints))
                key = (endpoints[0], record["predicate"], endpoints[1])
                current = best.get(key)
                if not current or record["confidence"] > current["confidence"]:
                    best[key] = record

    records = sorted(
        best.values(),
        key=lambda item: (item["confidence"], item["semantic_score"]),
        reverse=True,
    )[: args.limit]
    summary = {
        "status": "ok",
        "path": str(path),
        "entity_count": len(entities),
        "candidate_count": len(records),
        "predicate": args.predicate,
        "direction_mode": args.direction_mode,
        "cluster": args.cluster,
        "cross_cluster": args.cross_cluster,
    }
    return records, summary


def write_relation_candidates(args: argparse.Namespace, records: list[dict]) -> None:
    if not args.output:
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.append else "w"
    with args.output.open(mode, encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def cmd_link_relations(args: argparse.Namespace) -> int:
    try:
        records, summary = relation_candidate_records(args)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    write_relation_candidates(args, records)
    if args.format == "json":
        print(json.dumps({"summary": summary, "candidates": records}, ensure_ascii=False, indent=2))
    elif args.format == "jsonl":
        for record in records:
            print(json.dumps(record, ensure_ascii=False))
    else:
        print(
            f"candidates={summary['candidate_count']} entities={summary['entity_count']} "
            f"predicate={summary['predicate']}"
        )
        for record in records:
            evidence = record["evidence"]
            print(
                f"{record['confidence']:.4f}\t{record['source']} "
                f"-[{record['predicate']}]-> {record['target']}\t"
                f"{evidence.get('source_path')}#chunk={evidence.get('chunk_index')}"
            )
    if args.output:
        print(json.dumps({"event_type": "relation_candidates_written", "path": str(args.output), "count": len(records)}))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    target = args.target.resolve()
    path = args.path or default_index_path(target)
    try:
        coll = open_existing(path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    stats = coll.stats
    print(
        json.dumps(
            {
                "path": str(path),
                "doc_count": stats.doc_count,
                "index_completeness": dict(stats.index_completeness),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--path", type=Path)
    parser.add_argument("--dimension", type=int, default=DEFAULT_DIMENSION)
    parser.add_argument("--embedder", choices=["hash"], default="hash")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="msm-semantic-search")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init")
    add_common(p_init)
    p_init.set_defaults(func=cmd_init)

    p_add = sub.add_parser("add")
    add_common(p_add)
    p_add.add_argument("--input", type=Path, action="append", default=[])
    p_add.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    p_add.add_argument("--chunk-overlap", type=int, default=DEFAULT_OVERLAP)
    p_add.add_argument("--batch-size", type=int, default=128)
    p_add.add_argument("--no-optimize", action="store_true")
    p_add.set_defaults(func=cmd_add)

    p_search = sub.add_parser("search")
    add_common(p_search)
    p_search.add_argument("query", nargs="+")
    p_search.add_argument("--topk", "--limit", dest="topk", type=int, default=10)
    p_search.add_argument("--filter")
    p_search.add_argument("--format", choices=["table", "json", "jsonl"], default="table")
    p_search.add_argument("--preview-chars", type=int, default=220)
    p_search.set_defaults(func=cmd_search)

    p_link = sub.add_parser("link-relations")
    add_common(p_link)
    p_link.add_argument("--cluster")
    p_link.add_argument("--source-id", action="append", default=[])
    p_link.add_argument("--predicate", default="related_to")
    p_link.add_argument("--topk", type=int, default=12)
    p_link.add_argument("--limit", type=int, default=50)
    p_link.add_argument("--filter")
    p_link.add_argument("--cross-cluster", action="store_true")
    p_link.add_argument(
        "--direction-mode",
        choices=["infer", "directed", "undirected"],
        default="infer",
    )
    p_link.add_argument("--directed", dest="direction_mode", action="store_const", const="directed")
    p_link.add_argument("--include-registry-evidence", action="store_true")
    p_link.add_argument("--format", choices=["table", "json", "jsonl"], default="table")
    p_link.add_argument("--output", type=Path)
    p_link.add_argument("--append", action="store_true")
    p_link.set_defaults(func=cmd_link_relations)

    p_stats = sub.add_parser("stats")
    add_common(p_stats)
    p_stats.set_defaults(func=cmd_stats)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
