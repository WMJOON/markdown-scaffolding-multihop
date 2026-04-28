"""
Mode B: MD 엔티티 디렉토리 → Triple Export + KG 분석 리포트

출력:
  - triples.jsonl      : (subject_id, predicate, object_id) 전체 Triple
  - entities.jsonl     : 엔티티 목록 (id, type, label_en)
  - report.md          : 그래프 통계 + 연결성 분석 리포트
  - ontology.ttl       : Turtle 직렬화 (rdflib 표준)
  - [--embed] embed_report.md : 유사도 상위 쌍 목록
"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from core.triple_graph import TripleGraph
from core.md_to_triple import load_entity_dir, entity_feature_dict
from core.jsonl_io import write_jsonl_stream

logger = logging.getLogger(__name__)


# ─── 진입점 ───────────────────────────────────────────────────────────────────

def run_export(
    input_path:  Path,
    output:      str | None,
    use_embed:   bool,
    embed_model: str,
):
    logger.info("[Mode B] Export 시작: %s", input_path)
    print(f"[Mode B] 입력 디렉토리: {input_path}")

    # 출력 디렉토리
    out_dir = Path(output) if output else input_path.parent / "export"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[Mode B] 출력: {out_dir}")

    # ── MD → TripleGraph 로드 ─────────────────────────────────────────────────
    graph = TripleGraph()
    n_entities = load_entity_dir(input_path, graph)
    triples    = list(graph.iter_relations())
    print(f"[Mode B] 엔티티 {n_entities}개, Triple {len(triples)}개 로드")

    # ── 출력 1: triples.jsonl ─────────────────────────────────────────────────
    write_jsonl_stream(
        ({"subject": s, "predicate": p, "object": o} for s, p, o in triples),
        out_dir / "triples.jsonl",
    )
    print(f"[Mode B] triples.jsonl: {len(triples)}행")

    # ── 출력 2: entities.jsonl ────────────────────────────────────────────────
    entity_list = list(graph.iter_entities())
    write_jsonl_stream(
        ({"entity_id": eid, "entity_type": etype, "label_en": graph.get_label_en(eid)}
         for _, eid, etype in entity_list),
        out_dir / "entities.jsonl",
    )
    print(f"[Mode B] entities.jsonl: {len(entity_list)}행")

    # ── 출력 3: ontology.ttl ──────────────────────────────────────────────────
    ttl_path = out_dir / "ontology.ttl"
    ttl_path.write_text(graph.serialize("turtle"), encoding="utf-8")
    print(f"[Mode B] ontology.ttl 저장")

    # ── 출력 4: report.md ─────────────────────────────────────────────────────
    report = _build_report(graph, entity_list, triples, out_dir)
    report_path = out_dir / "report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"[Mode B] report.md 저장")

    # ── 출력 5: [선택] KG Embedding 분석 ─────────────────────────────────────
    if use_embed:
        print(f"[Mode B] KG Embedding 실행: {embed_model}")
        _run_embed_analysis(graph, embed_model, out_dir)
    else:
        print("[Mode B] KG Embedding 비활성화 (--embed 플래그로 활성화 가능)")

    print(f"\n[Mode B] 완료 → {out_dir}")


# ─── 그래프 분석 리포트 ───────────────────────────────────────────────────────

def _build_report(
    graph:       TripleGraph,
    entity_list: list,
    triples:     list[tuple[str, str, str]],
    out_dir:     Path,
) -> str:
    today = date.today().isoformat()

    # 타입별 집계
    type_counter: Counter = Counter()
    for _, eid, etype in entity_list:
        type_counter[etype] += 1

    # 관계 타입 집계
    rel_counter: Counter = Counter()
    for _, pred, _ in triples:
        rel_counter[pred] += 1

    # In-degree / Out-degree
    in_deg:  dict[str, int] = defaultdict(int)
    out_deg: dict[str, int] = defaultdict(int)
    for s, _, o in triples:
        out_deg[s] += 1
        in_deg[o]  += 1

    all_eids    = [eid for _, eid, _ in entity_list]
    max_out     = max((out_deg[e] for e in all_eids), default=0)
    max_in      = max((in_deg[e]  for e in all_eids), default=0)
    avg_out     = sum(out_deg[e] for e in all_eids) / len(all_eids) if all_eids else 0
    isolated    = sum(1 for e in all_eids if out_deg[e] == 0 and in_deg[e] == 0)

    # 허브 노드 (out-degree 상위 10)
    hubs = sorted(all_eids, key=lambda e: out_deg[e], reverse=True)[:10]

    lines = [
        f"# Ontology Export Report",
        f"",
        f"> 생성일: {today}  |  출력: `{out_dir}`",
        f"",
        f"## 기본 통계",
        f"",
        f"| 항목 | 값 |",
        f"|---|---|",
        f"| 총 엔티티 수 | {len(entity_list)} |",
        f"| 총 Triple 수 | {len(triples)} |",
        f"| 관계 유형 수 | {len(rel_counter)} |",
        f"| 고립 엔티티 (연결 없음) | {isolated} |",
        f"| 최대 out-degree | {max_out} |",
        f"| 최대 in-degree  | {max_in} |",
        f"| 평균 out-degree | {avg_out:.2f} |",
        f"",
        f"## 엔티티 타입별 분포",
        f"",
        f"| entity_type | 수 |",
        f"|---|---|",
    ]
    for etype, cnt in type_counter.most_common():
        lines.append(f"| {etype} | {cnt} |")

    lines += [
        f"",
        f"## 관계 타입별 빈도 (상위 20)",
        f"",
        f"| relation_type | 수 |",
        f"|---|---|",
    ]
    for pred, cnt in rel_counter.most_common(20):
        lines.append(f"| {pred} | {cnt} |")

    lines += [
        f"",
        f"## 허브 엔티티 (out-degree 상위 10)",
        f"",
        f"| entity_id | out-degree | in-degree |",
        f"|---|---|---|",
    ]
    for eid in hubs:
        lines.append(f"| {eid} | {out_deg[eid]} | {in_deg[eid]} |")

    lines += [
        f"",
        f"## 출력 파일",
        f"",
        f"| 파일 | 설명 |",
        f"|---|---|",
        f"| `triples.jsonl` | (subject, predicate, object) 전체 Triple |",
        f"| `entities.jsonl` | 엔티티 목록 (id, type, label) |",
        f"| `ontology.ttl` | Turtle 직렬화 |",
        f"| `report.md` | 이 파일 |",
    ]

    return "\n".join(lines) + "\n"


# ─── KG Embedding 분석 ────────────────────────────────────────────────────────

def _run_embed_analysis(
    graph:       TripleGraph,
    embed_model: str,
    out_dir:     Path,
):
    from embed.kg_embed import build_embedder, EmbedModel

    try:
        embedder = build_embedder(embed_model, graph)  # type: ignore[arg-type]
    except Exception as e:
        logger.error("[Mode B] Embedder 생성 실패: %s", e)
        print(f"[ERROR] Embedding 실패: {e}")
        return

    entity_list = list(graph.iter_entities())
    if not entity_list:
        return

    from embed.kg_embed import TFIDFEmbedder, SemanticEmbedder, HybridEmbedder
    if isinstance(embedder, HybridEmbedder):
        _semantic_similarity_report(embedder, entity_list, graph, out_dir, "Hybrid")
    elif isinstance(embedder, SemanticEmbedder):
        _semantic_similarity_report(embedder, entity_list, graph, out_dir, "Semantic")
    elif isinstance(embedder, TFIDFEmbedder):
        _tfidf_similarity_report(embedder, entity_list, graph, out_dir)
    else:
        _pykeen_similarity_report(embedder, entity_list, graph, out_dir)


def _tfidf_similarity_report(
    embedder,
    entity_list: list,
    graph:       TripleGraph,
    out_dir:     Path,
    top_k:       int = 5,
):
    lines = [
        "# KG Embedding 유사도 리포트 (TF-IDF)",
        "",
        f"> 생성일: {date.today().isoformat()}",
        "",
        "## 엔티티별 상위 유사 엔티티",
        "",
    ]
    for _, eid, etype in entity_list[:100]:   # 최대 100개
        feat     = entity_feature_dict(eid, graph)
        top      = embedder.top_k(feat["feature_text"], k=top_k + 1)
        filtered = [(e, s) for e, s in top if e != eid][:top_k]

        lines.append(f"### `{eid}` ({etype})")
        for sim_eid, sim in filtered:
            lines.append(f"  - `{sim_eid}` : {sim:.4f}")
        lines.append("")

    report_path = out_dir / "embed_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[Mode B] embed_report.md 저장 (TF-IDF, {min(100, len(entity_list))}개)")


def _semantic_similarity_report(
    embedder,
    entity_list: list,
    graph:       TripleGraph,
    out_dir:     Path,
    backend_label: str = "Semantic",
    top_k:       int = 5,
):
    lines = [
        f"# KG Embedding 유사도 리포트 ({backend_label})",
        "",
        f"> 생성일: {date.today().isoformat()}",
        "",
        "## 엔티티별 상위 유사 엔티티",
        "",
    ]
    for _, eid, etype in entity_list[:100]:
        feat = entity_feature_dict(eid, graph)
        top  = embedder.top_k(feat["feature_text"], k=top_k + 1)
        filtered = [(e, s) for e, s in top if e != eid][:top_k]

        lines.append(f"### `{eid}` ({etype})")
        for sim_eid, sim in filtered:
            lines.append(f"  - `{sim_eid}` : {sim:.4f}")
        lines.append("")

    report_path = out_dir / "embed_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[Mode B] embed_report.md 저장 ({backend_label}, {min(100, len(entity_list))}개)")


def _pykeen_similarity_report(
    embedder,
    entity_list: list,
    graph:       TripleGraph,
    out_dir:     Path,
    top_k:       int = 5,
):
    lines = [
        "# KG Embedding 유사도 리포트 (PyKEEN)",
        "",
        f"> 생성일: {date.today().isoformat()}",
        "",
    ]
    for _, eid, etype in entity_list[:50]:
        ranked   = embedder.cosine_similarity_to(eid)[:top_k]
        lines.append(f"### `{eid}` ({etype})")
        for sim_eid, sim in ranked:
            lines.append(f"  - `{sim_eid}` : {sim:.4f}")
        lines.append("")

    report_path = out_dir / "embed_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[Mode B] embed_report.md 저장 (PyKEEN, {min(50, len(entity_list))}개)")
