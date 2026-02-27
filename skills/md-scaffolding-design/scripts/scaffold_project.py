"""
scaffold_project.py
로컬 Markdown 디렉토리 또는 GitHub repo 구조를 분석해 graph-config.yaml과
entity 디렉토리 템플릿을 자동 생성한다.

사용:
    # 로컬 프로젝트 분석
    python3 scaffold_project.py --local ./my-docs

    # GitHub 레포 분석
    python3 scaffold_project.py --repo owner/repo

    # 프리셋 템플릿 사용
    python3 scaffold_project.py --template personal-memory  --output ./graph-config.yaml
    python3 scaffold_project.py --template github-docs      --output ./graph-config.yaml
    python3 scaffold_project.py --template git-repo         --output ./graph-config.yaml
    python3 scaffold_project.py --template obsidian-vault   --output ./graph-config.yaml
    python3 scaffold_project.py --template any-markdown     --output ./graph-config.yaml

    # 분석 + 프리셋 병합 (분석 결과로 프리셋 커스터마이즈)
    python3 scaffold_project.py --local ./my-docs --template github-docs --output ./graph-config.yaml
    python3 scaffold_project.py --repo owner/repo --template git-repo --output ./graph-config.yaml
"""

import os
import re
import sys
import json
import base64
import argparse
import subprocess
from pathlib import Path
from collections import Counter

import yaml
import requests

# ──────────────────────────────────────────────
# 프리셋 템플릿
# ──────────────────────────────────────────────

PRESETS = {
    "personal-memory": {
        "_description": "개인 지식 베이스 / 제텔카스텐 / 일간노트",
        "entity_dirs": {
            "note":    "notes",
            "project": "projects",
            "person":  "people",
            "topic":   "topics",
            "daily":   "daily",
        },
        "relation_map": {
            "related":   "related_to",
            "see_also":  "related_to",
            "part_of":   "part_of",
            "mentions":  "mentions",
        },
        "scalar_node_attrs": ["title", "date", "tags", "status", "area"],
    },
    "github-docs": {
        "_description": "GitHub 프로젝트 docs/ 기반 문서 구조",
        "entity_dirs": {
            "guide":     "docs/guides",
            "reference": "docs/reference",
            "tutorial":  "docs/tutorials",
            "adr":       "docs/decisions",
            "concept":   "docs/concepts",
        },
        "relation_map": {
            "see_also":    "related_to",
            "supersedes":  "supersedes",
            "implements":  "implements",
            "depends_on":  "depends_on",
        },
        "scalar_node_attrs": ["title", "status", "date", "author", "tags"],
    },
    "git-repo": {
        "_description": "일반 Git 레포 (README, docs, wiki, src 포함)",
        "entity_dirs": {
            "doc":      "docs",
            "wiki":     "wiki",
            "guide":    "docs/guides",
            "decision": "docs/decisions",
            "readme":   ".",
        },
        "relation_map": {
            "see_also":   "related_to",
            "depends_on": "depends_on",
            "supersedes": "supersedes",
            "related":    "related_to",
        },
        "scalar_node_attrs": ["title", "status", "date", "author", "tags", "version"],
    },
    "obsidian-vault": {
        "_description": "Obsidian vault (entity 노드 + wikilink 기반)",
        "entity_dirs": {
            "note":   "notes",
            "entity": "entities",
            "area":   "areas",
            "source": "sources",
        },
        "relation_map": {
            "related":  "related_to",
            "parent":   "child_of",
        },
        "scalar_node_attrs": ["title", "tags", "status", "created", "area"],
    },
    "any-markdown": {
        "_description": "임의 Markdown 디렉토리 — 최소 설정 (분석 결과에 의존)",
        "entity_dirs": {
            "doc": ".",
        },
        "relation_map": {
            "related": "related_to",
            "see_also": "related_to",
        },
        "scalar_node_attrs": ["title", "tags", "date", "status"],
    },
    "wiki": {
        "_description": "GitHub Wiki / 단일 계층 위키",
        "entity_dirs": {
            "page": ".",
        },
        "relation_map": {},
        "scalar_node_attrs": ["title", "category", "tags"],
    },
}

# ──────────────────────────────────────────────
# 디렉토리 구조 분석
# ──────────────────────────────────────────────

IGNORE_DIRS = {".git", ".github", "node_modules", "__pycache__", ".obsidian",
               "dist", "build", ".next", ".nuxt", "vendor", "venv", ".venv"}

def scan_local(root: Path, max_depth: int = 3) -> dict[str, int]:
    """로컬 디렉토리에서 md 파일이 있는 폴더 목록과 파일 수 반환"""
    counts: dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in IGNORE_DIRS and not d.startswith(".")]
        depth = len(Path(dirpath).relative_to(root).parts)
        if depth > max_depth:
            dirnames.clear()
            continue
        md_count = sum(1 for f in filenames if f.endswith(".md"))
        if md_count > 0:
            rel = str(Path(dirpath).relative_to(root))
            counts[rel if rel != "." else "."] = md_count
    return counts


