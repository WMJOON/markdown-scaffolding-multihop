#!/usr/bin/env python3
"""msm-ontology postprocess — owlgen이 못 내는 OWL 트리플을 compile 산출 TTL에 주입.

배경 (addendum PRD §3.1 / §3.4-3,4):
  linkml.generators.owlgen 는 다음을 정식 OWL로 내지 못한다(소스 확인):
    - owl:FunctionalProperty / owl:InverseFunctionalProperty  (relationship
      characteristics dict 에 functional 없음)
    - 다국어 rdfs:label "..."@lang                            (단일 언어 label만)
  대신 LinkML annotations 는 `<default_prefix>:<key> "<value>"` carrier 트리플로
  직렬화된다(예: `ex:label_ko "초안"`, `ex:owl_characteristic "FunctionalProperty"`).

본 후처리는 두 예약 annotation 키를 정식 OWL 로 변환한다(carrier 는 제거):
    label_<lang>:        "..."             → <subj> rdfs:label "..."@<lang>
    owl_characteristic:  "<X>Property"     → <subj> a owl:<X>Property

설계:
  - **TTL-only**: 소스 YAML 재파싱 불필요(annotations 는 이미 TTL carrier 트리플).
    rdflib 만 의존 → linkml 없이도 동작·테스트 가능.
  - **idempotent**: rdflib Graph 는 집합 → 재실행해도 동일.
  - **additive (논리 보강)**: owlgen base 의 논리 골격(class/subClassOf/property/
    domain/range)은 건드리지 않고, 예약 carrier 두 종만 정식 OWL 로 교체.

Usage:
  # 직접 모드 (단일 TTL 보강, 제자리)
  msm-ontology postprocess --ttl PATH [--apply] [--keep-carriers]
  # repo 모드 (out-dir 내 *.ttl 전체)
  msm-ontology postprocess --target REPO [--domain NAME] [--out-dir DIR] [--apply]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TOOL_VERSION = "msm-ontology/0.13.0"

# owl_characteristic 로 허용하는 property 특성 (owl: 네임스페이스 로컬명)
VALID_CHARACTERISTICS = {
    "FunctionalProperty",
    "InverseFunctionalProperty",
    "SymmetricProperty",
    "AsymmetricProperty",
    "TransitiveProperty",
    "ReflexiveProperty",
    "IrreflexiveProperty",
}

# label_<lang> 예약 키 (lang = 2~3 글자 + 선택적 region subtag, 예: ko, en, zh-Hans)
_LABEL_RE = re.compile(r"^label_([A-Za-z]{2,3}(?:-[A-Za-z0-9]+)*)$")
_CHARACTERISTIC_KEY = "owl_characteristic"


def _log(msg: str, level: str = "info") -> None:
    prefix = {"info": "[*]", "ok": "[+]", "warn": "[!]", "err": "[x]"}[level]
    print(f"{prefix} {msg}", file=sys.stderr, flush=True)


def _local_name(iri: str) -> str:
    """IRI 의 로컬명(마지막 / 또는 # 이후)을 반환."""
    tail = iri.rsplit("#", 1)[-1]
    tail = tail.rsplit("/", 1)[-1]
    return tail


def transform_graph(g):
    """rdflib Graph 를 제자리 변환.

    Returns (added_triples, carrier_triples, warnings):
      - added_triples:   새로 주입된 정식 OWL 트리플 리스트
      - carrier_triples: 원본 carrier annotation 트리플 리스트 (제거 후보)
      - warnings:        알 수 없는 characteristic 등 경고 메시지
    """
    from rdflib import Literal
    from rdflib.namespace import RDF, RDFS, OWL

    to_add: list = []
    carriers: list = []
    warnings: list = []

    for s, p, o in g:
        local = _local_name(str(p))

        if local == _CHARACTERISTIC_KEY:
            value = str(o)
            if value in VALID_CHARACTERISTICS:
                to_add.append((s, RDF.type, getattr(OWL, value)))
                carriers.append((s, p, o))
            else:
                warnings.append(
                    f"unknown owl_characteristic '{value}' on <{s}> "
                    f"(allowed: {', '.join(sorted(VALID_CHARACTERISTICS))})"
                )
            continue

        m = _LABEL_RE.match(local)
        if m:
            lang = m.group(1)
            to_add.append((s, RDFS.label, Literal(str(o), lang=lang)))
            carriers.append((s, p, o))

    added_triples = []
    for triple in to_add:
        if triple not in g:
            g.add(triple)
            added_triples.append(triple)

    return added_triples, carriers, warnings


def _load_rdflib():
    try:
        import rdflib  # noqa: F401
        return rdflib
    except ImportError:
        _log("rdflib not installed. Run: pip install rdflib", "err")
        sys.exit(1)


def postprocess_ttl(ttl_path: Path, apply: bool, keep_carriers: bool) -> bool:
    """단일 TTL 파일 후처리. 변경 발생 시 True."""
    rdflib = _load_rdflib()

    g = rdflib.Graph()
    try:
        g.parse(str(ttl_path), format="turtle")
    except Exception as e:  # noqa: BLE001
        _log(f"parse 실패 {ttl_path.name}: {e}", "err")
        return False

    added_triples, carriers, warnings = transform_graph(g)

    for w in warnings:
        _log(w, "warn")

    removed = 0
    if not keep_carriers:
        for triple in carriers:
            if triple in g:
                g.remove(triple)
                removed += 1

    if not added_triples and removed == 0:
        _log(f"{ttl_path.name}: 보강할 carrier 없음 (변경 없음)")
        return False

    carrier_note = "" if keep_carriers else f", -{removed} carrier 제거"
    if apply:
        g.serialize(destination=str(ttl_path), format="turtle")
        _log(f"{ttl_path.name}: +{len(added_triples)} OWL 트리플 주입{carrier_note}", "ok")
    else:
        _log(f"[dry] {ttl_path.name}: +{len(added_triples)} OWL 트리플 주입 예정"
             f"{carrier_note.replace('제거', '제거 예정')}")
        for s, p, o in added_triples:
            print(f"      {s.n3(g.namespace_manager)} {p.n3(g.namespace_manager)} "
                  f"{o.n3(g.namespace_manager)}")
    return True


def _resolve_owl_dir(target: Path, out_dir):
    if out_dir:
        p = Path(out_dir)
        return p if p.is_absolute() else (target / p)
    return target / "ontology" / "owl"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="owlgen 미지원 OWL 트리플(FunctionalProperty/다국어 label)을 TTL에 주입"
    )
    parser.add_argument("--ttl", default=None, help="직접 모드: 단일 TTL 파일")
    parser.add_argument("--target", default=None, help="repo 모드: KB 루트 경로")
    parser.add_argument("--domain", default=None, help="repo 모드: 특정 도메인 TTL만")
    parser.add_argument("--out-dir", default=None,
                        help="repo 모드: TTL 디렉토리 (기본: <target>/ontology/owl)")
    parser.add_argument("--apply", action="store_true", help="실제 파일 쓰기 (기본: dry-run)")
    parser.add_argument("--keep-carriers", action="store_true",
                        help="carrier annotation 트리플 보존 (기본: 제거)")
    args = parser.parse_args()

    if not args.ttl and not args.target:
        _log("--ttl 또는 --target 중 하나는 필수", "err")
        sys.exit(2)

    mode = "apply" if args.apply else "dry-run"

    # 직접 모드
    if args.ttl:
        ttl_path = Path(args.ttl).resolve()
        if not ttl_path.exists():
            _log(f"TTL 없음: {ttl_path}", "err")
            sys.exit(1)
        _log(f"postprocess [{mode}] — {ttl_path.name}")
        postprocess_ttl(ttl_path, args.apply, args.keep_carriers)
        sys.exit(0)

    # repo 모드
    target = Path(args.target).resolve()
    owl_dir = _resolve_owl_dir(target, args.out_dir)
    if not owl_dir.exists():
        _log(f"TTL 디렉토리 없음: {owl_dir} — compile 을 먼저 실행하세요.", "err")
        sys.exit(1)

    if args.domain:
        ttl_files = [owl_dir / f"{args.domain}.ttl"]
        if not ttl_files[0].exists():
            _log(f"파일 없음: {ttl_files[0]}", "err")
            sys.exit(1)
    else:
        ttl_files = sorted(owl_dir.glob("*.ttl"))
        if not ttl_files:
            _log(f"TTL 파일 없음: {owl_dir}", "warn")
            sys.exit(0)

    _log(f"postprocess [{mode}] — {len(ttl_files)}개 TTL @ {owl_dir}")
    changed = sum(
        postprocess_ttl(f, args.apply, args.keep_carriers) for f in ttl_files
    )
    _log(f"완료: {changed}/{len(ttl_files)}개 변경", "ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
