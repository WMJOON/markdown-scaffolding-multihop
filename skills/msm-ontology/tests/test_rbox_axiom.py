#!/usr/bin/env python
"""test_rbox_axiom — P2 RBox 공리 저작 + owl_postprocess 확장 (SPEC §5 P2, AC-R1/AC-R2).

인수는 **TTL 트리플 레벨**이다 (advisor: P2 는 추론 레벨이 아님 — property round-trip 은 P3).
검증:
  A1  axiom property --characteristic Transitive → owl:TransitiveProperty 트리플
  A2  --inverse → owl:inverseOf (동일 ns IRI)
  A3  --subproperty-of → rdfs:subPropertyOf (동일 ns IRI)
  A4  --chain R S → owl:propertyChainAxiom ( R S ) — **순서 보존** (R∘S≠S∘R)
  A5  D-1 게이트: 미선언 role 에 공리 부착 거부 / chain 요소 미선언 거부
  A6  멱등성: carrier 제거 설계로 postprocess 재실행 시 chain 1개 유지 (double-emit 없음)
  A7  materialize 가 rbox-compile 을 호출해 owl/{domain}.rbox.ttl 생성 (advisor Blind #1)
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import rbox  # noqa: E402
import axiom  # noqa: E402
import owl_postprocess as pp  # noqa: E402
import rdflib  # noqa: E402

OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")
RDFS = rdflib.namespace.RDFS
NS = "https://example.org/msm/demo/"


def _ns(**kw):
    import argparse
    return argparse.Namespace(**kw)


def _ok(cond, label):
    print(f"[{'OK' if cond else 'FAIL'}] {label}")
    return cond


def _declare(target, domain, label, evidence):
    return rbox.cmd_add_relation(_ns(
        target=str(target), domain=domain, label=label, alt=[], description=None,
        evidence=[evidence], status="accepted", apply=True))


def _prop(target, domain, role, *, characteristic=None, inverse=None,
          subproperty_of=None, chain=None, apply=True):
    return axiom.cmd_property(_ns(
        target=str(target), domain=domain, role=role, characteristic=characteristic,
        inverse=inverse, subproperty_of=subproperty_of, chain=chain,
        domain_class=None, range=None, show_inferences=False, apply=apply))


def _compile(target, domain, postprocess=True):
    return rbox.cmd_compile(_ns(
        target=str(target), domain=domain, out_dir=None,
        no_postprocess=not postprocess, apply=True))


def main() -> int:
    import warnings
    warnings.filterwarnings("ignore")
    passed = True
    tmp = Path(tempfile.mkdtemp(prefix="rbox_axiom_"))
    target = tmp / "kb"
    domain = "demo"

    # 선언 (D-1: 공리 부착 전 role 존재 필수)
    for lbl, ev in [("uses", "e1"), ("requires", "e2"), ("depends on", "e3"),
                    ("used by", "e4"), ("is part of", "e5")]:
        _declare(target, domain, lbl, f"evidence:seed:{ev}")

    # ── 공리 부착 ──
    _prop(target, domain, "is_part_of", characteristic="Transitive")
    _prop(target, domain, "uses", inverse="used_by")
    _prop(target, domain, "uses", subproperty_of="depends_on")
    _prop(target, domain, "depends_on", chain=["uses", "requires"])  # uses∘requires ⊑ depends_on

    # ── 컴파일 → 트리플 검증 ──
    _compile(target, domain, postprocess=True)
    ttl = target / "ontology" / "owl" / f"{domain}.rbox.ttl"
    g = rdflib.Graph().parse(data=ttl.read_text(encoding="utf-8"), format="turtle")

    U = rdflib.URIRef(NS + "uses")
    DEP = rdflib.URIRef(NS + "depends_on")
    IPO = rdflib.URIRef(NS + "is_part_of")

    passed &= _ok((IPO, rdflib.RDF.type, OWL.TransitiveProperty) in g,
                  "A1 characteristic → owl:TransitiveProperty")
    passed &= _ok((U, OWL.inverseOf, rdflib.URIRef(NS + "used_by")) in g,
                  "A2 inverse → owl:inverseOf (동일 ns)")
    passed &= _ok((U, RDFS.subPropertyOf, DEP) in g,
                  "A3 subproperty_of → rdfs:subPropertyOf (동일 ns)")

    # A4 chain + 순서
    chain_lists = list(g.objects(DEP, OWL.propertyChainAxiom))
    chain_order = None
    if len(chain_lists) == 1:
        chain_order = [str(x).split("/")[-1] for x in rdflib.collection.Collection(g, chain_lists[0])]
    passed &= _ok(chain_order == ["uses", "requires"],
                  f"A4 chain → propertyChainAxiom 순서 보존 (got {chain_order})")

    # ── A5 D-1 게이트 ──
    rc_undeclared = _prop(target, domain, "frobnicate", characteristic="Symmetric")
    passed &= _ok(rc_undeclared != 0, "A5 미선언 role 공리 부착 거부")
    rc_badchain = _prop(target, domain, "uses", chain=["uses", "nonexistent"])
    passed &= _ok(rc_badchain != 0, "A5 chain 요소 미선언 거부")

    # ── A6 멱등성 (carrier 제거 설계) ──
    _compile(target, domain, postprocess=False)   # carrier 살아있는 base ttl
    pp.postprocess_ttl(ttl, apply=True, keep_carriers=False)   # 1차: carrier→chain, carrier 제거
    pp.postprocess_ttl(ttl, apply=True, keep_carriers=False)   # 2차: carrier 없음 → no-op
    g2 = rdflib.Graph().parse(data=ttl.read_text(encoding="utf-8"), format="turtle")
    n_chains = len(list(g2.objects(DEP, OWL.propertyChainAxiom)))
    passed &= _ok(n_chains == 1, f"A6 postprocess 재실행 후 chain 1개 (double-emit 없음, got {n_chains})")

    # ── A7 materialize → rbox.ttl (advisor Blind #1) ──
    mtarget = tmp / "kb2"
    _declare(mtarget, domain, "uses", "evidence:seed:m1")
    _materialize_argv(mtarget)
    rbox_ttl = mtarget / "ontology" / "owl" / f"{domain}.rbox.ttl"
    passed &= _ok(rbox_ttl.exists(), "A7 materialize → owl/demo.rbox.ttl 생성")

    print()
    print("RBOX P2 AXIOM TESTS PASS" if passed else "RBOX P2 AXIOM TESTS **FAIL**")
    return 0 if passed else 1


def _materialize_argv(mtarget) -> int:
    """materialize.main() 은 argparse(sys.argv) 기반 — argv 교체로 호출."""
    import materialize
    orig = sys.argv[:]
    sys.argv = ["materialize", "--target", str(mtarget), "--apply"]
    try:
        materialize.main()
        return 0
    except SystemExit as e:
        return int(e.code or 0)
    finally:
        sys.argv = orig


if __name__ == "__main__":
    raise SystemExit(main())
