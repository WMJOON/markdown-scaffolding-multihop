#!/usr/bin/env python3
"""
msm-ontology shapes-validate — SHACL 기반 ontology Tbox 검증

Tbox 위치: {target}/ontology/system/semantic/{domain}/{name}.classes.ttl
Shapes:    {target}/ontology/system/semantic/{domain}/{name}.shapes.ttl

Usage:
  msm-ontology shapes-validate --target REPO --domain technical/semantic-web
  msm-ontology shapes-validate --target REPO --all
  msm-ontology shapes-validate --target REPO --classes PATH --shapes PATH

Options:
  --inference {none,rdfs,owlrl,both}   기본 none — Tbox 구조 검증은 asserted graph.
                                       rdfs/owlrl은 subClassOf 전이 닫힘이
                                       cardinality shape과 충돌하므로 Abox
                                       의미 검증 시에만 사용.

Exit code: 0=conforms, 1=violation, 2=usage error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SEMANTIC_SUBPATH = ("ontology", "system", "semantic")


def find_domain_pair(target: Path, domain: str) -> tuple[Path, Path]:
    """domain (예: 'technical/semantic-web') 에서 classes/shapes ttl 경로 추출."""
    semantic_root = target.joinpath(*SEMANTIC_SUBPATH)
    domain_dir = semantic_root / domain
    name = domain.split("/")[-1]
    classes = domain_dir / f"{name}.classes.ttl"
    shapes = domain_dir / f"{name}.shapes.ttl"
    return classes, shapes


def discover_all_domains(target: Path) -> list[str]:
    semantic_root = target.joinpath(*SEMANTIC_SUBPATH)
    if not semantic_root.exists():
        return []
    domains = []
    for classes in semantic_root.rglob("*.classes.ttl"):
        rel = classes.parent.relative_to(semantic_root)
        domains.append(str(rel))
    return sorted(domains)


def validate(
    classes_path: Path,
    shapes_path: Path,
    inference: str = "none",
) -> tuple[bool, str]:
    """pyshacl 호출. (conforms, report_text) 반환."""
    try:
        from pyshacl import validate as pyshacl_validate
    except ImportError:
        print(
            "ERROR: pyshacl 미설치.\n"
            "스킬 venv 재구성: python3 -m venv ~/.claude/skills/msm-ontology/.venv\n"
            "                  ~/.claude/skills/msm-ontology/.venv/bin/pip install -r \\\n"
            "                  ~/.claude/skills/msm-ontology/requirements.txt",
            file=sys.stderr,
        )
        sys.exit(2)

    from rdflib import Graph

    data_graph = Graph().parse(str(classes_path), format="turtle")
    shapes_graph = Graph().parse(str(shapes_path), format="turtle")

    conforms, _results_graph, results_text = pyshacl_validate(
        data_graph=data_graph,
        shacl_graph=shapes_graph,
        inference=inference,
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
        debug=False,
    )
    return conforms, results_text


def run_one(target: Path, domain: str, inference: str = "none") -> int:
    classes, shapes = find_domain_pair(target, domain)
    if not classes.exists():
        print(f"ERROR: {classes} 없음", file=sys.stderr)
        return 2
    if not shapes.exists():
        print(f"ERROR: {shapes} 없음", file=sys.stderr)
        return 2

    print(f"=== Validating {domain} (inference={inference}) ===")
    try:
        print(f"  classes: {classes.relative_to(target)}")
        print(f"  shapes:  {shapes.relative_to(target)}")
    except ValueError:
        print(f"  classes: {classes}")
        print(f"  shapes:  {shapes}")
    conforms, report = validate(classes, shapes, inference)
    print()
    if conforms:
        print(f"PASS  {domain} — 모든 shape 만족")
        return 0
    print(f"FAIL  {domain} — 위반 발견")
    print()
    print(report)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SHACL 기반 ontology Tbox 검증",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--target", type=Path, default=Path.cwd(),
                        help="KB 루트 (기본: cwd)")
    parser.add_argument("--domain", help="검증할 도메인 (예: 'technical/semantic-web'). --all 또는 --classes 사용 시 생략.")
    parser.add_argument("--all", action="store_true",
                        help="target 아래 모든 도메인 검증")
    parser.add_argument("--classes", type=Path,
                        help="명시적 classes.ttl 경로 (--shapes 동시 지정 필요)")
    parser.add_argument("--shapes", type=Path,
                        help="명시적 shapes.ttl 경로")
    parser.add_argument("--inference", choices=["none", "rdfs", "owlrl", "both"],
                        default="none",
                        help="추론 모드 (기본 none — Tbox 구조 검증용)")
    args = parser.parse_args()

    target = args.target.resolve()

    # 명시 경로 모드
    if args.classes or args.shapes:
        if not (args.classes and args.shapes):
            print("ERROR: --classes와 --shapes는 함께 지정", file=sys.stderr)
            return 2
        print(f"=== Validating explicit paths (inference={args.inference}) ===")
        print(f"  classes: {args.classes}")
        print(f"  shapes:  {args.shapes}")
        conforms, report = validate(args.classes, args.shapes, args.inference)
        print()
        if conforms:
            print("PASS")
            return 0
        print("FAIL")
        print(report)
        return 1

    if args.all:
        domains = discover_all_domains(target)
        if not domains:
            print(f"탐지된 도메인 없음 (under {target}/ontology/system/semantic/)")
            return 0
        print(f"발견된 도메인 {len(domains)}개: {', '.join(domains)}")
        print()
        fails = 0
        for d in domains:
            rc = run_one(target, d, args.inference)
            if rc != 0:
                fails += 1
            print()
        print(f"=== 요약: {len(domains) - fails}/{len(domains)} PASS ===")
        return 0 if fails == 0 else 1

    if not args.domain:
        parser.print_usage()
        return 2

    return run_one(target, args.domain, args.inference)


if __name__ == "__main__":
    sys.exit(main())
