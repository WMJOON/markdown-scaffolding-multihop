"""
github_adapter.py
GitHub 레포지토리 md 파일을 GitHub API로 가져와 NetworkX 그래프를 구성하고
멀티홉 컨텍스트를 출력한다. 로컬 클론 불필요.

사용:
    # GITHUB_TOKEN 환경변수 또는 gh CLI 인증 중 하나 필요
    python3 github_adapter.py --repo owner/repo --query "X와 Y의 관계는?"
    python3 github_adapter.py --repo owner/repo --paths docs/ wiki/ --hops 3
    python3 github_adapter.py --repo owner/repo --search keyword
    python3 github_adapter.py --repo owner/repo --stats
"""

import os
import re
import sys
import json
import base64
import argparse
import unicodedata
import subprocess
from pathlib import Path, PurePosixPath
from typing import Optional

import yaml
import requests
import networkx as nx

# ──────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────

def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


# ──────────────────────────────────────────────
# GitHub API 클라이언트
# ──────────────────────────────────────────────

def get_token() -> str:
    """GITHUB_TOKEN 환경변수 → gh CLI 토큰 순으로 획득"""
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def api_get(url: str, token: str) -> dict | list:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def list_md_files(repo: str, branch: str, paths: list[str], token: str) -> list[dict]:
    """지정 경로(들)의 .md 파일 목록 반환 [{path, sha, download_url}]"""
    files = []
    for path in paths:
        path = path.rstrip("/")
        url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
        tree = api_get(url, token)
        for item in tree.get("tree", []):
            if item["type"] == "blob" and item["path"].endswith(".md"):
                # path 필터: 지정 경로 하위이거나, "." (전체)
                if path == "." or item["path"].startswith(path + "/") or item["path"] == path:
                    files.append(item)
    return files


def fetch_file(repo: str, file_path: str, token: str) -> str:
    """단일 파일 내용 반환"""
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    data = api_get(url, token)
    content = data.get("content", "")
    encoding = data.get("encoding", "base64")
    if encoding == "base64":
        return base64.b64decode(content).decode("utf-8", errors="replace")
    return content


# ──────────────────────────────────────────────
# 파서
# ──────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """(frontmatter_dict, body) 반환"""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end >= 0:
            try:
                fm = yaml.safe_load(text[3:end]) or {}
            except Exception:
                fm = {}
            return fm, text[end + 3:]
    return {}, text


def extract_wikilinks(text: str) -> list[str]:
    """[[target]] 형태 추출"""
    return re.findall(r"\[\[([^\]|#]+?)(?:\|[^\]]+)?\]\]", text)


def extract_md_links(text: str) -> list[str]:
    """[label](path.md) 형태에서 .md 대상 추출"""
    raw = re.findall(r"\[.*?\]\(([^)]+)\)", text)
    result = []
    for r in raw:
        r = r.split("#")[0].strip()   # 앵커 제거
        if r.endswith(".md") and not r.startswith("http"):
            result.append(r)
    return result


def path_to_node_id(file_path: str) -> str:
    """파일 경로 → 노드 ID (확장자 제거, 슬래시 → __)"""
    p = PurePosixPath(file_path)
    return nfc(str(p.with_suffix("")).replace("/", "__"))


def resolve_link(src_path: str, link: str) -> str:
    """상대 경로 링크를 src 기준으로 절대화 후 노드 ID 반환"""
    if link.startswith("/"):
        resolved = link.lstrip("/")
    else:
        base = str(PurePosixPath(src_path).parent)
        resolved = str(PurePosixPath(base) / link) if base != "." else link
    # 정규화 (../ 처리)
    parts = []
    for part in resolved.replace("\\", "/").split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part and part != ".":
            parts.append(part)
    return nfc("/".join(parts).removesuffix(".md"))


# ──────────────────────────────────────────────
# Config 로더 (선택적)
# ──────────────────────────────────────────────

DEFAULT_CONFIG = "graph-config.yaml"

