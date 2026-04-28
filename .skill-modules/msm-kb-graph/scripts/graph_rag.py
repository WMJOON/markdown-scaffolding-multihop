"""
graph_rag.py
LangChain + NetworkX 기반 Graph RAG CLI.
Markdown 지식 베이스 entity 그래프 위에서 멀티홉 자연어 질의를 수행한다.

사용:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 graph_rag.py --query "X가 Y에 미치는 영향을 그래프 데이터와 연결해서 설명해줘"
    python3 graph_rag.py --query "산업 경쟁 구도는?" --hops 3
    python3 graph_rag.py --entity competitor__채널톡 --hops 2   # 서브그래프만 출력
    python3 graph_rag.py --query "..." --context-only            # LLM 없이 컨텍스트만
"""

import os
import sys
import argparse
import textwrap
from pathlib import Path
from typing import Optional

import networkx as nx

# ─── 로컬 모듈 ───────────────────────────────
TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))
from graph_builder import (
    build_graph,
    find_nodes_by_keyword,
    get_subgraph,
    nfc,
)

# ─── LangChain ───────────────────────────────
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage


# ══════════════════════════════════════════════
# 서브그래프 → 텍스트 직렬화
# ══════════════════════════════════════════════

def subgraph_to_text(G: nx.DiGraph, sub: nx.DiGraph) -> str:
    """서브그래프를 LLM이 읽기 쉬운 Triples + Node Facts로 직렬화"""
    lines: list[str] = []

    # 1) 엣지 분류 (단일 패스)
    direct_edges: list[tuple] = []
    inferred_edges: list[tuple] = []
    for s, t, d in sub.edges(data=True):
        (inferred_edges if d.get("inferred") else direct_edges).append((s, t, d))

    lines.append("## Graph Triples (직접 관계)")
    for src, tgt, data in direct_edges:
        src_name = G.nodes[src].get("name", src)
        tgt_name = G.nodes[tgt].get("name", tgt)
        rel = data.get("relation", "related_to")
        lines.append(f"  ({src_name}) --[{rel}]--> ({tgt_name})")

    # 2) 합성 추론 트리플 (있을 때만)
    if inferred_edges:
        lines.append("\n## Composition Inferences (합성 추론으로 도출된 관계)")
        for src, tgt, data in inferred_edges:
            src_name = G.nodes[src].get("name", src)
            tgt_name = G.nodes[tgt].get("name", tgt)
            rel = data.get("relation", "?")
            via = data.get("via", "")
            comp = data.get("composition", "")
            lines.append(f"  ({src_name}) --[{rel}]--> ({tgt_name})  [추론: {comp}, 경로: {via}]")

    # 3) 노드 속성
    lines.append("\n## Node Facts (속성)")
    SKIP_ATTRS = {"source_file", "type"}
    for node_id, data in sub.nodes(data=True):
        name = data.get("name", node_id)
        entity_type = data.get("type", "?")
        facts = {k: v for k, v in data.items() if k not in SKIP_ATTRS and v is not None}
        line = f"  [{entity_type}] {name}"
        if facts:
            kv = ", ".join(f"{k}={v}" for k, v in facts.items() if k != "name")
            line += f"  ({kv})"
        lines.append(line)

    return "\n".join(lines)


# ══════════════════════════════════════════════
# 관련 시작 노드 자동 탐색
# ══════════════════════════════════════════════

def find_relevant_nodes(G: nx.DiGraph, query: str, top_k: int = 5) -> list[str]:
    """질의 텍스트에서 관련 노드를 탐색."""
    q = nfc(query)
    found: dict[str, int] = {}
    for node_id, data in G.nodes(data=True):
        name = nfc(str(data.get("name", "")))
        nid  = nfc(node_id)
        if (name and name in q) or nid in q:
            found[node_id] = found.get(node_id, 0) + 2
            continue
        for part in [name, nid.split("__")[-1]]:
            if len(part) >= 2 and part in q:
                found[node_id] = found.get(node_id, 0) + 1

    ranked = sorted(found.items(), key=lambda x: -x[1])
    return [node_id for node_id, _ in ranked[:top_k]]


# ══════════════════════════════════════════════
# LangChain Graph QA Chain
# ══════════════════════════════════════════════

SYSTEM_PROMPT = """\
당신은 지식 그래프 분석 전문가입니다.
아래 Knowledge Graph에서 추출한 정보를 바탕으로 질문에 답하세요.

규칙:
- 그래프에 있는 데이터만 근거로 사용하세요.
- 확인되지 않은 정보는 "그래프에 데이터 없음"으로 표시하세요.
- 멀티홉 경로를 명시적으로 설명하세요. 예: A → B → C 순으로...
- 한국어로 답변하세요.

## 범주론적 관계 유형 (Categorical Morphisms)

그래프에 다음 유형의 관계가 포함될 수 있습니다:
- **requires**: F_j 분석에 F_i 출력이 선행 입력으로 필요
- **informs**: F_i 결과가 F_j 해석에 맥락 제공
- **causes**: F_i 상태 변화가 F_j를 유발
- **constrains**: F_i가 F_j의 선택지/실행 조건을 제한
- **contrasts_with**: 대립적 관점 (양방향)

"Composition Inferences" 섹션의 관계는 직접 선언되지 않았으나
합성 법칙(g ∘ f)에 의해 자동 도출된 관계입니다.
추론 경로를 반드시 근거로 설명하세요.
"""


