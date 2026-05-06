"""
leiden_cluster.py
Leiden 알고리즘으로 MSM KB 그래프에서 커뮤니티를 자동 탐지한다.

설계 결정:
  - 방향성: DiGraph → undirected 투영 (KB 클러스터링 표준, 방향 정보는 클러스터링 신호로 부적합)
  - Composition 엣지: inferred=True 엣지 제외 — 파생 관계가 아닌 직접 작성한 링크만 반영
  - 클러스터 레이블 안정성: 클러스터 내 최고차수 노드명을 레이블로 사용 (cluster 키)
    + 현재 실행의 정수 인덱스(cluster_idx 키)를 함께 기록
    cluster_idx는 실행마다 재할당될 수 있으므로 쿼리/Dataview는 cluster 키를 사용할 것

사용:
    python3 leiden_cluster.py                        # 리포트만 (write-back 없음)
    python3 leiden_cluster.py --write-back           # frontmatter에 cluster / cluster_idx 기록
    python3 leiden_cluster.py --config path/to/graph-config.yaml
    python3 leiden_cluster.py --min-size 3           # 소형 클러스터 제외 기준
    python3 leiden_cluster.py --report-bridges       # 브릿지 노드 상세 출력
    python3 leiden_cluster.py --json                 # JSON 출력 (파이프 연계용)

의존성:
    pip install leidenalg igraph
    (leidenalg, igraph는 선택적 의존성 — 클러스터링이 필요한 경우만 설치)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

import networkx as nx
import yaml

# graph_builder 임포트 (동일 디렉토리)
_SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from graph_builder import build_graph, load_config  # noqa: E402


# ──────────────────────────────────────────────
# Leiden 실행
# ──────────────────────────────────────────────

def _to_raw_undirected(G: nx.DiGraph) -> nx.Graph:
    """
    composition 추론 엣지(inferred=True)를 제거한 뒤 undirected 투영.
    순수하게 사용자가 작성한 링크만 클러스터링 신호로 사용.
    """
    raw = nx.DiGraph()
    raw.add_nodes_from(G.nodes(data=True))
    for u, v, d in G.edges(data=True):
        if not d.get("inferred", False):
            raw.add_edge(u, v, **d)
    return raw.to_undirected()


def run_leiden(
    G: nx.DiGraph,
    resolution: float = 1.0,
    seed: int = 42,
) -> dict[str, dict]:
    """
    Leiden 알고리즘 실행.

    Returns:
        {
          node_id: {
            "cluster_idx": int,
            "cluster": str (최고차수 노드명 레이블),
          },
          ...
        }
    """
    try:
        import igraph as ig
        import leidenalg
    except ImportError as e:
        raise ImportError(
            f"Leiden 클러스터링에 필요한 패키지가 없습니다: {e}\n"
            "설치: pip install leidenalg igraph"
        ) from e

    G_und = _to_raw_undirected(G)
    nodes = list(G_und.nodes())
    if not nodes:
        return {}

    node_idx = {n: i for i, n in enumerate(nodes)}
    edges = [(node_idx[u], node_idx[v]) for u, v in G_und.edges()]

    ig_graph = ig.Graph(n=len(nodes), edges=edges, directed=False)
    ig_graph.vs["name"] = nodes

    partition = leidenalg.find_partition(
        ig_graph,
        leidenalg.RBConfigurationVertexPartition,
        resolution_parameter=resolution,
        seed=seed,
    )

    # 클러스터별 최고차수 노드 → 안정 레이블
    degree = dict(G_und.degree())
    cluster_labels: dict[int, str] = {}
    for cluster_idx, community in enumerate(partition):
        member_nodes = [nodes[i] for i in community]
        top_node = max(member_nodes, key=lambda n: degree.get(n, 0))
        cluster_labels[cluster_idx] = top_node

    result: dict[str, dict] = {}
    for cluster_idx, community in enumerate(partition):
        label = cluster_labels[cluster_idx]
        for i in community:
            result[nodes[i]] = {
                "cluster_idx": cluster_idx,
                "cluster": label,
            }

    return result


# ──────────────────────────────────────────────
# 리포트
# ──────────────────────────────────────────────

def build_report(
    G: nx.DiGraph,
    assignments: dict[str, dict],
    min_size: int = 1,
    show_bridges: bool = False,
) -> str:
    G_und = _to_raw_undirected(G)

    # 클러스터별 노드 목록
    clusters: dict[int, list[str]] = {}
    for node, info in assignments.items():
        idx = info["cluster_idx"]
        clusters.setdefault(idx, []).append(node)

    # 브릿지 노드 탐지 (2+ 다른 클러스터 이웃을 가진 노드)
    node_cluster = {n: info["cluster_idx"] for n, info in assignments.items()}
    bridges: dict[str, set[int]] = {}
    for node in G_und.nodes():
        if node not in node_cluster:
            continue
        neighbor_clusters = {
            node_cluster[nb]
            for nb in G_und.neighbors(node)
            if nb in node_cluster and node_cluster[nb] != node_cluster[node]
        }
        if neighbor_clusters:
            bridges[node] = neighbor_clusters

    # 고립 노드 (엣지 없음)
    isolated = [n for n in G.nodes() if G.degree(n) == 0]

    lines: list[str] = [
        "=" * 52,
        "  Leiden Cluster Report",
        "=" * 52,
        f"총 클러스터: {len(clusters)}개  |  노드: {len(assignments)}개  |  "
        f"브릿지 노드: {len(bridges)}개  |  고립 노드: {len(isolated)}개",
        "",
    ]

    degree_map = dict(G_und.degree())
    for idx in sorted(clusters.keys()):
        members = clusters[idx]
        if len(members) < min_size:
            continue
        label = assignments[members[0]]["cluster"] if members else str(idx)
        top_members = sorted(members, key=lambda n: degree_map.get(n, 0), reverse=True)[:5]
        top_str = ", ".join(top_members)
        lines.append(f"Cluster {idx:>3}  [{label}]  ({len(members)}개 노드)")
        lines.append(f"  상위 노드: {top_str}")

    lines.append("")
    if bridges and show_bridges:
        lines.append(f"── 브릿지 노드 ({len(bridges)}개) ──────────────────────")
        for node, neighbor_clusters in sorted(bridges.items()):
            nc_str = ", ".join(str(c) for c in sorted(neighbor_clusters))
            lines.append(f"  {node}  ←→  clusters [{nc_str}]")
        lines.append("")

    if isolated:
        lines.append(f"── 고립 노드 ({len(isolated)}개) ──────────────────────")
        lines.append("  " + ", ".join(isolated[:20]))
        if len(isolated) > 20:
            lines.append(f"  ... 외 {len(isolated) - 20}개")
        lines.append("")

    # 합성 노트 후보: 브릿지 노드가 없는 클러스터 쌍
    cluster_set = set(clusters.keys())
    bridged_pairs: set[frozenset[int]] = set()
    for node, neighbor_clusters in bridges.items():
        own = node_cluster[node]
        for nc in neighbor_clusters:
            bridged_pairs.add(frozenset([own, nc]))

    # 대형 클러스터 쌍 중 브릿지 없는 쌍 → synthesis 후보
    large_clusters = [
        idx for idx, members in clusters.items() if len(members) >= max(2, min_size)
    ]
    unconnected: list[tuple[int, int]] = []
    for i, a in enumerate(large_clusters):
        for b in large_clusters[i + 1:]:
            if frozenset([a, b]) not in bridged_pairs:
                unconnected.append((a, b))

    if unconnected:
        lines.append(f"── Synthesis 후보 (브릿지 없는 클러스터 쌍, 상위 5개) ─")
        label_a_b = [
            (
                assignments[clusters[a][0]]["cluster"],
                assignments[clusters[b][0]]["cluster"],
                a, b,
            )
            for a, b in unconnected[:5]
        ]
        for la, lb, a, b in label_a_b:
            lines.append(f"  Cluster {a} [{la}]  ↔  Cluster {b} [{lb}]")
        lines.append("")

    lines.append("=" * 52)
    return "\n".join(lines)


# ──────────────────────────────────────────────
# Write-back
# ──────────────────────────────────────────────

def _upsert_frontmatter_field(text: str, key: str, value) -> str:
    """frontmatter 내 특정 키 값을 upsert — 파일 전체 재직렬화 없이 최소 변경."""
    if not text.startswith("---"):
        return text
    end = text.find("---", 3)
    if end < 0:
        return text
    fm_block = text[3:end]
    body = text[end:]

    serialized = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    pattern = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
    replacement = f"{key}: {serialized}"

    if pattern.search(fm_block):
        fm_block = pattern.sub(replacement, fm_block)
    else:
        fm_block = fm_block.rstrip("\n") + f"\n{replacement}\n"

    return f"---{fm_block}{body}"


def write_back(G: nx.DiGraph, assignments: dict[str, dict], dry_run: bool = False) -> int:
    """
    assignments의 cluster / cluster_idx를 각 노드의 source_file frontmatter에 기록.
    Returns: 수정된 파일 수
    """
    updated = 0
    for node_id, info in assignments.items():
        if node_id not in G.nodes:
            continue
        source_file = G.nodes[node_id].get("source_file")
        if not source_file:
            continue
        filepath = Path(source_file)
        if not filepath.exists():
            continue

        text = filepath.read_text(encoding="utf-8")
        text = _upsert_frontmatter_field(text, "cluster", info["cluster"])
        text = _upsert_frontmatter_field(text, "cluster_idx", info["cluster_idx"])

        if dry_run:
            print(f"  [dry-run] {filepath.name}  →  cluster: {info['cluster']}  cluster_idx: {info['cluster_idx']}")
        else:
            filepath.write_text(text, encoding="utf-8")
        updated += 1

    return updated


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Leiden 커뮤니티 클러스터링 — MSM KB 그래프",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python3 leiden_cluster.py                          # 리포트 출력
  python3 leiden_cluster.py --write-back             # frontmatter 기록
  python3 leiden_cluster.py --dry-run                # 기록 미리보기
  python3 leiden_cluster.py --report-bridges         # 브릿지 노드 상세
  python3 leiden_cluster.py --min-size 3             # 3노드 미만 클러스터 숨김
  python3 leiden_cluster.py --resolution 0.5         # 해상도↓ → 큰 클러스터
  python3 leiden_cluster.py --json > clusters.json   # JSON 출력
        """,
    )
    parser.add_argument("--config", "-c", type=Path, help="graph-config.yaml 경로")
    parser.add_argument("--write-back", action="store_true", help="frontmatter에 cluster / cluster_idx 기록")
    parser.add_argument("--dry-run", action="store_true", help="write-back 대상 미리보기 (실제 기록 없음)")
    parser.add_argument("--min-size", type=int, default=1, metavar="N", help="리포트에 표시할 최소 클러스터 크기 (기본: 1)")
    parser.add_argument("--report-bridges", action="store_true", help="브릿지 노드 상세 출력")
    parser.add_argument("--resolution", type=float, default=1.0, help="Leiden resolution (기본 1.0, ↓ → 큰 클러스터)")
    parser.add_argument("--seed", type=int, default=42, help="난수 시드 (기본 42, 동일 값이면 결과 재현)")
    parser.add_argument("--json", action="store_true", dest="json_out", help="JSON 형식으로 출력")
    args = parser.parse_args()

    print("그래프 로딩 중...", file=sys.stderr)
    G = build_graph(args.config)
    print(f"노드 {G.number_of_nodes()}개  엣지 {G.number_of_edges()}개 로드됨", file=sys.stderr)

    print("Leiden 클러스터링 실행 중...", file=sys.stderr)
    assignments = run_leiden(G, resolution=args.resolution, seed=args.seed)

    if args.json_out:
        print(json.dumps(assignments, ensure_ascii=False, indent=2))
        return

    report = build_report(
        G,
        assignments,
        min_size=args.min_size,
        show_bridges=args.report_bridges,
    )
    print(report)

    if args.write_back or args.dry_run:
        action = "미리보기" if args.dry_run else "기록"
        print(f"\nfrontmatter write-back {action}:", file=sys.stderr)
        count = write_back(G, assignments, dry_run=args.dry_run)
        verb = "대상" if args.dry_run else "완료"
        print(f"{count}개 파일 {action} {verb}.", file=sys.stderr)
        if args.write_back and not args.dry_run:
            print(
                "\n⚠️  cluster_idx는 실행마다 재할당될 수 있습니다.\n"
                "   Dataview / Obsidian 쿼리는 cluster 키(레이블)를 사용하세요.",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
