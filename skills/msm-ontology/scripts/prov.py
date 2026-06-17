#!/usr/bin/env python3
"""
msm-ontology prov — PROV-O 출처 레이어 생성 (v0.13.1)

각 owl:Class 를 explain entities.jsonl 과 조인하여 그 entity 의 source_refs(1차 출처)를
prov:hadPrimarySource 트리플로 투영한다. 조인 키는 2단계:
  1차: classes.ttl 의 dct:identifier  ⋈  entity id
  폴백: classes.ttl 의 owl:Class subject IRI  ⋈  entity owl_class(풀 IRI)
폴백은 owlgen 이 dct:identifier 를 드롭한 컴파일 도메인(enterprise·legal 등)을 위한 것.
동시에 출처 강제 SHACL 게이트(*.prov.shapes.ttl)를 도메인 네임스페이스에 맞춰 생성.

산출물(둘 다 generated artifact — 직접 편집 금지, 본 명령으로 재생성):
  {domain}/{name}.prov.ttl          1차 출처 prov:Entity + class→source 파생 링크
  {domain}/{name}.prov.shapes.ttl   as-namespace owl:Class 출처 minCount 1 강제

생성된 파일은 `shapes-validate` 가 자동 병합한다(v0.13.1) → 근거 미상 노드 차단.

두 키 모두 매칭되는 출처가 0건인 도메인(출처 entities.jsonl 부재)은 경고 후 skip 한다
— 그 도메인은 evidence/entities.jsonl 백필이 선행되어야 한다.

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
META_NS = "https://wmjoon.kb/meta#"          # 메타 어휘 (StructuralClass 마커)
EXEMPT_SUFFIX = ".prov.exempt.txt"           # 도메인별 구조클래스 면제 큐레이트 리스트


def slug_iri(path: str) -> str:
    return SRC_BASE + re.sub(r"[^A-Za-z0-9._/\-]", "_", path)


def load_exempt(classes_path: Path, ns: str | None) -> set[str]:
    """{name}.prov.exempt.txt 를 읽어 출처 면제 owl:Class IRI 집합 반환.

    파일 한 줄당 owl:Class local name (CamelCase). '#' 주석·빈 줄 허용.
    구조/추상 카테고리 노드(예: CostConcept, AnalysisMethod)처럼 evidence
    1차 출처가 본질적으로 없는 노드를 게이트에서 제외하기 위한 **명시 선언**.
    default-enforce: 리스트에 없으면 강제. 오타·rename 시 매칭이 끊겨 다시
    강제되는 안전한 실패(allowlist 의 반대).
    """
    if not ns:
        return set()
    p = classes_path.with_name(classes_path.name[: -len(".classes.ttl")] + EXEMPT_SUFFIX)
    if not p.exists():
        return set()
    out: set[str] = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.add(ns + line)
    return out


def build_source_index(target: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """모든 entities.jsonl 을 스캔해 두 조인 인덱스를 구축.

    explain(개념) + system/semantic(백킹) 양쪽을 본다.
      - id_index:  entity id → source_refs (정본 조인 키; dct:identifier ⋈ id)
      - owl_index: entity owl_class(풀 IRI) → source_refs (폴백 키)

    폴백이 필요한 이유: owlgen 이 dct:identifier annotation 을 드롭하는 컴파일
    도메인(enterprise·legal 등)은 ttl 에 identifier 가 없어 id 조인이 불가하다.
    이때 entities.jsonl 의 owl_class 풀 IRI 를 ttl 의 owl:Class subject IRI 와
    직접 매칭해 출처를 잇는다.
    """
    id_index: dict[str, list[str]] = {}
    owl_index: dict[str, list[str]] = {}
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
                srcs = o.get("source_refs") or o.get("source_file") or o.get("source") or []
                if isinstance(srcs, str):
                    srcs = [srcs]
                if not srcs:
                    continue
                for key, idx in ((o.get("id"), id_index), (o.get("owl_class"), owl_index)):
                    if not key:
                        continue
                    idx.setdefault(key, [])
                    for s in srcs:
                        if s not in idx[key]:
                            idx[key].append(s)
    return id_index, owl_index


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


def gen_for_file(target: Path, classes_path: Path, src_index: dict, owl_index: dict, apply: bool) -> str:
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

    exempt = load_exempt(classes_path, ns)  # 구조/추상 클래스 출처 면제 (명시 선언)
    sources: set[str] = set()
    links: list[str] = []
    ungrounded: list[str] = []
    exempted: list[str] = []
    for cls, ident in rows:
        # 1차: dct:identifier ⋈ entity id, 폴백: subject IRI ⋈ entity owl_class
        srcs = src_index.get(ident, []) if ident else []
        if not srcs and ns:
            srcs = owl_index.get(ns + cls, [])
        if not srcs:
            if ns and (ns + cls) in exempt:
                exempted.append(cls)   # 게이트 제외, 출처 미상 경고 안 함
            else:
                ungrounded.append(cls)
            continue
        for src in srcs:
            sources.add(src)
            links.append(f"as:{cls} prov:hadPrimarySource <{slug_iri(src)}> .")

    if not sources:
        return (f"SKIP  {label} — 조인 0건 (dct:identifier·owl_class 모두 미매칭, "
                f"{len(rows)} class). 출처 entities.jsonl 백필 필요.")

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
    ]
    if exempted:
        head.append(f"@prefix kb:   <{META_NS}> .")
    head.append("")
    head.append("# ── 1차 출처 노드 (prov:Entity) ─────────────────────────────")
    for src in sorted(sources):
        head.append(f"<{slug_iri(src)}> a prov:Entity ;")
        head.append(f'    dct:source "{src}" ;')
        head.append(f'    rdfs:label "{src}" .')
    head.append("")
    head.append("# ── owl:Class → 1차 출처 파생 링크 ──────────────────────────")
    markers: list[str] = []
    if exempted:
        markers.append("")
        markers.append("# ── 구조/추상 클래스 (출처 면제 — 게이트 제외, prov.exempt.txt 큐레이트) ──")
        markers += [f"as:{c} a kb:StructuralClass ." for c in sorted(exempted)]
    prov_ttl = "\n".join(head + sorted(links) + markers) + "\n"

    # ── prov.shapes.ttl (namespace-scoped 게이트) ──────────────
    # 구조클래스 면제: kb:StructuralClass 마커 보유 노드를 타깃에서 제외 (default-enforce).
    kb_decl = (f'\n            sh:declare [ sh:prefix "kb" ; sh:namespace '
               f'"{META_NS}"^^xsd:anyURI ] ;' if exempted else "")
    exempt_filter = ("\n                FILTER NOT EXISTS { ?this a kb:StructuralClass }"
                     if exempted else "")
    exempt_note = (f"\n# 구조/추상 클래스 {len(exempted)}개는 출처 면제(게이트 제외): "
                   f"{', '.join(sorted(exempted))}." if exempted else "")
    shapes_ttl = f'''# {name}.prov.shapes.ttl  — GENERATED ARTIFACT (do not edit)
# 재생성: msm-ontology prov --domain {domain_rel} --apply
# {ns} 네임스페이스 owl:Class 는 prov:hadPrimarySource 최소 1개 필수.{exempt_note}

@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

[]  a sh:NodeShape ;
    sh:name "ClassProvenanceShape" ;
    sh:target [
        a sh:SPARQLTarget ;
        sh:prefixes [
            sh:declare [ sh:prefix "owl" ; sh:namespace "http://www.w3.org/2002/07/owl#"^^xsd:anyURI ] ;{kb_decl}
        ] ;
        sh:select """
            SELECT ?this WHERE {{
                ?this a owl:Class .
                FILTER(STRSTARTS(STR(?this), "{ns}")){exempt_filter}
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

    joined = len(rows) - len(ungrounded) - len(exempted)
    msg = (f"{verb} {domain} — {joined}/{len(rows)} class / "
           f"{len(links)} link / {len(sources)} source")
    if exempted:
        msg += f" / 면제 {len(exempted)}"
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

    src_index, owl_index = build_source_index(target)
    print(f"source index: {len(src_index)} id-key, {len(owl_index)} owl_class-key (→ source_refs)")
    print(f"mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print()

    files = discover_classes_files(target, None if args.all else args.domain)
    if not files:
        scope = "전역" if args.all else args.domain
        print(f"대상 *.classes.ttl 없음 ({scope})")
        return 0
    for f in files:
        print(gen_for_file(target, f, src_index, owl_index, args.apply))
    return 0


if __name__ == "__main__":
    sys.exit(main())
