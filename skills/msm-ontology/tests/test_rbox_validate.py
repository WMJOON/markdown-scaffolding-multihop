#!/usr/bin/env python
"""test_rbox_validate — P4 RBox 정합 게이트 (SPEC §5 P4, AC-R7).

  V1  선언 role 만 쓰는 깨끗한 KB → exit 0
  V2  Abox 가 미선언 술어 사용 → exit 1 (undeclared_role)
  V3  Abox TTL 없음 → warn, exit 0
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import rbox  # noqa: E402
import rdflib  # noqa: E402

NS = "https://example.org/msm/demo/"
OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")
DOMAIN = "demo"


def _ns(**kw):
    import argparse
    return argparse.Namespace(**kw)


def _ok(cond, label):
    print(f"[{'OK' if cond else 'FAIL'}] {label}")
    return cond


def _declare(target, label, ev, status="accepted"):
    rbox.cmd_add_relation(_ns(target=str(target), domain=DOMAIN, label=label, alt=[],
                              description=None, evidence=[f"e:{ev}"], status=status, apply=True))


def _abox(target, pairs):
    owl_dir = target / "ontology" / "owl"
    owl_dir.mkdir(parents=True, exist_ok=True)
    g = rdflib.Graph()
    U = lambda n: rdflib.URIRef(NS + n)  # noqa: E731
    for s, p, o in pairs:
        g.add((U(s), rdflib.RDF.type, OWL.NamedIndividual))
        g.add((U(o), rdflib.RDF.type, OWL.NamedIndividual))
        g.add((U(s), U(p), U(o)))
    g.serialize(destination=str(owl_dir / "demo.abox.ttl"), format="turtle")


def _validate(target):
    return rbox.cmd_validate(_ns(target=str(target), domain=DOMAIN))


def main() -> int:
    import warnings
    warnings.filterwarnings("ignore")
    passed = True
    tmp = Path(tempfile.mkdtemp(prefix="rbox_val_"))

    # V1 clean
    t1 = tmp / "clean"
    _declare(t1, "uses", "1")
    _declare(t1, "requires", "2")
    rbox.cmd_compile(_ns(target=str(t1), domain=DOMAIN, out_dir=None, no_postprocess=False, apply=True))
    _abox(t1, [("a", "uses", "b"), ("b", "requires", "c")])
    passed &= _ok(_validate(t1) == 0, "V1 깨끗한 KB → exit 0")

    # V2 undeclared predicate in abox
    t2 = tmp / "undeclared"
    _declare(t2, "uses", "1")
    rbox.cmd_compile(_ns(target=str(t2), domain=DOMAIN, out_dir=None, no_postprocess=False, apply=True))
    _abox(t2, [("a", "uses", "b"), ("a", "frobnicate", "b")])  # frobnicate 미선언
    passed &= _ok(_validate(t2) == 1, "V2 미선언 술어 → exit 1")

    # V3 no abox ttl → warn, exit 0
    t3 = tmp / "noabox"
    _declare(t3, "uses", "1")
    passed &= _ok(_validate(t3) == 0, "V3 Abox TTL 없음 → warn, exit 0")

    print()
    print("RBOX P4 VALIDATE TESTS PASS" if passed else "RBOX P4 VALIDATE TESTS **FAIL**")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