def run_graph_qa(
    query: str,
    G: nx.DiGraph,
    start_nodes: Optional[list[str]] = None,
    hops: int = 2,
    model: str = "claude-sonnet-4-6",
) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "[오류] ANTHROPIC_API_KEY 환경변수를 설정하세요.\n  export ANTHROPIC_API_KEY=sk-ant-..."

    if start_nodes is None:
        start_nodes = find_relevant_nodes(G, query)
    if not start_nodes:
        return "[오류] 질의와 관련된 그래프 노드를 찾지 못했습니다. --entity 옵션으로 직접 지정하세요."

    sub = get_subgraph(G, start_nodes, hops=hops)
    context = subgraph_to_text(G, sub)

    print(f"\n[서브그래프] {sub.number_of_nodes()}개 노드 / {sub.number_of_edges()}개 엣지 (시작: {start_nodes})")
    print("─" * 60)

    llm = ChatAnthropic(model=model, api_key=api_key, max_tokens=2048)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"## Knowledge Graph\n\n{context}\n\n---\n\n## 질문\n{query}"),
    ]
    response = llm.invoke(messages)
    return response.content


# ══════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════

def print_subgraph(G: nx.DiGraph, sub: nx.DiGraph) -> None:
    print(f"\n노드({sub.number_of_nodes()}개):")
    for node_id, data in sub.nodes(data=True):
        print(f"  [{data.get('type','?'):18s}] {data.get('name', node_id)}")
    print(f"\n엣지({sub.number_of_edges()}개):")
    for src, tgt, data in sub.edges(data=True):
        s = G.nodes[src].get("name", src)
        t = G.nodes[tgt].get("name", tgt)
        print(f"  {s}  --[{data.get('relation','')}]-->  {t}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="LangChain Graph RAG - Markdown knowledge graph 멀티홉 질의",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            예시:
              python3 graph_rag.py --query "X가 Y에 미치는 영향은?"
              python3 graph_rag.py --query "산업 경쟁 구도" --hops 3
              python3 graph_rag.py --entity competitor__채널톡 --hops 2
              python3 graph_rag.py --search 키워드
        """),
    )
    parser.add_argument("--query", "-q", help="자연어 질의")
    parser.add_argument("--entity", "-e", help="시작 노드 ID (--query 없이 서브그래프만 볼 때)")
    parser.add_argument("--hops", "-n", type=int, default=2, help="탐색 hop 수 (기본: 2)")
    parser.add_argument("--search", "-s", help="노드 이름 키워드 검색")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Claude 모델 ID")
    parser.add_argument("--context-only", action="store_true", help="LLM 호출 없이 서브그래프 컨텍스트만 출력")
    parser.add_argument("--config", "-c", type=Path, help="graph-config.yaml 경로 (생략 시 자동 탐색)")
    args = parser.parse_args()

    print("그래프 로딩 중...", end=" ", flush=True)
    G = build_graph(args.config)
    print(f"완료 ({G.number_of_nodes()}노드 / {G.number_of_edges()}엣지)")

    if args.search:
        results = find_nodes_by_keyword(G, args.search)
        print(f"\n검색 결과 ({args.search!r}): {len(results)}개")
        for r in results:
            d = G.nodes[r]
            print(f"  {r}  [{d.get('type','')}] {d.get('name','')}")
        sys.exit(0)

    if args.entity and not args.query:
        node_id = nfc(args.entity)
        if not G.has_node(node_id):
            print(f"[오류] 노드 없음: {node_id!r}")
            sys.exit(1)
        sub = get_subgraph(G, [node_id], hops=args.hops)
        print_subgraph(G, sub)
        if args.context_only:
            print("\n" + subgraph_to_text(G, sub))
        sys.exit(0)

    if not args.query:
        parser.print_help()
        sys.exit(1)

    start_nodes: Optional[list[str]] = None
    if args.entity:
        start_nodes = [nfc(args.entity)]

    if args.context_only:
        if start_nodes is None:
            start_nodes = find_relevant_nodes(G, args.query)
        sub = get_subgraph(G, start_nodes, hops=args.hops)
        print(f"\n[서브그래프] {sub.number_of_nodes()}노드 / {sub.number_of_edges()}엣지")
        print(subgraph_to_text(G, sub))
        sys.exit(0)

    answer = run_graph_qa(
        query=args.query,
        G=G,
        start_nodes=start_nodes,
        hops=args.hops,
        model=args.model,
    )
    print("\n" + "═" * 60)
    print(answer)
    print("═" * 60)
