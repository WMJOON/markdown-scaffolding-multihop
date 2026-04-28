"""
graph_builder.py
Markdown 파일을 NetworkX DiGraph로 변환한다.

사용:
    python3 graph_builder.py                              # 그래프 통계 (config 자동 탐색)
    python3 graph_builder.py --config path/to/graph-config.yaml
    python3 graph_builder.py --search 채널톡
    python3 graph_builder.py --export
"""

import re
import sys
import json
import argparse
import unicodedata
from pathlib import Path
from typing import Optional

import yaml
import networkx as nx

# ──────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────

def nfc(s: str) -> str:
    """macOS HFS+(NFD) ↔ 일반 문자열(NFC) 정규화"""
    return unicodedata.normalize("NFC", s)


# ──────────────────────────────────────────────
# Config 로더
# ──────────────────────────────────────────────

DEFAULT_CONFIG_NAME = "graph-config.yaml"

def find_config(start: Path) -> Optional[Path]:
    """start 디렉토리부터 상위로 올라가며 graph-config.yaml 탐색"""
    for directory in [start, *start.parents]:
        candidate = directory / DEFAULT_CONFIG_NAME
        if candidate.exists():
            return candidate
    return None


def load_config(config_path: Optional[Path] = None) -> tuple[dict, Path]:
    """
    config 로드 후 (config_dict, base_dir) 반환.
    config_path가 None이면 CWD부터 자동 탐색.
    """
    if config_path is None:
        config_path = find_config(Path.cwd())
    if config_path is None:
        # fallback: 스크립트 위치에서 탐색
        config_path = find_config(Path(__file__).parent)
    if config_path is None:
        raise FileNotFoundError(
            f"{DEFAULT_CONFIG_NAME}을 찾지 못했습니다. "
            "--config 옵션으로 경로를 직접 지정하거나 "
            "프로젝트 루트에 graph-config.yaml을 생성하세요."
        )
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    base_dir = config_path.parent
    return cfg, base_dir


def resolve_entity_dirs(cfg: dict, base_dir: Path) -> dict[str, Path]:
    return {
        etype: base_dir / rel_path
        for etype, rel_path in cfg.get("entity_dirs", {}).items()
    }


def resolve_instance_dirs(cfg: dict, base_dir: Path) -> dict[str, Path]:
    """domain → path 매핑 (instance_dirs). type frontmatter로 class 결정."""
    return {
        domain: base_dir / rel_path
        for domain, rel_path in cfg.get("instance_dirs", {}).items()
    }


# ──────────────────────────────────────────────
# 파서
# ──────────────────────────────────────────────

def parse_frontmatter(filepath: Path) -> Optional[dict]:
    """---...--- 블록에서 YAML frontmatter 추출"""
    try:
        text = filepath.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return None
        end = text.find("---", 3)
        if end < 0:
            return None
        return yaml.safe_load(text[3:end]) or {}
    except Exception:
        return None


def parse_body(filepath: Path) -> str:
    """frontmatter 이후 마크다운 본문 반환"""
    try:
        text = filepath.read_text(encoding="utf-8")
        if text.startswith("---"):
            end = text.find("---", 3)
            if end >= 0:
                return text[end + 3:]
        return text
    except Exception:
        return ""


def extract_wikilinks(value) -> list[str]:
    """[[target]] 또는 [[target|alias]] 형태에서 target 추출 (재귀)"""
    if isinstance(value, str):
        return re.findall(r"\[\[([^\]|#]+?)(?:\|[^\]]+)?\]\]", value)
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(extract_wikilinks(item))
        return result
    return []


# ──────────────────────────────────────────────
# 그래프 빌더
# ──────────────────────────────────────────────

def _iter_nodes(cfg: dict, base_dir: Path) -> list[tuple[str, Path]]:
    """(entity_type, md_file) 이터레이터. entity_dirs + instance_dirs 모두 지원."""
    pairs: list[tuple[str, Path]] = []
    # 레거시: entity_dirs (class → path)
    for etype, dir_path in resolve_entity_dirs(cfg, base_dir).items():
        if not dir_path.exists():
            continue
        for md_file in sorted(dir_path.glob("*.md")):
            pairs.append((etype, md_file))
    # 신규: instance_dirs (domain → path, type frontmatter로 class 결정)
    for _domain, dir_path in resolve_instance_dirs(cfg, base_dir).items():
        if not dir_path.exists():
            continue
        for md_file in sorted(dir_path.glob("*.md")):
            fm = parse_frontmatter(md_file)
            etype = (fm or {}).get("type", _domain)
            pairs.append((etype, md_file))
    return pairs


