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


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="axiom", description="OWL TBox 공리(HITL) 저작 — 결과 가시화 후 승인 시 병합"
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

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
