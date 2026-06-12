#!/usr/bin/env python
"""test_rbox — P1 RBox first-class layer (SPEC §5 P1, AC-R6).

스크립트 하네스 컨벤션(이 스킬의 test_*.py 와 동일): def main() → exit code.
검증:
  R1  add-relation --apply 가 Rbox/roles/{domain}.yaml 에 role 선언 (status=draft)
  R2  evidence 누락 시 거부 (source_refs_missing)
  R3  중복 선언 거부
  R4  list 가 선언 role + status 표시
  R5  compile 이 roles YAML → owl/{domain}.rbox.ttl, role 이 owl:ObjectProperty 로 방출 (AC-R6 핵심)
  R6  aliases 보존
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import rbox  # noqa: E402


def _ns(**kw):
    import argparse
    return argparse.Namespace(**kw)


def _ok(cond, label):
    print(f"[{'OK' if cond else 'FAIL'}] {label}")
    return cond


def main() -> int:
    import warnings
    warnings.filterwarnings("ignore")
    passed = True
    tmp = Path(tempfile.mkdtemp(prefix="rbox_test_"))
    target = tmp / "kb"
    domain = "demo"

    # ── R2: evidence 누락 거부 ──
    rc = rbox.cmd_add_relation(_ns(
        target=str(target), domain=domain, label="uses",
        alt=[], description=None, evidence=[], status="draft", apply=True))
    passed &= _ok(rc == 1, "R2 evidence 누락 → exit 1 (source_refs_missing)")

    # ── R1: 정상 선언 ──
    rc = rbox.cmd_add_relation(_ns(
        target=str(target), domain=domain, label="uses",
        alt=["utilizes", "employs"], description="주체가 대상을 사용한다",
        evidence=["evidence:seed:demo1"], status="draft", apply=True))
    roles_yaml = target / "ontology" / "Rbox" / "roles" / f"{domain}.yaml"
    passed &= _ok(rc == 0 and roles_yaml.exists(), "R1 add-relation --apply → roles YAML 생성")

    from ruamel.yaml import YAML
    doc = YAML().load(roles_yaml.read_text(encoding="utf-8"))
    slot = (doc.get("slots") or {}).get("uses") or {}
    ann = slot.get("annotations") or {}
    passed &= _ok(ann.get("status") == "draft", "R1 status=draft 기록")
    passed &= _ok("evidence:seed:demo1" in str(ann.get("source_refs")), "R1 source_refs 기록")
    passed &= _ok(list(slot.get("aliases") or []) == ["utilizes", "employs"], "R6 aliases 보존")

    # ── R3: 중복 선언 거부 ──
    rc = rbox.cmd_add_relation(_ns(
        target=str(target), domain=domain, label="uses",
        alt=[], description=None, evidence=["evidence:seed:demo1"],
        status="draft", apply=True))
    passed &= _ok(rc == 1, "R3 중복 role 선언 → exit 1")

    # 두 번째 role 추가 (accepted)
    rbox.cmd_add_relation(_ns(
        target=str(target), domain=domain, label="requires",
        alt=[], description=None, evidence=["evidence:seed:demo2"],
        status="accepted", apply=True))

    # ── R4: list ──
    rc = rbox.cmd_list(_ns(target=str(target), domain=domain, status=None))
    passed &= _ok(rc == 0, "R4 list exit 0 (uses+requires)")

    # ── R5: compile → rbox.ttl + ObjectProperty (AC-R6) ──
    rc = rbox.cmd_compile(_ns(
        target=str(target), domain=domain, out_dir=None,
        no_postprocess=False, apply=True))
    ttl_path = target / "ontology" / "owl" / f"{domain}.rbox.ttl"
    passed &= _ok(rc == 0 and ttl_path.exists(), "R5 compile → owl/demo.rbox.ttl")

    import rdflib
    g = rdflib.Graph().parse(data=ttl_path.read_text(encoding="utf-8"), format="turtle")
    OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")
    objprop_iris = list(g.subjects(rdflib.RDF.type, OWL.ObjectProperty))
    objprops = {str(s).split("/")[-1] for s in objprop_iris}
    passed &= _ok("uses" in objprops and "requires" in objprops,
                  f"R5/AC-R6 role → owl:ObjectProperty 방출 (got {sorted(objprops)})")
    # 네임스페이스 정렬: role IRI 가 도메인 컨벤션(example.org/msm/{domain}/) 공유 (reason 병합 전제)
    ns_ok = any(str(s) == "https://example.org/msm/demo/uses" for s in objprop_iris)
    passed &= _ok(ns_ok, f"R5 role IRI 네임스페이스 정렬 (got {sorted(str(s) for s in objprop_iris)})")
    # skos altLabel à-la-carte 차용 (SPEC D-1)
    SKOS = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
    uses_iri = rdflib.URIRef("https://example.org/msm/demo/uses")
    alts = {str(o) for o in g.objects(uses_iri, SKOS.altLabel)}
    passed &= _ok(alts == {"utilizes", "employs"}, f"R6 aliases → skos:altLabel (got {alts})")

    print()
    print("RBOX P1 TESTS PASS" if passed else "RBOX P1 TESTS **FAIL**")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