def build_graph(config_path: Optional[Path] = None) -> nx.DiGraph:
    cfg, base_dir = load_config(config_path)
    relation_map  = cfg.get("relation_map", {})
    scalar_attrs  = set(cfg.get("scalar_node_attrs", []))

    G = nx.DiGraph()
    node_pairs = _iter_nodes(cfg, base_dir)

    # ── 1단계: 노드 추가 ──
    for entity_type, md_file in node_pairs:
        fm = parse_frontmatter(md_file)
        if fm is None:
            continue
        node_id = nfc(md_file.stem)
        attrs = {"type": entity_type, "source_file": str(md_file)}
        for field in scalar_attrs:
            if field in fm and fm[field] is not None:
                attrs[field] = fm[field]
        G.add_node(node_id, **attrs)

    # ── 2단계: 엣지 추가 (frontmatter RELATION_MAP 기반) ──
    for _entity_type, md_file in node_pairs:
        fm = parse_frontmatter(md_file)
        if fm is None:
            continue
        src = nfc(md_file.stem)
        for field, relation in relation_map.items():
            if field not in fm:
                continue
            targets = [nfc(t) for t in extract_wikilinks(fm[field])]
            for tgt in targets:
                if G.has_node(tgt):
                    G.add_edge(src, tgt, relation=relation, field=field)

    # ── 3단계: 엣지 추가 (본문 wikilink 기반) ──
    for _entity_type, md_file in node_pairs:
        src = nfc(md_file.stem)
        if not G.has_node(src):
            continue
        body = parse_body(md_file)
        for tgt in [nfc(t) for t in extract_wikilinks(body)]:
            if G.has_node(tgt) and not G.has_edge(src, tgt):
                G.add_edge(src, tgt, relation="links_to", field="body")

    # ── 4단계: 범주론적 합성 추론 (opt-in) ──
    inferred = infer_compositions(G, cfg, base_dir)
    if inferred > 0:
        print(f"[categorical] 합성 추론 엣지 {inferred}개 추가", file=sys.stderr)

    return G


# ──────────────────────────────────────────────
# Categorical Composition (범주론적 합성 추론)
# ──────────────────────────────────────────────

_COMP_COL_INDEX = {"causes": 0, "requires": 1, "constrains": 2, "informs": 3}


def _load_ontology(cfg: dict, base_dir: Path) -> Optional[dict]:
    """graph-ontology.yaml 로드 (composition_table이 있을 때만 반환)"""
    if "composition_table" in cfg:
        return cfg
    for name in ("graph-ontology.yaml", "graph-ontology.yml"):
        p = base_dir / name
        if p.exists():
            with open(p, encoding="utf-8") as f:
                onto = yaml.safe_load(f)
            if onto and "composition_table" in onto:
                return onto
    return None


def infer_compositions(
    G: nx.DiGraph,
    cfg: dict,
    base_dir: Path,
    max_hops: int = 3,
) -> int:
    """
    범주론적 합성 추론으로 새로운 엣지를 자동 도출한다.
    composition_table이 config/ontology에 없으면 아무것도 하지 않는다 (opt-in).

    Returns: 추가된 합성 엣지 수
    """
    onto = _load_ontology(cfg, base_dir)
    if onto is None:
        return 0

    comp_table = onto["composition_table"]
    transitive_types = {
        mt for mt, props in onto.get("morphism_types", {}).items()
        if props.get("transitive", True)
    }

    added = 0
    for _ in range(max_hops - 1):
        cat_edges = [
            (u, v, d["relation"])
            for u, v, d in G.edges(data=True)
            if d.get("relation") in transitive_types
        ]
        if not cat_edges:
            break

        new_edges: list[tuple[str, str, dict]] = []
        for u1, v1, f_type in cat_edges:
            if f_type not in comp_table:
                continue
            for u2, v2, g_type in cat_edges:
                if v1 != u2 or u1 == v2:
                    continue
                col_idx = _COMP_COL_INDEX.get(g_type)
                if col_idx is None:
                    continue
                # direct edge takes precedence
                if G.has_edge(u1, v2) and not G.edges[u1, v2].get("inferred"):
                    continue
                if G.has_edge(u1, v2):
                    continue
                new_edges.append((u1, v2, {
                    "relation": comp_table[f_type][col_idx],
                    "inferred": True,
                    "via": f"{u1}→{v1}→{v2}",
                    "composition": f"{f_type} ∘ {g_type}",
                    "field": "composition",
                }))

        if not new_edges:
            break
        for u, v, d in new_edges:
            if not G.has_edge(u, v):
                G.add_edge(u, v, **d)
                added += 1

    return added


