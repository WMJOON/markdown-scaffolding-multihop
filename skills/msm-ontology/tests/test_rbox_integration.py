#!/usr/bin/env python
"""test_rbox_integration — 실제 ABox 경로 end-to-end (SPEC §5, advisor 검증 #2).

단위 테스트들은 ABox 를 hand-written rdflib turtle 로 만들지만, 이 테스트는 **실제 파이프라인**:
  definition/{d}.yaml (TBox) + Rbox/roles/{d}.yaml (roles+chain) + Abox/{d}.yaml (instances)
  → materialize (compile + rbox-compile + **abox-compile** + reason)
  → inferred.jsonl 에 chain 멀티홉 fact.

핵심: abox-compile 의 **실제 출력**이 graph-diff 필터(s∈NamedIndividual ∧ p∈ObjProp ∧ o∈Ind)와
정합하는지 — hand-fixture 가 가정하던 NamedIndividual 타이핑·네임스페이스를 실측 검증한다.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import rbox  # noqa: E402
import axiom  # noqa: E402

DOMAIN = "wiring"

DEFINITION = """\
id: https://example.org/msm/wiring
name: msm_wiring
prefixes: {linkml: https://w3id.org/linkml/, ex: https://example.org/msm/wiring/}
default_prefix: ex
default_range: string
imports: [linkml:types]
classes:
  Agent: {}
  Tool: {}
  Runtime: {}
"""

ABOX = """\
# 실제 ABox YAML — abox-compile 이 individual + object-property 로 컴파일
instances:
  agent1:
    instance_of: Agent
    uses: [tool1]
  tool1:
    instance_of: Tool
    requires: [runtime1]
  runtime1:
    instance_of: Runtime
"""


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
    tmp = Path(tempfile.mkdtemp(prefix="rbox_integ_"))
    target = tmp / "kb"
    onto = target / "ontology"

    # TBox definition + ABox YAML (실제 파일)
    (onto / "definition").mkdir(parents=True)
    (onto / "definition" / f"{DOMAIN}.yaml").write_text(DEFINITION, encoding="utf-8")
    (onto / "Abox").mkdir(parents=True)
    (onto / "Abox" / f"{DOMAIN}.yaml").write_text(ABOX, encoding="utf-8")

    # RBox roles (실제 도구) — 네임스페이스는 definition 에서 도출돼야 함
    for lbl, ev in [("uses", "1"), ("requires", "2"), ("depends on", "3")]:
        rbox.cmd_add_relation(_ns(target=str(target), domain=DOMAIN, label=lbl, alt=[],
                                  description=None, evidence=[f"e:{ev}"], status="accepted", apply=True))
    axiom.cmd_property(_ns(target=str(target), domain=DOMAIN, role="depends_on",
                           characteristic=None, inverse=None, subproperty_of=None,
                           chain=["uses", "requires"], domain_class=None, range=None,
                           show_inferences=False, apply=True))

    # roles 네임스페이스가 definition ex prefix 를 재사용했는지 (정렬 확인)
    roles_doc_text = (onto / "Rbox" / "roles" / f"{DOMAIN}.yaml").read_text(encoding="utf-8")
    passed &= _ok("https://example.org/msm/wiring/" in roles_doc_text,
                  "roles ns = definition ex prefix 재사용 (reason 병합 정렬)")

    # ── 실제 materialize (compile + rbox-compile + abox-compile + reason) ──
    import materialize
    orig = sys.argv[:]
    sys.argv = ["materialize", "--target", str(target), "--apply"]
    try:
        materialize.main()
    except SystemExit as e:
        if e.code not in (0, None):
            print(f"[FAIL] materialize exit {e.code}")
            return 1
    finally:
        sys.argv = orig

    # abox-compile 실제 산출물 존재 확인
    abox_ttl = onto / "owl" / f"{DOMAIN}.abox.ttl"
    passed &= _ok(abox_ttl.exists(), "abox-compile 실제 산출 owl/wiring.abox.ttl")

    inferred = onto / "Abox" / "_inferred" / "inferred.jsonl"
    if not _ok(inferred.exists(), "inferred.jsonl 생성"):
        return 1
    props = {}
    for line in inferred.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            if rec.get("inferred_properties"):
                props[rec["id"]] = rec["inferred_properties"]
    print(f"  inferred_properties = {json.dumps(props, ensure_ascii=False)}")

    # ★ 핵심: 실제 abox-compile 경로로 chain 멀티홉이 inferred 됨
    passed &= _ok(props.get("agent1", {}).get("depends_on") == ["runtime1"],
                  "★ 실제 ABox 경로: agent1 depends_on runtime1 (chain 멀티홉)")

    print()
    print("RBOX INTEGRATION TESTS PASS" if passed else "RBOX INTEGRATION TESTS **FAIL**")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
