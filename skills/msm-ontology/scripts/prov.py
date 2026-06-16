#!/usr/bin/env python3
"""
msm-ontology prov — PROV-O 출처 레이어 생성 (v0.13.1)

각 owl:Class 의 dct:identifier 를 explain entities.jsonl 의 entity id 와 조인하여
그 entity 의 source_refs(1차 출처)를 prov:hadPrimarySource 트리플로 투영한다.
동시에 출처 강제 SHACL 게이트(*.prov.shapes.ttl)를 도메인 네임스페이스에 맞춰 생성.

산출물(둘 다 generated artifact — 직접 편집 금지, 본 명령으로 재생성):
  {domain}/{name}.prov.ttl          1차 출처 prov:Entity + class→source 파생 링크
  {domain}/{name}.prov.shapes.ttl   as-namespace owl:Class 출처 minCount 1 강제

생성된 파일은 `shapes-validate` 가 자동 병합한다(v0.13.1) → 근거 미상 노드 차단.

조인 키(dct:identifier)가 없는 도메인(예: LinkML YAML 컴파일 도메인)은
경고 후 skip한다 — 그 도메인의 출처 주입은 별도 경로(compile 단계) 필요.

Usage:
  msm-ontology prov --target REPO --domain technical/agent-semantics --apply
  msm-ontology prov --target REPO --all --apply
  msm-ontology prov --target REPO --all              # dry-run (기본)

Exit code: 0=정상(생성/스킵), 2=usage error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEMANTIC_SUBPATH = ("ontology", "system", "semantic")
EXPLAIN_SUBPATH = ("ontology", "explain")
SRC_BASE = "https://wmjoon.kb/source/"


def slug_iri(path: str) -> str:
    return SRC_BASE + re.sub(r"[^A-Za-z0-9._/\-]", "_", path)


def build_source_index(target: Path) -> dict[str, list[str]]:
    """모든 entities.jsonl 을 스캔해 entity id → source_refs 전역 인덱스 구축.

    explain(개념) + system/semantic(백킹) 양쪽을 본다. id 는 전역 유일하므로
    도메인↔explain 경로 매핑 없이 dct:identifier 로 바로 조인 가능.
    """
    index: dict[str, list[str]] = {}
    roots = [target.joinpath(*EXPLAIN_SUBPATH), target.joinpath(*SEMANTIC_SUBPATH)]
    for root in roots:
        if not root.exists():
            continue
        for jf in root.rglob("entities.jsonl"):
            for line in jf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                eid = o.get("id")
                if not eid:
                    continue
                srcs = o.get("source_refs") or o.get("source_file") or o.get("source") or []
                if isinstance(srcs, str):
                    srcs = [srcs]
                if srcs:
                    index.setdefault(eid, [])
                    for s in srcs:
                        if s not in index[eid]:
                            index[eid].append(s)
    return index


def discover_classes_files(target: Path, domain: str | None) -> list[Path]:
    """대상 classes.ttl 경로 목록 (파일 중심).

    도메인당 classes.ttl 이 복수일 수 있고(예: conversation-design,
    healthcare/stroke), 파일 basename 이 디렉토리명과 다를 수 있으므로
    (예: enterprise/enterprise-workflow.classes.ttl) 파일을 직접 발견한다.
    """
    semantic_root = target.joinpath(*SEMANTIC_SUBPATH)
    if not semantic_root.exists():
        return []
    if domain:
        scope = semantic_root / domain
        return sorted(scope.glob("*.classes.ttl")) if scope.exists() else []
    return sorted(semantic_root.rglob("*.classes.ttl"))


def parse_classes(classes_path: Path):
    """(namespace, [(localname, identifier|None), ...]) 반환."""
    import rdflib
    from rdflib.namespace import OWL, DCTERMS, RDF

    g = rdflib.Graph()
    g.parse(str(classes_path), format="turtle")
    rows = []
    ns = None
    for s in g.subjects(RDF.type, OWL.Class):
        s_str = str(s)
        if "#" not in s_str:
            continue
        base = s_str.split("#")[0] + "#"
        if ns is None:
            ns = base
        ident = g.value(s, DCTERMS.identifier)
        rows.append((s_str.split("#")[-1], str(ident) if ident else None))
    return ns, sorted(rows)


def gen_for_file(target: Path, classes_path: Path, src_index: dict, apply: bool) -> str:
    """한 classes.ttl 의 prov.ttl + prov.shapes.ttl 생성. 상태 문자열 반환."""
    semantic_root = target.joinpath(*SEMANTIC_SUBPATH)
    name = classes_path.name[: -len(".classes.ttl")]
    try:
        label = f"{classes_path.parent.relative_to(semantic_root)}/{name}"
    except ValueError:
        label = name
    domain = label  # 메시지/재생성 힌트용

    ns, rows = parse_classes(classes_path)
    if not rows:
        return f"SKIP  {label} — owl:Class 없음"

    with_ident = [(c, i) for c, i in rows if i]
    if not with_ident:
        return (f"SKIP  {label} — dct:identifier 0건 (조인 키 없음, "
                f"{len(rows)} class). compile 단계 출처 주입 필요.")

    sources: set[str] = set()
    links: list[str] = []
    ungrounded: list[str] = []
    for cls, ident in with_ident:
        srcs = src_index.get(ident, [])
        if not srcs:
            ungrounded.append(cls)
            continue
        for src in srcs:
            sources.add(src)
            links.append(f"as:{cls} prov:hadPrimarySource <{slug_iri(src)}> .")

    domain_dir = classes_path.parent
    try:
        domain_rel = str(domain_dir.relative_to(semantic_root))
    except ValueError:
        domain_rel = domain
    prov_path = domain_dir / f"{name}.prov.ttl"
    shapes_path = domain_dir / f"{name}.prov.shapes.ttl"

    # ── prov.ttl ──────────────────────────────────────────────
    head = [
        f"# {name}.prov.ttl  — GENERATED ARTIFACT (do not edit)",
        f"# 재생성: msm-ontology prov --domain {domain_rel} --apply",
        "# classes.ttl(dct:identifier) ⋈ explain entities.jsonl(source_refs)",
        "#",
        f"@prefix as:   <{ns}> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        "@prefix dct:  <http://purl.org/dc/terms/> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "",
        "# ── 1차 출처 노드 (prov:Entity) ─────────────────────────────",
    ]
    for src in sorted(sources):
        head.append(f"<{slug_iri(src)}> a prov:Entity ;")
        head.append(f'    dct:source "{src}" ;')
        head.append(f'    rdfs:label "{src}" .')
    head.append("")
    head.append("# ── owl:Class → 1차 출처 파생 링크 ──────────────────────────")
    prov_ttl = "\n".join(head + sorted(links)) + "\n"

    # ── prov.shapes.ttl (namespace-scoped 게이트) ──────────────
    shapes_ttl = f'''# {name}.prov.shapes.ttl  — GENERATED ARTIFACT (do not edit)
# 재생성: msm-ontology prov --domain {domain_rel} --apply
# {ns} 네임스페이스 owl:Class 는 prov:hadPrimarySource 최소 1개 필수.

@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

[]  a sh:NodeShape ;
    sh:name "ClassProvenanceShape" ;
    sh:target [
        a sh:SPARQLTarget ;
        sh:prefixes [
            sh:declare [ sh:prefix "owl" ; sh:namespace "http://www.w3.org/2002/07/owl#"^^xsd:anyURI ] ;
        ] ;
        sh:select """
            SELECT ?this WHERE {{
                ?this a owl:Class .
                FILTER(STRSTARTS(STR(?this), "{ns}"))
            }}
        """ ;
    ] ;
    sh:property [
        sh:path prov:hadPrimarySource ;
        sh:minCount 1 ;
        sh:nodeKind sh:IRI ;
        sh:message "근거 미상 개념 노드: 모든 owl:Class 는 prov:hadPrimarySource(1차 출처) 최소 1개를 명시해야 함."@ko ;
    ] .
'''

    if apply:
        prov_path.write_text(prov_ttl, encoding="utf-8")
        shapes_path.write_text(shapes_ttl, encoding="utf-8")
        verb = "WROTE"
    else:
        verb = "DRY  "

    msg = (f"{verb} {domain} — {len(with_ident)} class / "
           f"{len(links)} link / {len(sources)} source")
    if ungrounded:
        msg += f"\n      ⚠ 출처 미상 {len(ungrounded)}: {', '.join(ungrounded)}"
    return msg


def main() -> int:
    p = argparse.ArgumentParser(
        description="PROV-O 출처 레이어 생성 (v0.13.1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--target", type=Path, default=Path.cwd(), help="KB 루트 (기본: cwd)")
    p.add_argument("--domain", help="도메인 (예: 'technical/agent-semantics')")
    p.add_argument("--all", action="store_true", help="모든 도메인")
    p.add_argument("--apply", action="store_true", help="파일 기록 (기본: dry-run)")
    args = p.parse_args()

    target = args.target.resolve()
    if not (args.domain or args.all):
        p.print_usage()
        return 2

    try:
        import rdflib  # noqa: F401
    except ImportError:
        print("ERROR: rdflib 미설치 — 스킬 venv 확인", file=sys.stderr)
        return 2

    src_index = build_source_index(target)
    print(f"source index: {len(src_index)} entity (id → source_refs)")
    print(f"mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print()

    files = discover_classes_files(target, None if args.all else args.domain)
    if not files:
        scope = "전역" if args.all else args.domain
        print(f"대상 *.classes.ttl 없음 ({scope})")
        return 0
    for f in files:
        print(gen_for_file(target, f, src_index, args.apply))
    return 0


if __name__ == "__main__":
    sys.exit(main())
