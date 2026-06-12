#!/usr/bin/env python3
"""msm-ontology axiom — OWL TBox 공리(HITL) 저작 도구.

설계 철학 (RDF=LLM / OWL=HITL):
  ABox 사실(RDF)은 evidence/LLM 이 채우는 자동화 층이지만, TBox 공리(OWL)는 추론
  blast-radius 가 커서 **사람이 대화로 결정**하는 층이다. 이 도구는 OWL 을 자동
  생성하지 않는다 — 사람이 제안한 공리의 **결과를 커밋 전에 가시화**하고(컴파일된
  OWL + 현 ABox 에 대한 추론 consequence), HITL 승인(`--apply`) 후에만 LinkML 정본에
  주석 보존 상태로 병합한다.

지원 공리 (v0.13.0 데모 슬라이스): classification-rule
  사람이 "이런 조건을 만족하면 이 클래스로 분류" 를 선언 → owlgen 이 충분조건 GCI
  (intersection ⊑ class) 로 컴파일 → reasoner 가 인스턴스를 재분류.
  ⚠️ 이는 owl:equivalentClass(양방향 ≡)가 **아니라** 충분조건(단방향 ⊑)이다.

Usage:
  # 미리보기 (기본, compile 만 — 빠름): YAML diff + 컴파일된 OWL
  msm-ontology axiom classification-rule --target REPO --domain D \\
      --class MultimodalModel --is-a TransformerMLMModel \\
      --some canBeUsedFor:ImageGeneration

  # 추론 consequence 까지 (현 ABox 에 무엇이 재분류되는지 — Pellet, 느림)
  ...  --show-inferences

  # HITL 승인 후 LinkML 정본에 병합 (주석 보존)
  ...  --apply
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

TOOL_VERSION = "msm-ontology/0.13.0"
SCRIPT_DIR = Path(__file__).resolve().parent


def _log(msg: str, level: str = "info") -> None:
    prefix = {"info": "[*]", "ok": "[+]", "warn": "[!]", "err": "[x]"}[level]
    print(f"{prefix} {msg}", file=sys.stderr, flush=True)


def _build_rule(is_a: str | None, somes: list[str]) -> dict:
    """--is-a + --some slot:Range → LinkML classification_rules dict."""
    rule: dict = {}
    if is_a:
        rule["is_a"] = is_a
    slot_conditions: dict = {}
    for spec in somes:
        if ":" not in spec:
            _log(f"--some 형식 오류 '{spec}' (slot:RangeClass 이어야 함)", "err")
            sys.exit(2)
        slot, rng = spec.split(":", 1)
        slot_conditions[slot] = {"range": rng, "required": True}
    if slot_conditions:
        rule["slot_conditions"] = slot_conditions
    return rule


def _rule_yaml_snippet(cls: str, rule: dict) -> str:
    import yaml
    block = {cls: {"classification_rules": rule}}
    text = yaml.safe_dump({"classes": block}, sort_keys=False, allow_unicode=True)
    return text


def _inject_rule(def_path: Path, cls: str, rule: dict, is_a: str | None, out_path: Path) -> bool:
    """definition YAML 을 ruamel 라운드트립으로 로드해 classes[cls].classification_rules 주입.

    주석/순서 보존. 클래스가 없으면 생성(is_a + rule). out_path 에 기록.
    """
    try:
        from ruamel.yaml import YAML
    except ImportError:
        return False
    yamlrt = YAML()
    yamlrt.preserve_quotes = True
    with def_path.open(encoding="utf-8") as f:
        doc = yamlrt.load(f)
    classes = doc.get("classes")
    if classes is None:
        _log("definition 에 classes 섹션 없음", "err")
        return False
    if cls not in classes:
        new_cls = {}
        if is_a:
            new_cls["is_a"] = is_a
        new_cls["classification_rules"] = rule
        classes[cls] = new_cls
        _log(f"클래스 '{cls}' 없음 → is_a={is_a} 로 신규 생성", "warn")
    else:
        if classes[cls] is None:
            classes[cls] = {}
        classes[cls]["classification_rules"] = rule
    with out_path.open("w", encoding="utf-8") as f:
        yamlrt.dump(doc, f)
    return True


def _compile_preview(candidate_def: Path, cls: str) -> None:
    """후보 definition 을 owlgen 으로 컴파일해 클래스 관련 OWL 트리플(특히 GCI) 표시."""
    try:
        from linkml.generators.owlgen import OwlSchemaGenerator
        from rdflib import Graph
    except ImportError as e:  # noqa: BLE001
        _log(f"compile 미리보기 불가 ({e})", "warn")
        return
    import warnings
    warnings.filterwarnings("ignore")
    try:
        ttl = OwlSchemaGenerator(str(candidate_def), use_native_uris=False).serialize()
    except Exception as e:  # noqa: BLE001
        _log(f"compile 실패: {e}", "err")
        return
    g = Graph()
    g.parse(data=ttl, format="turtle")
    print("  --- 컴파일된 OWL (충분조건 GCI: intersection ⊑ "
          f"{cls}, ≠ equivalentClass) ---")
    shown = 0
    for line in ttl.splitlines():
        s = line.strip()
        if any(k in s for k in ("Restriction", "onProperty", "someValuesFrom",
                                "intersectionOf", "subClassOf", cls)):
            print(f"      {s}")
            shown += 1
    if shown == 0:
        _log("GCI 트리플을 찾지 못함 — classification_rules 가 비었는지 확인", "warn")


def _show_inferences(target: Path, domain: str, candidate_def: Path) -> None:
    """후보 TBox + 현 ABox 로 materialize 해 --class 로 재분류되는 individual 표시."""
    tmp = Path(tempfile.mkdtemp(prefix="msm_axiom_infer_"))
    try:
        (tmp / "ontology" / "definition").mkdir(parents=True)
        # 후보 definition 만 복사 (해당 domain) + 현 ABox 전체 복사
        shutil.copy(candidate_def, tmp / "ontology" / "definition" / f"{domain}.yaml")
        src_abox = target / "ontology" / "Abox"
        if src_abox.exists():
            shutil.copytree(src_abox, tmp / "ontology" / "Abox",
                            ignore=shutil.ignore_patterns("_inferred", "md"))
        r = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "materialize.py"),
             "--target", str(tmp), "--apply"],
            capture_output=True, text=True,
        )
        inferred = tmp / "ontology" / "Abox" / "_inferred" / "inferred.jsonl"
        print("  --- 추론 consequence (현 ABox 에 적용 시) ---")
        if not inferred.exists():
            print("      (재분류되는 individual 없음)")
            return
        n = 0
        for line in inferred.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            print(f"      {rec['id']}: {rec['asserted_types']} +추론→ {rec['inferred_types']}")
            n += 1
        if n == 0:
            print("      (재분류되는 individual 없음)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_classification_rule(args) -> int:
    target = Path(args.target).resolve()
    def_path = target / "ontology" / "definition" / f"{args.domain}.yaml"
    if not def_path.exists():
        _log(f"definition 없음: {def_path}", "err")
        return 1

    rule = _build_rule(args.is_a, args.some or [])
    if "slot_conditions" not in rule:
        _log("최소 하나의 --some slot:RangeClass 가 필요합니다", "err")
        return 2

    # 1) YAML 스니펫 (사람이 검토/붙여넣기용)
    print(f"[제안] classes.{args.class_name}.classification_rules "
          f"→ {def_path.relative_to(target)}")
    print("  --- LinkML 스니펫 ---")
    for line in _rule_yaml_snippet(args.class_name, rule).splitlines():
        print(f"      {line}")

    # 2) 후보 컴파일 → OWL 미리보기 (항상, compile 만 — 빠름)
    tmp = Path(tempfile.mkdtemp(prefix="msm_axiom_cand_"))
    candidate = tmp / f"{args.domain}.yaml"
    has_ruamel = _inject_rule(def_path, args.class_name, rule, args.is_a, candidate)
    if not has_ruamel:
        _log("ruamel.yaml 없음 — 컴파일 미리보기/apply 불가. 위 스니펫을 수동 병합하세요.", "warn")
        shutil.rmtree(tmp, ignore_errors=True)
        return 3
    _compile_preview(candidate, args.class_name)

    # 3) (옵션) 추론 consequence — Pellet, 느림
    if args.show_inferences:
        _show_inferences(target, args.domain, candidate)

    # 4) apply (HITL gate) — 주석 보존 병합
    if args.apply:
        if _inject_rule(def_path, args.class_name, rule, args.is_a, def_path):
            _log(f"applied: classification_rules → {def_path} (주석 보존)", "ok")
        else:
            _log("ruamel.yaml 없음 — apply 불가. 스니펫을 수동 병합하세요.", "err")
            shutil.rmtree(tmp, ignore_errors=True)
            return 3
    else:
        _log("미리보기만 수행 (commit 하려면 --apply). OWL 은 사람 승인 후에만 병합됩니다.")

    shutil.rmtree(tmp, ignore_errors=True)
    return 0


# ───────────────────────────────────── RBox property axiom (v0.14.0, AC-R2)

# --characteristic 단축형 → owl_characteristic 값
_CHAR_MAP = {
    "Functional": "FunctionalProperty",
    "InverseFunctional": "InverseFunctionalProperty",
    "Symmetric": "SymmetricProperty",
    "Asymmetric": "AsymmetricProperty",
    "Transitive": "TransitiveProperty",
    "Reflexive": "ReflexiveProperty",
    "Irreflexive": "IrreflexiveProperty",
}


def _roles_path(target: Path, domain: str) -> Path:
    return target / "ontology" / "Rbox" / "roles" / f"{domain}.yaml"


def _load_roles_doc(roles_path: Path):
    from ruamel.yaml import YAML
    y = YAML()
    y.preserve_quotes = True
    y.indent(mapping=2, sequence=4, offset=2)
    with roles_path.open(encoding="utf-8") as f:
        return y, y.load(f)


def _declared_roles(doc) -> set:
    return set((doc.get("slots") or {}).keys())


def _build_property_updates(args, declared: set) -> tuple[dict, dict, list]:
    """returns (annotation_updates, native_updates, errors)."""
    ann: dict = {}
    native: dict = {}
    errors: list = []

    if args.characteristic:
        val = _CHAR_MAP.get(args.characteristic)
        if not val:
            errors.append(f"알 수 없는 --characteristic '{args.characteristic}' "
                          f"(허용: {', '.join(_CHAR_MAP)})")
        else:
            ann["owl_characteristic"] = val
    if args.inverse:
        if args.inverse not in declared:
            errors.append(f"--inverse 대상 role '{args.inverse}' 미선언 "
                          f"(먼저 rbox add-relation 필요 — D-1 게이트)")
        ann["inverse_of"] = args.inverse
    if args.subproperty_of:
        if args.subproperty_of not in declared:
            errors.append(f"--subproperty-of 대상 role '{args.subproperty_of}' 미선언 (D-1 게이트)")
        ann["subproperty_of"] = args.subproperty_of
    if args.chain:
        if len(args.chain) < 2:
            errors.append("--chain 은 2개 이상 role 이 필요 (R∘S⊑T)")
        for r in args.chain:
            if r not in declared:
                errors.append(f"--chain 요소 role '{r}' 미선언 (D-1 게이트)")
        ann["property_chain"] = ",".join(args.chain)
    if args.domain_class:
        native["domain"] = args.domain_class
    if args.range:
        native["range"] = args.range
    return ann, native, errors


def _inject_property(roles_path: Path, role: str, ann_updates: dict,
                     native_updates: dict, out_path: Path) -> bool:
    """roles YAML 의 slots[role] 에 annotation/native 공리를 ruamel 라운드트립 병합."""
    try:
        from ruamel.yaml import YAML  # noqa: F401
    except ImportError:
        return False
    y, doc = _load_roles_doc(roles_path)
    slots = doc.get("slots") or {}
    slot = slots.get(role)
    if slot is None:
        _log(f"role '{role}' 미선언 — axiom 부착 불가 (D-1: rbox add-relation 먼저)", "err")
        return False
    from ruamel.yaml.comments import CommentedMap
    if ann_updates:
        ann = slot.get("annotations")
        if ann is None:
            ann = CommentedMap()
            slot["annotations"] = ann
        for k, v in ann_updates.items():
            ann[k] = v
    for k, v in native_updates.items():
        slot[k] = v
    with out_path.open("w", encoding="utf-8") as f:
        y.dump(doc, f)
    return True


def _rbox_compile_preview(candidate_roles: Path, role: str) -> None:
    """후보 roles 를 owlgen + owl_postprocess 로 컴파일해 해당 role 의 RBox OWL 트리플 표시."""
    try:
        from linkml.generators.owlgen import OwlSchemaGenerator
        from rdflib import Graph
    except ImportError as e:  # noqa: BLE001
        _log(f"compile 미리보기 불가 ({e})", "warn")
        return
    import warnings as _w
    _w.filterwarnings("ignore")
    tmp_ttl = candidate_roles.with_suffix(".rbox.ttl")
    try:
        ttl = OwlSchemaGenerator(str(candidate_roles), use_native_uris=False).serialize()
    except Exception as e:  # noqa: BLE001
        _log(f"compile 실패: {e}", "err")
        return
    tmp_ttl.write_text(ttl, encoding="utf-8")
    # owl_postprocess 로 subPropertyOf/propertyChainAxiom/inverseOf/characteristic 주입
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        import owl_postprocess as pp  # type: ignore
        pp.postprocess_ttl(tmp_ttl, apply=True, keep_carriers=False)
    except Exception as e:  # noqa: BLE001
        _log(f"owl_postprocess 생략 ({e})", "warn")
    g = Graph()
    g.parse(str(tmp_ttl), format="turtle")
    print("  --- 컴파일된 RBox OWL (postprocess 후) ---")
    shown = 0
    for line in g.serialize(format="turtle").splitlines():
        s = line.strip()
        if any(k in s for k in ("subPropertyOf", "propertyChainAxiom", "inverseOf",
                                "Property", "onProperty", role)):
            print(f"      {s}")
            shown += 1
    if shown == 0:
        _log("RBox 트리플을 찾지 못함 — 공리가 비었는지 확인", "warn")


def cmd_property(args) -> int:
    target = Path(args.target).resolve()
    roles_path = _roles_path(target, args.domain)
    if not roles_path.exists():
        _log(f"roles 파일 없음: {roles_path} (rbox add-relation 먼저)", "err")
        return 1

    _, doc = _load_roles_doc(roles_path)
    declared = _declared_roles(doc)
    if args.role not in declared:
        _log(f"role '{args.role}' 미선언 — axiom 부착 불가 (D-1: rbox add-relation 먼저)", "err")
        return 1

    ann_updates, native_updates, errors = _build_property_updates(args, declared)
    if errors:
        for e in errors:
            _log(e, "err")
        return 2
    if not ann_updates and not native_updates:
        _log("부착할 공리가 없습니다 (--characteristic/--inverse/--subproperty-of/--chain/--domain/--range)", "err")
        return 2

    print(f"[제안] slots.{args.role} 공리 → {roles_path.relative_to(target)}")
    print(f"  annotations: {dict(ann_updates)}" + (f" | native: {dict(native_updates)}" if native_updates else ""))

    tmp = Path(tempfile.mkdtemp(prefix="msm_rbox_axiom_"))
    candidate = tmp / f"{args.domain}.yaml"
    if not _inject_property(roles_path, args.role, ann_updates, native_updates, candidate):
        shutil.rmtree(tmp, ignore_errors=True)
        return 3
    _rbox_compile_preview(candidate, args.role)

    if args.show_inferences:
        _log("(참고) property-value 추론은 P3 graph-diff 전까지 round-trip 안 됨 — "
             "여기서는 type-consequence 만 의미 있음 (SPEC §3.1 / core.md §7.3)", "warn")

    if args.apply:
        if _inject_property(roles_path, args.role, ann_updates, native_updates, roles_path):
            _log(f"applied: slots.{args.role} 공리 → {roles_path} (주석 보존)", "ok")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
            return 3
    else:
        _log("미리보기만 수행 (commit 하려면 --apply). OWL 은 사람 승인 후에만 병합됩니다.")

    shutil.rmtree(tmp, ignore_errors=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="axiom", description="OWL 공리(HITL) 저작 — 결과 가시화 후 승인 시 병합"
    )
    sub = parser.add_subparsers(dest="kind", required=True)

    cr = sub.add_parser("classification-rule",
                        help="충분조건 GCI (조건 만족 시 클래스로 분류)")
    cr.add_argument("--target", required=True, help="KB 루트 경로")
    cr.add_argument("--domain", required=True, help="대상 도메인 (definition/{domain}.yaml)")
    cr.add_argument("--class", dest="class_name", required=True, help="분류 대상 클래스")
    cr.add_argument("--is-a", default=None, help="GCI 전제의 base 클래스")
    cr.add_argument("--some", action="append", metavar="SLOT:RANGE",
                    help="존재 제약 (slot some Range). 복수 지정 가능")
    cr.add_argument("--show-inferences", action="store_true",
                    help="현 ABox 에 대한 추론 consequence 표시 (Pellet, 느림)")
    cr.add_argument("--apply", action="store_true",
                    help="HITL 승인 — LinkML 정본에 주석 보존 병합 (기본: 미리보기)")
    cr.set_defaults(func=cmd_classification_rule)

    pr = sub.add_parser("property",
                        help="RBox 공리 (characteristic/inverse/subproperty/chain/domain/range)")
    pr.add_argument("--target", required=True, help="KB 루트 경로")
    pr.add_argument("--domain", required=True, help="대상 도메인 (Rbox/roles/{domain}.yaml)")
    pr.add_argument("--role", required=True, help="공리를 부착할 role (먼저 rbox add-relation 필요)")
    pr.add_argument("--characteristic", default=None, choices=list(_CHAR_MAP),
                    help="property 특성 (Transitive/Symmetric/Functional/...)")
    pr.add_argument("--inverse", default=None, metavar="ROLE", help="owl:inverseOf 대상 role")
    pr.add_argument("--subproperty-of", dest="subproperty_of", default=None,
                    metavar="ROLE", help="rdfs:subPropertyOf 대상 role")
    pr.add_argument("--chain", nargs="+", default=None, metavar="ROLE",
                    help="propertyChainAxiom (순서 중요: R S → R∘S⊑이role)")
    pr.add_argument("--domain-class", dest="domain_class", default=None,
                    metavar="CLASS", help="rdfs:domain")
    pr.add_argument("--range", default=None, metavar="CLASS", help="rdfs:range")
    pr.add_argument("--show-inferences", action="store_true",
                    help="(P2 한정: type-consequence 만 — property round-trip 은 P3)")
    pr.add_argument("--apply", action="store_true",
                    help="HITL 승인 — roles YAML 에 주석 보존 병합 (기본: 미리보기)")
    pr.set_defaults(func=cmd_property)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