# ──────────────────────────────────────────────
# 요약 / 직렬화
# ──────────────────────────────────────────────

def summarize(G: nx.DiGraph) -> str:
    type_counts: dict[str, int] = {}
    for _, data in G.nodes(data=True):
        t = data.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    rel_counts: dict[str, int] = {}
    for _, _, data in G.edges(data=True):
        r = data.get("relation", "unknown")
        rel_counts[r] = rel_counts.get(r, 0) + 1

    lines = [
        f"노드: {G.number_of_nodes()}개  엣지: {G.number_of_edges()}개",
        "",
        "[ 노드 타입 ]",
    ]
    for t, cnt in sorted(type_counts.items()):
        lines.append(f"  {t:25s} {cnt:3d}개")
    lines += ["", "[ 엣지 relation ]"]
    for r, cnt in sorted(rel_counts.items()):
        lines.append(f"  {r:30s} {cnt:3d}개")

    # 합성 엣지 통계 (단일 패스)
    inferred = [(u, v, d) for u, v, d in G.edges(data=True) if d.get("inferred")]
    if inferred:
        lines += ["", f"[ 합성 추론 (categorical) ] {len(inferred)}개"]
        for _, _, d in inferred:
            lines.append(f"  {d.get('via','')}  ({d.get('composition','')} → {d.get('relation','')})")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# 공개 인터페이스
# ──────────────────────────────────────────────

def get_graph(config_path: Optional[Path] = None) -> nx.DiGraph:
    """다른 모듈에서 import해서 사용"""
    return build_graph(config_path)


def get_subgraph(G: nx.DiGraph, start_nodes: list[str], hops: int = 2) -> nx.DiGraph:
    """start_nodes 기준 BFS N-hop 서브그래프 반환"""
    visited: set[str] = set()
    frontier = set(n for n in start_nodes if G.has_node(n))
    for _ in range(hops):
        next_frontier: set[str] = set()
        for node in frontier:
            visited.add(node)
            next_frontier.update(G.successors(node))
            next_frontier.update(G.predecessors(node))
        frontier = next_frontier - visited
        visited.update(frontier)
    return G.subgraph(visited)


def find_nodes_by_keyword(G: nx.DiGraph, keyword: str) -> list[str]:
    """node_id 또는 name 속성에서 키워드 검색"""
    kw = nfc(keyword.lower())
    results = []
    for node_id, data in G.nodes(data=True):
        name = nfc(str(data.get("name", "")).lower())
        if kw in node_id.lower() or kw in name:
            results.append(node_id)
    return results


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Markdown 파일 → NetworkX 그래프 빌더")
    parser.add_argument("--config", "-c", type=Path, help="graph-config.yaml 경로 (생략 시 자동 탐색)")
    parser.add_argument("--export", action="store_true", help="graph.json 내보내기")
    parser.add_argument("--search", metavar="KEYWORD", help="노드 검색")
    args = parser.parse_args()

    G = build_graph(args.config)
    print(summarize(G))

    if args.export:
        out = Path(args.config).parent / "graph.json" if args.config else Path("graph.json")
        data = nx.node_link_data(G)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"내보내기 완료: {out}")

    if args.search:
        matches = find_nodes_by_keyword(G, args.search)
        print(f"\n검색 결과 ({args.search!r}): {len(matches)}개")
        for m in matches:
            d = G.nodes[m]
            print(f"  {m}  [{d.get('type','')}] {d.get('name','')}")