def load_local_config(config_path: Optional[Path]) -> dict:
    """로컬 graph-config.yaml 로드 (없으면 빈 dict)"""
    if config_path and config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    for candidate in [Path.cwd() / DEFAULT_CONFIG, Path(__file__).parent.parent / DEFAULT_CONFIG]:
        if candidate.exists():
            with open(candidate, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


# ──────────────────────────────────────────────
# 그래프 빌더
# ──────────────────────────────────────────────

def build_github_graph(
    repo: str,
    branch: str = "main",
    paths: list[str] | None = None,
    token: str = "",
    config: dict | None = None,
) -> nx.DiGraph:
    if paths is None:
        paths = ["."]
    if config is None:
        config = {}

    relation_map   = config.get("relation_map", {})
    scalar_attrs   = set(config.get("scalar_node_attrs", ["name", "title", "status", "tags"]))
    entity_dirs    = config.get("entity_dirs", {})   # path prefix → entity type

    # path prefix 기반 entity type 분류 함수
    def infer_type(file_path: str) -> str:
        for etype, rel_path in entity_dirs.items():
            rel_path = rel_path.rstrip("/")
            if file_path.startswith(rel_path + "/") or file_path == rel_path:
                return etype
        # fallback: 상위 디렉토리명
        parts = file_path.split("/")
        return parts[-2] if len(parts) >= 2 else "doc"

    print(f"  GitHub API에서 .md 파일 목록 가져오는 중...", flush=True)
    try:
        files = list_md_files(repo, branch, paths, token)
    except requests.HTTPError as e:
        print(f"[오류] GitHub API 실패: {e}")
        sys.exit(1)

    print(f"  {len(files)}개 파일 발견. 내용 가져오는 중...", flush=True)

    # node_id → file_path 역매핑 (wikilink 해소용)
    node_id_map: dict[str, str] = {}
    # 파일 내용 캐시
    file_cache: dict[str, tuple[dict, str]] = {}  # file_path → (fm, body)

    G = nx.DiGraph()

    # ── 1단계: 노드 추가 ──
    for item in files:
        fp = item["path"]
        try:
            text = fetch_file(repo, fp, token)
        except Exception as e:
            print(f"  [경고] {fp} 스킵: {e}")
            continue

        fm, body = parse_frontmatter(text)
        file_cache[fp] = (fm, body)

        node_id = path_to_node_id(fp)
        node_id_map[node_id] = fp
        # stem만으로도 검색 가능하게 추가 등록
        stem = nfc(PurePosixPath(fp).stem)
        if stem not in node_id_map:
            node_id_map[stem] = fp

        attrs = {
            "type":        infer_type(fp),
            "source_file": fp,
            "repo":        repo,
        }
        title = fm.get("title") or fm.get("name") or PurePosixPath(fp).stem
        attrs["name"] = title
        for field in scalar_attrs:
            if field in fm and fm[field] is not None:
                attrs[field] = fm[field]
        G.add_node(node_id, **attrs)

    # ── 2단계: frontmatter 엣지 (RELATION_MAP) ──
    for fp, (fm, _) in file_cache.items():
        src = path_to_node_id(fp)
        for field, relation in relation_map.items():
            if field not in fm:
                continue
            val = fm[field]
            targets = []
            if isinstance(val, str):
                targets = extract_wikilinks(val) or [val]
            elif isinstance(val, list):
                for v in val:
                    targets += extract_wikilinks(str(v)) if "[[" in str(v) else [str(v)]
            for tgt_raw in targets:
                tgt = nfc(tgt_raw)
                if G.has_node(tgt):
                    G.add_edge(src, tgt, relation=relation, field=field)

    # ── 3단계: 본문 엣지 (wikilink + markdown link) ──
    for fp, (_, body) in file_cache.items():
        src = path_to_node_id(fp)
        if not G.has_node(src):
            continue
        # wikilink
        for tgt_raw in extract_wikilinks(body):
            tgt = nfc(tgt_raw)
            resolved = node_id_map.get(tgt, tgt).removesuffix(".md").replace("/", "__")
            resolved = nfc(resolved)
            if G.has_node(resolved) and not G.has_edge(src, resolved):
                G.add_edge(src, resolved, relation="links_to", field="body_wikilink")
        # markdown link ([label](path.md))
        for link in extract_md_links(body):
            resolved = resolve_link(fp, link).replace("/", "__")
            resolved = nfc(resolved)
            if G.has_node(resolved) and not G.has_edge(src, resolved):
                G.add_edge(src, resolved, relation="links_to", field="body_mdlink")

    return G


# ──────────────────────────────────────────────
# 그래프 RAG 유틸 (graph_builder.py 미러)
# ──────────────────────────────────────────────

def get_subgraph(G: nx.DiGraph, start_nodes: list[str], hops: int = 2) -> nx.DiGraph:
    visited: set[str] = set()
    frontier = set(n for n in start_nodes if G.has_node(n))
    for _ in range(hops):
        nxt: set[str] = set()
        for node in frontier:
            visited.add(node)
            nxt.update(G.successors(node))
            nxt.update(G.predecessors(node))
        frontier = nxt - visited
        visited.update(frontier)
    return G.subgraph(visited)


def find_nodes_by_keyword(G: nx.DiGraph, keyword: str) -> list[str]:
    kw = nfc(keyword.lower())
    return [
        nid for nid, data in G.nodes(data=True)
        if kw in nfc(str(data.get("name", "")).lower()) or kw in nid.lower()
    ]


def find_relevant_nodes(G: nx.DiGraph, query: str, top_k: int = 5) -> list[str]:
    """
    양방향 토큰 매칭:
    A) 노드 name/slug가 질의에 포함되는지 (name ⊆ query)
    B) 질의 토큰이 노드 name/id에 포함되는지 (token ⊆ name)
    두 방식을 모두 적용해 GitHub 파일명 슬러그에도 대응한다.
    """
    q = nfc(query.lower())
    # 질의에서 2글자 이상 토큰 추출
    tokens = [t for t in re.split(r"[\s_\-/]+", q) if len(t) >= 2]
    found: dict[str, int] = {}
    for nid, data in G.nodes(data=True):
        name     = nfc(str(data.get("name", "")).lower())
        # 전체 경로를 공백으로 펼쳐서 검색 대상에 포함 (patterns__agents__README → "patterns agents readme")
        nid_flat = nfc(nid.lower().replace("__", " ").replace("-", " ").replace("_", " "))
        score = 0
        # A) 노드 name이 질의 안에 포함
        if name and name in q:
            score += 3
        # B) 질의 토큰이 name 또는 펼쳐진 경로에 포함
        for tok in tokens:
            if tok in name:
                score += 2
            elif tok in nid_flat:
                score += 1
        if score > 0:
            found[nid] = score
    return [nid for nid, _ in sorted(found.items(), key=lambda x: -x[1])[:top_k]]


def subgraph_to_text(G: nx.DiGraph, sub: nx.DiGraph) -> str:
    lines = ["## Graph Triples (관계)"]
    for src, tgt, data in sub.edges(data=True):
        sn = G.nodes[src].get("name", src)
        tn = G.nodes[tgt].get("name", tgt)
        lines.append(f"  ({sn}) --[{data.get('relation','?')}]--> ({tn})")
    lines.append("\n## Node Facts (속성)")
    SKIP = {"source_file", "repo"}
    for nid, data in sub.nodes(data=True):
        name = data.get("name", nid)
        etype = data.get("type", "?")
        kv = ", ".join(f"{k}={v}" for k, v in data.items()
                       if k not in SKIP | {"name", "type"} and v is not None)
        lines.append(f"  [{etype}] {name}" + (f"  ({kv})" if kv else ""))
    return "\n".join(lines)


def summarize(G: nx.DiGraph) -> str:
    tc: dict[str, int] = {}
    for _, d in G.nodes(data=True):
        t = d.get("type", "?")
        tc[t] = tc.get(t, 0) + 1
    rc: dict[str, int] = {}
    for _, _, d in G.edges(data=True):
        r = d.get("relation", "?")
        rc[r] = rc.get(r, 0) + 1
    lines = [f"노드: {G.number_of_nodes()}개  엣지: {G.number_of_edges()}개", "", "[ 노드 타입 ]"]
    for t, c in sorted(tc.items()):
        lines.append(f"  {t:25s} {c:3d}개")
    lines += ["", "[ 엣지 relation ]"]
    for r, c in sorted(rc.items()):
        lines.append(f"  {r:30s} {c:3d}개")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GitHub repo md 파일 → Graph RAG (로컬 클론 불필요)"
    )
    parser.add_argument("--repo",   "-r", required=True, help="owner/repo")
    parser.add_argument("--branch", "-b", default="main",  help="브랜치 (기본: main)")
    parser.add_argument("--paths",  "-p", nargs="+", default=["."],
                        help="탐색할 경로 목록 (기본: 전체). 예: docs/ wiki/")
    parser.add_argument("--query",  "-q", help="자연어 질의 (컨텍스트 출력)")
    parser.add_argument("--entity", "-e", help="시작 노드 ID")
    parser.add_argument("--hops",   "-n", type=int, default=2)
    parser.add_argument("--search", "-s", help="노드 키워드 검색")
    parser.add_argument("--stats",        action="store_true", help="그래프 통계만 출력")
    parser.add_argument("--config", "-c", type=Path, help="graph-config.yaml 경로")
    parser.add_argument("--token",        help="GitHub 토큰 (생략 시 GITHUB_TOKEN 또는 gh CLI)")
    args = parser.parse_args()

    token  = args.token or get_token()
    config = load_local_config(args.config)

    print(f"그래프 로딩 중... ({args.repo} / {args.branch})", flush=True)
    G = build_github_graph(
        repo=args.repo,
        branch=args.branch,
        paths=args.paths,
        token=token,
        config=config,
    )
    print(f"완료 ({G.number_of_nodes()}노드 / {G.number_of_edges()}엣지)\n")

    if args.stats or (not args.search and not args.query and not args.entity):
        print(summarize(G))
        sys.exit(0)

    if args.search:
        matches = find_nodes_by_keyword(G, args.search)
        print(f"검색 결과 ({args.search!r}): {len(matches)}개")
        for m in matches:
            d = G.nodes[m]
            print(f"  {m}  [{d.get('type','')}] {d.get('name','')}  ({d.get('source_file','')})")
        sys.exit(0)

    # 서브그래프 컨텍스트 출력
    start_nodes: list[str] = []
    if args.entity:
        start_nodes = [nfc(args.entity)]
    elif args.query:
        start_nodes = find_relevant_nodes(G, args.query)

    if not start_nodes:
        print("[오류] 관련 노드를 찾지 못했습니다. --entity 또는 --search 로 노드 ID를 먼저 확인하세요.")
        sys.exit(1)

    sub = get_subgraph(G, start_nodes, hops=args.hops)
    print(f"[서브그래프] {sub.number_of_nodes()}노드 / {sub.number_of_edges()}엣지  (시작: {start_nodes})")
    print("─" * 60)
    print(subgraph_to_text(G, sub))
