#!/usr/bin/env python3
"""owl_postprocess + compile 통합 테스트 (addendum PRD §6 AC-A1/A2/A3).

검증:
  AC-A2  annotations.label_<lang> → rdfs:label@lang, annotations.owl_characteristic → owl:...Property
  AC-A3  compile --no-postprocess 산출 = base owlgen (트리플 동형)
  AC-A1  compile(+postprocess) 결과에 FunctionalProperty + @ko label 무손실
  idempotency  postprocess 재실행 시 변경 0

요구: pip install linkml rdflib  (없으면 skip)
실행: python3 tests/test_owl_postprocess.py
"""
from __future__ import annotations

import sys
import tempfile
import shutil
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "wftest.yaml"
sys.path.insert(0, str(SCRIPTS))


def _need(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except ImportError:
        return False


def main() -> int:
    if not _need("rdflib"):
        print("SKIP: rdflib 미설치")
        return 0
    if not _need("linkml"):
        print("SKIP: linkml 미설치 (pip install linkml)")
        return 0

    import warnings
    warnings.filterwarnings("ignore")
    from rdflib import Graph
    from rdflib.namespace import RDF, RDFS, OWL
    from rdflib.compare import to_isomorphic
    import compile as C
    import owl_postprocess as PP

    tmp = Path(tempfile.mkdtemp(prefix="msm_onto_test_"))
    try:
        defdir = tmp / "ontology" / "definition"
        defdir.mkdir(parents=True)
        shutil.copy(FIXTURE, defdir / "wftest.yaml")
        owldir = tmp / "ontology" / "owl"

        # --- AC-A3: --no-postprocess == base owlgen ---
        C._compile_yaml(defdir / "wftest.yaml", owldir, apply=True, postprocess=False)
        from linkml.generators.owlgen import OwlSchemaGenerator
        raw = OwlSchemaGenerator(str(defdir / "wftest.yaml"), use_native_uris=False).serialize()
        g_raw = Graph(); g_raw.parse(data=raw, format="turtle")
        g_base = Graph(); g_base.parse(str(owldir / "wftest.ttl"), format="turtle")
        assert to_isomorphic(g_raw) == to_isomorphic(g_base), "AC-A3 FAIL: --no-postprocess != base"
        print("[AC-A3] --no-postprocess == base owlgen (isomorphic) OK")

        # --- AC-A1/A2: compile + postprocess ---
        shutil.rmtree(owldir, ignore_errors=True)
        C._compile_yaml(defdir / "wftest.yaml", owldir, apply=True, postprocess=True)
        g = Graph(); g.parse(str(owldir / "wftest.ttl"), format="turtle")

        classes = set(g.subjects(RDF.type, OWL.Class))
        objprops = set(g.subjects(RDF.type, OWL.ObjectProperty))
        func = set(g.subjects(RDF.type, OWL.FunctionalProperty))
        sym = set(g.subjects(RDF.type, OWL.SymmetricProperty))
        ko = [o for o in g.objects(None, RDFS.label) if getattr(o, "language", None) == "ko"]
        carriers = [(s, p, o) for s, p, o in g
                    if str(p).rsplit("/", 1)[-1] == "owl_characteristic"
                    or str(p).rsplit("/", 1)[-1].startswith("label_")]

        assert len(classes) == 3, f"classes={len(classes)}"
        assert len(objprops) == 2, f"objprops={len(objprops)}"
        assert len(func) == 1, f"FunctionalProperty={len(func)}"
        assert len(sym) == 1, f"SymmetricProperty={len(sym)}"
        assert len(ko) == 2, f"@ko labels={len(ko)}"
        assert len(carriers) == 0, f"carriers 잔존={len(carriers)}"

        # 무손실(losslessness): carrier 외 base 트리플은 전부 post 에 보존되어야 한다 (AC-A1)
        def _is_carrier(t):
            ln = str(t[1]).rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            return ln == "owl_characteristic" or ln.startswith("label_")
        base_non_carrier = {t for t in g_base if not _is_carrier(t)}
        lost = base_non_carrier - set(g)
        assert not lost, f"AC-A1 FAIL: base 트리플 {len(lost)}개 소실: {list(lost)[:3]}"
        print(f"[AC-A1] base 비-carrier 트리플 {len(base_non_carrier)}개 전부 보존 (소실 0) OK")
        print(f"[AC-A2] 3 class / 2 objprop / 1 Functional / 1 Symmetric / 2 @ko / 0 carrier OK")

        # --- idempotency ---
        changed = PP.postprocess_ttl(owldir / "wftest.ttl", apply=True, keep_carriers=False)
        assert changed is False, "idempotency FAIL: 재실행에 변경 발생"
        print("[idempotency] postprocess 재실행 변경 없음 OK")

        print("\nALL ONTOLOGY POSTPROCESS TESTS PASS")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