def get_github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        return token
    try:
        r = subprocess.run(["gh", "auth", "token"],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return ""


def scan_github(repo: str, branch: str = "main") -> dict[str, int]:
    """GitHub API로 md 파일이 있는 폴더 목록과 파일 수 반환"""
    token = get_github_token()
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    tree = resp.json().get("tree", [])

    counts: dict[str, int] = {}
    for item in tree:
        if item["type"] == "blob" and item["path"].endswith(".md"):
            parts = item["path"].split("/")
            parent = "/".join(parts[:-1]) if len(parts) > 1 else "."
            counts[parent] = counts.get(parent, 0) + 1
    return counts


# ──────────────────────────────────────────────
# 분석 결과 → graph-config 생성
# ──────────────────────────────────────────────

def dir_to_entity_type(dir_path: str) -> str:
    """디렉토리명을 entity 타입 슬러그로 변환"""
    name = dir_path.split("/")[-1] if "/" in dir_path else dir_path
    name = name.lower().replace("-", "_").replace(" ", "_")
    # 복수형 정규화 (단순)
    if name.endswith("ies"):
        name = name[:-3] + "y"
    elif name.endswith("ses") or name.endswith("xes"):
        name = name[:-2]
    elif name.endswith("s") and len(name) > 3:
        name = name[:-1]
    return name or "doc"


def infer_config(dir_counts: dict[str, int],
                 preset: dict | None = None) -> dict:
    """분석된 디렉토리 구조로 graph-config.yaml 내용 생성"""
    sorted_dirs = sorted(dir_counts.items(), key=lambda x: -x[1])

    entity_dirs = {}
    if preset:
        entity_dirs = dict(preset.get("entity_dirs", {}))

    preset_paths = set(entity_dirs.values())
    for dpath, count in sorted_dirs:
        if dpath in preset_paths:
            continue
        etype = dir_to_entity_type(dpath)
        base = etype
        idx = 2
        while etype in entity_dirs:
            etype = f"{base}_{idx}"
            idx += 1
        entity_dirs[etype] = dpath

    base = preset or {}
    return {
        "entity_dirs":       entity_dirs,
        "relation_map":      base.get("relation_map", {}),
        "scalar_node_attrs": base.get("scalar_node_attrs",
                                       ["title", "name", "tags", "status", "date"]),
    }


# ──────────────────────────────────────────────
# 출력
# ──────────────────────────────────────────────

CONFIG_HEADER = """\
# graph-config.yaml
# md-graph-multihop 설정 파일
# 이 파일 위치를 base_dir로 사용한다.
#
# 사용:
#   python3 graph_builder.py --config graph-config.yaml
#   python3 graph_rag.py --config graph-config.yaml --query "..."
#   python3 github_adapter.py --repo owner/repo --config graph-config.yaml
#
# OWL 온톨로지 방식(권장)은 graph-ontology.example.yaml 참조
"""


def write_config(config: dict, output: Path, header_comment: str = "") -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        if header_comment:
            f.write(header_comment + "\n")
        yaml.dump(config, f, allow_unicode=True,
                  default_flow_style=False, sort_keys=False)
    print(f"graph-config.yaml 생성: {output}")


def print_summary(dir_counts: dict[str, int], config: dict) -> None:
    print("\n[ 감지된 md 디렉토리 ]")
    for d, cnt in sorted(dir_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {d:40s}  {cnt:3d}개")
    print("\n[ 생성된 entity_dirs ]")
    for etype, path in config["entity_dirs"].items():
        print(f"  {etype:20s}  →  {path}")
    if config["relation_map"]:
        print("\n[ relation_map ]")
        for k, v in config["relation_map"].items():
            print(f"  {k:20s}  →  {v}")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Markdown 프로젝트 구조 분석 → graph-config.yaml 자동 생성"
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--local", "-l", type=Path,
                     help="로컬 디렉토리 경로")
    src.add_argument("--repo",  "-r",
                     help="GitHub repo (owner/repo)")

    parser.add_argument("--branch",   "-b", default="main")
    parser.add_argument("--template", "-t",
                        choices=list(PRESETS.keys()),
                        help=f"프리셋 템플릿: {', '.join(PRESETS)}")
    parser.add_argument("--output",   "-o", type=Path,
                        default=Path("graph-config.yaml"),
                        help="출력 파일 경로 (기본: ./graph-config.yaml)")
    parser.add_argument("--dry-run",  action="store_true",
                        help="파일 생성 없이 결과만 출력")
    parser.add_argument("--list-templates", action="store_true",
                        help="사용 가능한 프리셋 목록 출력")
    args = parser.parse_args()

    if args.list_templates:
        print("[ 사용 가능한 프리셋 ]")
        for name, preset in PRESETS.items():
            print(f"  {name:20s}  {preset.get('_description','')}")
        sys.exit(0)

    preset = {k: v for k, v in PRESETS.get(args.template, {}).items()
              if not k.startswith("_")} if args.template else None

    dir_counts: dict[str, int] = {}

    if args.local:
        print(f"로컬 스캔: {args.local}")
        dir_counts = scan_local(args.local)
    elif args.repo:
        print(f"GitHub 스캔: {args.repo} / {args.branch}")
        try:
            dir_counts = scan_github(args.repo, args.branch)
        except Exception as e:
            print(f"[오류] GitHub API 실패: {e}")
            if not preset:
                sys.exit(1)
            print("프리셋만으로 config 생성합니다.")

    if not dir_counts and not preset:
        print("[오류] --local, --repo, --template 중 하나 이상 필요합니다.")
        parser.print_help()
        sys.exit(1)

    config = infer_config(dir_counts, preset)
    print_summary(dir_counts, config)

    if not args.dry_run:
        write_config(config, args.output, CONFIG_HEADER)
        print(f"\n다음 단계:")
        print(f"  1. {args.output} 에서 entity_dirs / relation_map 검토 및 수정")
        print(f"  2. python3 graph_builder.py --config {args.output}")
        print(f"  3. python3 graph_rag.py --config {args.output} --query '...'")
        print(f"\n  OWL 온톨로지 방식으로 전환하려면:")
        print(f"  cp graph-ontology.example.yaml graph-ontology.yaml  # 예시 참조")
