#!/usr/bin/env python3
"""
zvec_graph_index.py
graph_builder.py가 구축한 NetworkX 그래프 노드를 zvec에 인덱싱하고
시맨틱 벡터 검색으로 관련 노드를 탐색한다.

사용:
    python3 zvec_graph_index.py index                          # 그래프 노드 인덱싱
    python3 zvec_graph_index.py search "경쟁사 시장 전략"       # 시맨틱 검색
    python3 zvec_graph_index.py stats                          # collection 상태
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import textwrap
from pathlib import Path
from typing import Any, Sequence

import zvec

# ─── 상수 ───────────────────────────────────────
DEFAULT_COLLECTION_PATH = "/tmp/md-graph-zvec"
DEFAULT_COLLECTION_NAME = "md_graph_nodes"
DEFAULT_VECTOR_FIELD = "dense_embedding"
DEFAULT_DIMENSION = 384
DEFAULT_BODY_MAX_CHARS = 500
UPSERT_BATCH_SIZE = 512

SKIP_NODE_ATTRS = {"source_file", "type"}

_zvec_initialized = False


# ─── graph_builder import ───────────────────────
_gb_module = None


def _import_graph_builder():
    """sibling skill의 graph_builder를 동적 import — 패키지 설치 없이 사용"""
    global _gb_module
    if _gb_module is not None:
        return _gb_module
    multihop_scripts = Path(__file__).resolve().parent.parent.parent / "md-graph-multihop" / "scripts"
    path_str = str(multihop_scripts)
    if multihop_scripts.exists() and path_str not in sys.path:
        sys.path.insert(0, path_str)
    import graph_builder
    _gb_module = graph_builder
    return graph_builder


# ─── zvec init ──────────────────────────────────
def _ensure_zvec_init() -> None:
    global _zvec_initialized
    if not _zvec_initialized:
        zvec.init(log_level=zvec.LogLevel.WARN)
        _zvec_initialized = True


# ─── 유틸 ───────────────────────────────────────
def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _ensure_no_space_path(path: Path) -> None:
    if " " in str(path):
        raise ValueError(
            f"zvec collection path에 공백이 포함됨: {path}\n"
            "공백 없는 경로를 사용하세요 (예: /tmp/md-graph-zvec)."
        )


def _l2_normalize(values: Sequence[float]) -> list[float]:
    norm = sum(v * v for v in values) ** 0.5
    if norm == 0:
        return [0.0 for _ in values]
    return [float(v / norm) for v in values]


def _hash_embed(text: str, dimension: int) -> list[float]:
    """결정적 오프라인 해시 임베딩 — 한국어 토큰 포함"""
    normalized = _normalize_text(text).lower()
    tokens = re.findall(r"[a-z0-9가-힣_]+", normalized) or [normalized or "empty"]
    vector = [0.0] * dimension
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for i, byte_value in enumerate(digest):
            index = (byte_value + (i * 17)) % dimension
            sign = 1.0 if digest[(i + 11) % 32] % 2 == 0 else -1.0
            magnitude = 0.25 + (digest[(i + 3) % 32] / 255.0)
            vector[index] += sign * magnitude
    return _l2_normalize(vector)


def _quote_sql(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


# ─── embedder ───────────────────────────────────
def _resolve_extension_class(module: Any, candidates: Sequence[str]) -> Any | None:
    embedded_mod = getattr(module, "embedding", None)
    for class_name in candidates:
        cls = getattr(module, class_name, None)
        if cls is None and embedded_mod is not None:
            cls = getattr(embedded_mod, class_name, None)
        if cls is not None:
            return cls
    return None


def _prepare_embedder(kind: str, dimension: int) -> tuple[Any | None, str]:
    if kind == "hash":
        return None, "hash"

    import zvec.extension as zext

    if kind == "local":
        cls = _resolve_extension_class(zext, ["DefaultLocalDenseEmbedding"])
        if cls is None:
            raise RuntimeError("DefaultLocalDenseEmbedding not available in zvec.extension")
        return cls(), cls.__name__

    if kind == "openai":
        cls = _resolve_extension_class(zext, ["OpenAIDenseEmbedding"])
        if cls is None:
            raise RuntimeError("OpenAIDenseEmbedding not available in zvec.extension")
        try:
            return cls(dimension=dimension), cls.__name__
        except TypeError:
            return cls(), cls.__name__

    if kind == "qwen":
        cls = _resolve_extension_class(zext, ["QwenDenseEmbedding", "QwenEmbeddingFunction"])
        if cls is None:
            raise RuntimeError("QwenDenseEmbedding not available in zvec.extension")
        try:
            return cls(dimension), cls.__name__
        except TypeError:
            return cls(dimension=dimension), cls.__name__

    raise ValueError(f"unsupported embedder: {kind}")


def _coerce_vector(raw_vector: Any, dimension: int) -> list[float]:
    if hasattr(raw_vector, "tolist"):
        raw_vector = raw_vector.tolist()
    if isinstance(raw_vector, list) and raw_vector and isinstance(raw_vector[0], (list, tuple)):
        if len(raw_vector) != 1:
            raise ValueError("embedder returned nested vectors; expected a single vector")
        raw_vector = raw_vector[0]
    if not isinstance(raw_vector, (list, tuple)):
        raise ValueError(f"embedder output type is not a vector: {type(raw_vector).__name__}")
    vector = [float(value) for value in raw_vector]
    if len(vector) != dimension:
        raise ValueError(f"embedding dimension mismatch: expected {dimension}, got {len(vector)}")
    return vector


def _embed_text(text: str, *, kind: str, embedder: Any | None, dimension: int) -> list[float]:
    if kind == "hash":
        return _hash_embed(text, dimension)
    if embedder is None:
        raise RuntimeError("embedder is not initialized")
    return _coerce_vector(embedder.embed(text), dimension)


# ─── 노드 텍스트 구성 ──────────────────────────
def _node_to_text(
    node_id: str,
    data: dict[str, Any],
    *,
    include_body: bool = False,
    body_max_chars: int = DEFAULT_BODY_MAX_CHARS,
) -> str:
    """노드 속성을 검색용 단일 텍스트로 직렬화"""
    parts: list[str] = []

    name = data.get("name", node_id)
    parts.append(name)

    entity_type = data.get("type", "")
    if entity_type:
        parts.append(f"[{entity_type}]")

    for key, value in data.items():
        if key in SKIP_NODE_ATTRS or key == "name" or value is None:
            continue
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value)
        parts.append(f"{key}: {value}")

    if include_body:
        source_file = data.get("source_file")
        if source_file:
            try:
                gb = _import_graph_builder()
                body = _normalize_text(gb.parse_body(Path(source_file)))[:body_max_chars]
                if body:
                    parts.append(body)
            except Exception:
                pass

    return " ".join(parts)


# ─── zvec collection 관리 ───────────────────────
def _metric_type(metric: str) -> Any:
    mapping = {
        "cosine": zvec.MetricType.COSINE,
        "l2": zvec.MetricType.L2,
        "ip": zvec.MetricType.IP,
    }
    return mapping[metric]


def _create_schema(name: str, vector_field: str, dimension: int, metric: str = "cosine") -> Any:
    vector = zvec.VectorSchema(
        vector_field,
        zvec.DataType.VECTOR_FP32,
        dimension,
        zvec.HnswIndexParam(metric_type=_metric_type(metric)),
    )
    fields = [
        zvec.FieldSchema("node_id", zvec.DataType.STRING),
        zvec.FieldSchema("name", zvec.DataType.STRING, nullable=True),
        zvec.FieldSchema("entity_type", zvec.DataType.STRING, nullable=True),
        zvec.FieldSchema("text", zvec.DataType.STRING),
        zvec.FieldSchema("source_file", zvec.DataType.STRING, nullable=True),
    ]
    return zvec.CollectionSchema(name=name, fields=fields, vectors=[vector])


def _open_collection(path: Path, *, read_only: bool) -> Any:
    _ensure_no_space_path(path)
    if not path.exists():
        raise FileNotFoundError(f"collection이 없음: {path}\n먼저 'index' 명령으로 빌드하세요.")
    option = zvec.CollectionOption(read_only=read_only, enable_mmap=True)
    return zvec.open(path=str(path), option=option)


def _field_value(doc: Any, key: str) -> Any:
    if hasattr(doc, "has_field") and doc.has_field(key):
        return doc.field(key)
    fields = getattr(doc, "fields", None) or {}
    return fields.get(key)


# ═══════════════════════════════════════════════
# 검색 코어 — CLI와 공개 API가 공유
# ═══════════════════════════════════════════════

def _query_collection(
    collection_path: str,
    query: str,
    *,
    embedder_kind: str = "hash",
    dimension: int = DEFAULT_DIMENSION,
    entity_type: str | None = None,
    top_k: int = 5,
) -> list[Any] | None:
    """zvec collection에 벡터 질의를 수행하고 raw 결과 반환."""
    _ensure_zvec_init()
    path = Path(collection_path)
    if not path.exists():
        return None

    collection = _open_collection(path, read_only=True)
    embedder, _ = _prepare_embedder(embedder_kind, dimension)

    gb = _import_graph_builder()
    query_vector = _embed_text(
        _normalize_text(gb.nfc(query)),
        kind=embedder_kind,
        embedder=embedder,
        dimension=dimension,
    )

    filter_expr = None
    if entity_type:
        filter_expr = f"entity_type = {_quote_sql(entity_type)}"

    return collection.query(
        vectors=zvec.VectorQuery(DEFAULT_VECTOR_FIELD, vector=query_vector),
        topk=top_k,
        filter=filter_expr,
        output_fields=None,
        include_vector=False,
    )


# ═══════════════════════════════════════════════
# 공개 API — Python import용
# ═══════════════════════════════════════════════

def find_relevant_nodes_zvec(
    query: str,
    top_k: int = 5,
    collection_path: str = DEFAULT_COLLECTION_PATH,
    embedder_kind: str = "hash",
    dimension: int = DEFAULT_DIMENSION,
    entity_type: str | None = None,
) -> list[str]:
    """
    zvec 시맨틱 검색으로 관련 노드 ID 리스트 반환.
    graph_rag.py의 find_relevant_nodes() 드롭인 대체용.
    """
    results = _query_collection(
        collection_path, query,
        embedder_kind=embedder_kind,
        dimension=dimension,
        entity_type=entity_type,
        top_k=top_k,
    )
    node_ids: list[str] = []
    for doc in results or []:
        nid = _field_value(doc, "node_id")
        if nid:
            node_ids.append(str(nid))
    return node_ids


def find_relevant_nodes_hybrid(
    G: Any,
    query: str,
    top_k: int = 5,
    collection_path: str = DEFAULT_COLLECTION_PATH,
    embedder_kind: str = "hash",
    dimension: int = DEFAULT_DIMENSION,
    zvec_weight: float = 0.7,
) -> list[str]:
    """
    zvec 벡터 검색 + 기존 keyword matching을 결합한 하이브리드 검색.
    zvec_weight: zvec 점수 비중 (0.0~1.0). 나머지는 keyword.
    """
    gb = _import_graph_builder()

    zvec_nodes = find_relevant_nodes_zvec(
        query, top_k=top_k * 2,
        collection_path=collection_path,
        embedder_kind=embedder_kind,
        dimension=dimension,
    )
    keyword_nodes = gb.find_nodes_by_keyword(G, query)

    # RRF 기반 점수 병합
    scores: dict[str, float] = {}
    for rank, nid in enumerate(zvec_nodes):
        scores[nid] = scores.get(nid, 0.0) + zvec_weight * (1.0 / (rank + 1))
    for rank, nid in enumerate(keyword_nodes):
        scores[nid] = scores.get(nid, 0.0) + (1.0 - zvec_weight) * (1.0 / (rank + 1))

    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return [nid for nid, _ in ranked[:top_k]]


# ═══════════════════════════════════════════════
# CLI: index
# ═══════════════════════════════════════════════

def cmd_index(args: argparse.Namespace) -> int:
    _ensure_zvec_init()
    gb = _import_graph_builder()

    print("그래프 로딩 중...", end=" ", flush=True)
    G = gb.build_graph(Path(args.config) if args.config else None)
    print(f"완료 ({G.number_of_nodes()}노드 / {G.number_of_edges()}엣지)")

    if G.number_of_nodes() == 0:
        print("[index] 그래프에 노드가 없습니다.", file=sys.stderr)
        return 2

    collection_path = Path(args.collection)
    _ensure_no_space_path(collection_path)

    if args.force and collection_path.exists():
        import shutil
        shutil.rmtree(collection_path)
        print(f"[index] 기존 collection 삭제: {collection_path}")

    if collection_path.exists():
        collection = _open_collection(collection_path, read_only=False)
        print(f"[index] 기존 collection 열기: {collection_path}")
    else:
        collection_path.parent.mkdir(parents=True, exist_ok=True)
        schema = _create_schema(
            name=DEFAULT_COLLECTION_NAME,
            vector_field=DEFAULT_VECTOR_FIELD,
            dimension=args.dimension,
        )
        option = zvec.CollectionOption(read_only=False, enable_mmap=True)
        collection = zvec.create_and_open(path=str(collection_path), schema=schema, option=option)
        print(f"[index] 새 collection 생성: {collection_path}")

    embedder, embedder_name = _prepare_embedder(args.embedder, args.dimension)
    print(f"[index] embedder={embedder_name} dimension={args.dimension}")

    batch: list[Any] = []
    total = 0
    for node_id, data in G.nodes(data=True):
        text = _node_to_text(
            node_id, data,
            include_body=args.include_body,
            body_max_chars=args.body_max_chars,
        )
        vector = _embed_text(text, kind=args.embedder, embedder=embedder, dimension=args.dimension)

        fields: dict[str, Any] = {
            "node_id": node_id,
            "text": text,
        }
        name = data.get("name")
        if name:
            fields["name"] = str(name)
        entity_type = data.get("type")
        if entity_type:
            fields["entity_type"] = str(entity_type)
        source_file = data.get("source_file")
        if source_file:
            fields["source_file"] = str(source_file)

        doc_id = hashlib.sha1(node_id.encode("utf-8")).hexdigest()[:20]
        batch.append(
            zvec.Doc(
                id=doc_id,
                fields=fields,
                vectors={DEFAULT_VECTOR_FIELD: vector},
            )
        )

        if len(batch) >= UPSERT_BATCH_SIZE:
            collection.upsert(batch)
            total += len(batch)
            batch.clear()

    if batch:
        collection.upsert(batch)
        total += len(batch)

    collection.optimize()
    collection.flush()

    print(f"[index] {total}개 노드 인덱싱 완료")
    print(f"[index] collection={collection_path}")
    return 0


# ═══════════════════════════════════════════════
# CLI: search
# ═══════════════════════════════════════════════

def cmd_search(args: argparse.Namespace) -> int:
    query_text = " ".join(args.query).strip()
    if not query_text:
        print("[search] 검색어를 입력하세요.", file=sys.stderr)
        return 2

    results = _query_collection(
        args.collection, query_text,
        embedder_kind=args.embedder,
        dimension=args.dimension,
        entity_type=args.entity_type,
        top_k=args.limit,
    )

    if args.top1:
        if results:
            nid = _field_value(results[0], "node_id")
            print(nid or "", end="")
        return 0

    if args.json_output:
        entries = []
        for doc in results or []:
            entries.append({
                "node_id": _field_value(doc, "node_id"),
                "name": _field_value(doc, "name"),
                "entity_type": _field_value(doc, "entity_type"),
                "score": getattr(doc, "score", None),
            })
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return 0

    print(f"[search] query={query_text!r}")
    print(f"[search] collection={args.collection}")

    if not results:
        print("[search] 결과 없음")
        return 0

    for idx, doc in enumerate(results, 1):
        score = getattr(doc, "score", None)
        score_text = f"{score:.6f}" if isinstance(score, (int, float)) else str(score)
        node_id = _field_value(doc, "node_id")
        name = _field_value(doc, "name")
        entity_type = _field_value(doc, "entity_type")
        text = _field_value(doc, "text")
        print(f"[{idx}] node_id={node_id}  score={score_text}")
        if name:
            print(f"    name: {name}")
        if entity_type:
            print(f"    type: {entity_type}")
        if isinstance(text, str):
            stripped = text.strip()
            if stripped:
                snippet = stripped[:200] + ("..." if len(stripped) > 200 else "")
                print(f"    text: {snippet}")

    return 0


# ═══════════════════════════════════════════════
# CLI: stats
# ═══════════════════════════════════════════════

def cmd_stats(args: argparse.Namespace) -> int:
    _ensure_zvec_init()
    collection_path = Path(args.collection)
    collection = _open_collection(collection_path, read_only=True)
    schema = collection.schema
    print(f"[stats] collection={collection_path}")
    print(f"[stats] name={schema.name}")
    print(f"[stats] fields={', '.join(f.name for f in schema.fields)}")
    for v in schema.vectors:
        print(f"[stats] vector={v.name} dimension={v.dimension}")
    print(f"[stats] doc_count={collection.stats.doc_count}")
    print(f"[stats] index_completeness={dict(collection.stats.index_completeness)}")
    return 0


# ═══════════════════════════════════════════════
# CLI parser
# ═══════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zvec_graph_index.py",
        description="zvec 기반 그래프 노드 시맨틱 검색",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            예시:
              python3 zvec_graph_index.py index
              python3 zvec_graph_index.py search "경쟁사 분석"
              python3 zvec_graph_index.py stats
        """),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── index ──
    p_index = subparsers.add_parser("index", help="그래프 노드를 zvec에 인덱싱")
    p_index.add_argument("--config", "-c", help="graph-config.yaml 경로 (생략 시 자동 탐색)")
    p_index.add_argument("--collection", default=DEFAULT_COLLECTION_PATH, help="zvec collection 경로")
    p_index.add_argument(
        "--embedder",
        choices=["hash", "local", "openai", "qwen"],
        default="hash",
        help="임베딩 백엔드 (기본: hash)",
    )
    p_index.add_argument("--dimension", type=int, default=DEFAULT_DIMENSION, help="벡터 차원 (기본: 384)")
    p_index.add_argument("--include-body", action="store_true", help="노드 본문도 인덱싱에 포함")
    p_index.add_argument("--body-max-chars", type=int, default=DEFAULT_BODY_MAX_CHARS, help="본문 최대 문자 수")
    p_index.add_argument("--force", action="store_true", help="기존 collection 삭제 후 재빌드")
    p_index.set_defaults(func=cmd_index)

    # ── search ──
    p_search = subparsers.add_parser("search", help="시맨틱 노드 검색")
    p_search.add_argument("query", nargs="+", help="검색 질의")
    p_search.add_argument("--collection", default=DEFAULT_COLLECTION_PATH, help="zvec collection 경로")
    p_search.add_argument(
        "--embedder",
        choices=["hash", "local", "openai", "qwen"],
        default="hash",
        help="검색 embedder (인덱싱과 동일해야 함)",
    )
    p_search.add_argument("--dimension", type=int, default=DEFAULT_DIMENSION, help="벡터 차원")
    p_search.add_argument("--limit", type=int, default=5, help="Top-K (기본: 5)")
    p_search.add_argument("--entity-type", help="entity type 필터")
    p_search.add_argument("--top1", action="store_true", help="최상위 1개 노드 ID만 출력")
    p_search.add_argument("--json", dest="json_output", action="store_true", help="JSON 출력")
    p_search.set_defaults(func=cmd_search)

    # ── stats ──
    p_stats = subparsers.add_parser("stats", help="collection 상태 확인")
    p_stats.add_argument("--collection", default=DEFAULT_COLLECTION_PATH, help="zvec collection 경로")
    p_stats.set_defaults(func=cmd_stats)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr, flush=True)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
