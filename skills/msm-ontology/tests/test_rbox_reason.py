#!/usr/bin/env python
"""test_rbox_reason — P3 graph-diff 추론 캡처 (SPEC §5 P3, AC-R3/AC-R4).

§7.3 의 prop[ind] 비대칭 round-trip 한계를 graph-diff(raw asserted vs as_rdflib_graph post)로 해소.
검증 (inferred.jsonl 레벨):
  R-chain      a uses b, b requires c + (uses∘requires⊑depends_on) → a depends_on c (멀티홉, AC-R4)
  R-transitive x ipo y, y ipo z + Transitive(ipo)           → x ipo z (AC-R3)
  R-inverse    m member_of grp + inverseOf(member_of,has_member) → grp has_member m (AC-R3)
  R-clean      asserted fact(a uses b)는 inferred_properties 에 없음 (false-positive 0)
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
import reason  # noqa: E402
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


def _declare(target, label, ev):
    rbox.cmd_add_relation(_ns(target=str(target), domain=DOMAIN, label=label, alt=[],
                              description=None, evidence=[f"e:{ev}"], status="accepted", apply=True))


def _prop(target, role, **kw):
    axiom.cmd_property(_ns(target=str(target), domain=DOMAIN, role=role,
                           characteristic=kw.get("characteristic"), inverse=kw.get("inverse"),
                           subproperty_of=kw.get("subproperty_of"), chain=kw.get("chain"),
                           domain_class=None, range=None, show_inferences=False, apply=True))


def _abox(owl_dir):
    """ABox by hand: NamedIndividual + object-property assertions (동일 ns)."""
    g = rdflib.Graph()
    U = lambda n: rdflib.URIRef(NS + n)  # noqa: E731
    inds = ["a", "b", "c", "x", "y", "z", "m", "grp"]
    for i in inds:
        g.add((U(i), rdflib.RDF.type, OWL.NamedIndividual))
    g.add((U("a"), U("uses"), U("b")))
    g.add((U("b"), U("requires"), U("c")))
    g.add((U("x"), U("is_part_of"), U("y")))
    g.add((U("y"), U("is_part_of"), U("z")))
    g.add((U("m"), U("member_of"), U("grp")))
    g.serialize(destination=str(owl_dir / "demo.abox.ttl"), format="turtle")


def _inferred_props(inferred_path):
    """{ind_name: {prop: [vals]}} from inferred.jsonl."""
    out = {}
    for line in inferred_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            if rec.get("inferred_properties"):
                out[rec["id"]] = rec["inferred_properties"]
    return out


def main() -> int:
    import warnings
    warnings.filterwarnings("ignore")
    passed = True
    tmp = Path(tempfile.mkdtemp(prefix="rbox_reason_"))
    target = tmp / "kb"

    for lbl, ev in [("uses", "1"), ("requires", "2"), ("depends on", "3"),
                    ("is part of", "4"), ("member of", "5"), ("has member", "6")]:
        _declare(target, lbl, ev)
    _prop(target, "depends_on", chain=["uses", "requires"])
    _prop(target, "is_part_of", characteristic="Transitive")
    _prop(target, "member_of", inverse="has_member")

    rbox.cmd_compile(_ns(target=str(target), domain=DOMAIN, out_dir=None,
                         no_postprocess=False, apply=True))
    owl_dir = target / "ontology" / "owl"
    _abox(owl_dir)

    # reason (실제 코드패스) — argv 교체
    orig = sys.argv[:]
    sys.argv = ["reason", "--target", str(target), "--apply"]
    try:
        reason.main()
    except SystemExit as e:
        if e.code not in (0, None):
            print(f"[FAIL] reason exit {e.code}")
            return 1
    finally:
        sys.argv = orig

    inferred = owl_dir.parent / "Abox" / "_inferred" / "inferred.jsonl"
    if not _ok(inferred.exists(), "inferred.jsonl 생성"):
        return 1
    props = _inferred_props(inferred)
    print(f"  inferred_properties = {json.dumps(props, ensure_ascii=False)}")

    passed &= _ok(props.get("a", {}).get("depends_on") == ["c"],
                  "R-chain 멀티홉: a depends_on c (AC-R4)")
    passed &= _ok("z" in props.get("x", {}).get("is_part_of", []),
                  "R-transitive: x is_part_of z (AC-R3)")
    passed &= _ok("m" in props.get("grp", {}).get("has_member", []),
                  "R-inverse: grp has_member m (AC-R3)")
    # false-positive: asserted a uses b 가 inferred 로 새지 않음
    a_props = props.get("a", {})
    passed &= _ok("b" not in a_props.get("uses", []),
                  "R-clean: asserted fact 누수 0 (a uses b ∉ inferred)")

    print()
    print("RBOX P3 REASON TESTS PASS" if passed else "RBOX P3 REASON TESTS **FAIL**")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
