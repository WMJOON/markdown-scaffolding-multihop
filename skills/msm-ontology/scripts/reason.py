#!/usr/bin/env python3
"""msm-ontology reason — OWL2 DL reasoning 실행 후 inferred facts를 JSONL에 역주입.

Usage: msm-ontology reason --target REPO [--out-dir DIR] [--inferred-dir DIR] [--apply]

핵심 (v0.13.0 + ABox 추론):
  - out-dir 내 **모든 TTL(TBox + ABox)을 하나의 그래프로 병합**해 함께 추론한다.
    (TBox 공리와 ABox individual 이 같은 그래프에 있어야 reclassification 이 동작)
  - reason 전 asserted 타입을 스냅샷하고, reason 후 타입과 **diff** 해 inferred-only
    (gained) 타입만 골라낸다 → 소비자가 "추론이 무엇을 더했는지" 구분 가능.

의존성:
  pip install owlready2 rdflib  +  Java 런타임(Pellet/HermiT) — java -version 으로 확인

추론 결과 저장 경로 (기본): ontology/Abox/_inferred/inferred.jsonl
  (기존 instances.jsonl 은 수정하지 않음)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

TOOL_VERSION = "msm-ontology/0.13.0"
INFERRED_FILE = "inferred.jsonl"


def _log(msg: str, level: str = "info") -> None:
    prefix = {"info": "[*]", "ok": "[+]", "warn": "[!]", "err": "[x]"}[level]
    print(f"{prefix} {msg}", file=sys.stderr, flush=True)


def _load_owlready2():
    try:
        import owlready2
        return owlready2
    except ImportError:
        _log("owlready2 not installed. Run: pip install owlready2", "err")
        sys.exit(1)


def _run_reasoner(owlready2, onto):
    """Pellet → HermiT 순으로 fallback."""
    try:
        with onto:
            owlready2.sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=False)
        return "pellet"
    except Exception as e:
        _log(f"Pellet 실패 ({e}), HermiT 시도...", "warn")

    try:
        with onto:
            owlready2.sync_reasoner_hermit()
        return "hermit"
    except Exception as e:
        _log(f"HermiT 실패 ({e})", "err")
        _log("Java가 설치돼 있는지 확인하세요: java -version", "err")
        raise


def _merge_ttls_to_graph(ttl_files: list[Path]):
    """모든 TTL(TBox+RBox+ABox)을 하나의 rdflib Graph 로 병합해 반환 (asserted baseline).

    이 그래프가 graph-diff 추론 캡처의 pre(asserted) 기준이다 (P3, SPEC §3.1).
    """
    try:
        import rdflib
    except ImportError:
        _log("rdflib 필요: pip install rdflib", "err")
        return None
    g = rdflib.Graph()
    for ttl in ttl_files:
        try:
            g.parse(str(ttl), format="turtle")
        except Exception as e:  # noqa: BLE001
            _log(f"TTL 파싱 실패 {ttl.name}: {e}", "err")
            return None
    return g


def _graph_to_nt(g) -> Path:
    """rdflib Graph → 단일 NTriples temp (owlready2 는 Turtle 직접 파싱 불가)."""
    fd, nt_name = tempfile.mkstemp(suffix=".nt", prefix="msm_merged_")
    os.close(fd)
    nt_path = Path(nt_name)
    g.serialize(destination=str(nt_path), format="nt", encoding="utf-8")
    return nt_path


def _type_names(owlready2, ind) -> set:
    """individual 의 명시/추론 클래스 이름 집합 (owl:Thing 제외)."""
    return {
        c.name for c in ind.is_a
        if isinstance(c, owlready2.ThingClass) and c is not owlready2.Thing
    }


def _snapshot_types(owlready2, onto) -> dict:
    """reason 전 asserted 타입 스냅샷 {iri: set(type names)} (type 재분류는 owlready2 객체모델이 견고)."""
    return {ind.iri: _type_names(owlready2, ind) for ind in onto.individuals()}


def _local(iri) -> str:
    s = str(iri)
    s = s.rsplit("#", 1)[-1]
    return s.rsplit("/", 1)[-1]


def _obj_property_facts(g, ind_set: set, objprop_set: set) -> dict:
    """그래프에서 (s∈Ind ∧ p∈ObjProp ∧ o∈Ind) object-property fact 만 추출 → {s_iri: {p_local: set(o_local)}}.

    (P3 graph-diff 필터, SPEC §3.1 / PRD §14 Q1: 노이즈 제거 — rdf:type/owl·rdfs·skos·linkml
     /restriction bnode 는 o∈Ind 조건이 떨군다.)
    """
    out: dict = {}
    for s, p, o in g:
        if s in ind_set and p in objprop_set and o in ind_set:
            out.setdefault(str(s), {}).setdefault(_local(p), set()).add(_local(o))
    return out


def _abox_individuals_and_objprops(g):
    """asserted 그래프에서 안정적인 Individual / ObjectProperty IRI 집합 (필터 기준)."""
    import rdflib
    OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")
    inds = set(g.subjects(rdflib.RDF.type, OWL.NamedIndividual))
    objprops = set(g.subjects(rdflib.RDF.type, OWL.ObjectProperty))
    return inds, objprops


def _extract_inferred(owlready2, onto, pre_types: dict, raw_graph, source_label: str) -> list[dict]:
    """type 은 owlready2 객체모델 diff(견고), property 는 **graph-diff**(P3) 로 추출.

    - type 재분류: reason 후 _type_names − pre_types  (AC-R5 불변, 기존 경로 유지)
    - property 추론(chain/transitive/inverse): post(as_rdflib_graph) − raw(asserted),
      (Ind,ObjProp,Ind) 필터.  §7.3 의 prop[ind] 비대칭 round-trip 한계를 quadstore 직독으로 해소.
    """
    import rdflib  # noqa: F401
    ind_set, objprop_set = _abox_individuals_and_objprops(raw_graph)
    pre_obj = _obj_property_facts(raw_graph, ind_set, objprop_set)
    post_graph = onto.world.as_rdflib_graph()
    post_obj = _obj_property_facts(post_graph, ind_set, objprop_set)

    records: list[dict] = []
    for ind in onto.individuals():
        iri = ind.iri
        asserted = pre_types.get(iri, set())
        gained_types = _type_names(owlready2, ind) - asserted

        gained_props: dict = {}
        post_p = post_obj.get(iri, {})
        pre_p = pre_obj.get(iri, {})
        for p, vals in post_p.items():
            delta = vals - pre_p.get(p, set())
            if delta:
                gained_props[p] = sorted(delta)

        if not gained_types and not gained_props:
            continue
        records.append({
            "id": ind.name,
            "iri": iri,
            "asserted_types": sorted(asserted),
            "inferred_types": sorted(gained_types),         # 재분류 delta (subClassOf/GCI)
            "all_types": sorted(asserted | gained_types),    # asserted ∪ inferred
            "inferred_properties": gained_props,             # graph-diff delta (chain/transitive/inverse)
            "inferred": True,
            "source_ontology": source_label,
            "tool_version": TOOL_VERSION,
        })
    return records


def _write_inferred(inferred_dir: Path, records: list[dict], apply: bool) -> None:
    if not records:
        _log("추론된 fact 없음.")
        return

    out_path = inferred_dir / INFERRED_FILE
    if apply:
        inferred_dir.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        _log(f"{len(records)}개 inferred fact → {out_path}", "ok")
    else:
        _log(f"[dry] {len(records)}개 inferred fact (--apply 없이는 쓰기 안 함)")
        for r in records[:5]:
            print(f"      {json.dumps(r, ensure_ascii=False)}")
        if len(records) > 5:
            print(f"      ... ({len(records) - 5}개 더)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OWL2 DL reasoning → inferred facts JSONL 역주입 (TBox+ABox 병합 추론)"
    )
    parser.add_argument("--target", required=True, help="KB 루트 경로")
    parser.add_argument("--out-dir", default=None,
                        help="TTL 입력 디렉토리 (기본: <target>/ontology/owl)")
    parser.add_argument("--inferred-dir", default=None,
                        help="inferred.jsonl 출력 디렉토리 (기본: <target>/ontology/Abox/_inferred)")
    parser.add_argument("--apply", action="store_true", help="실제 파일 쓰기 (기본: dry-run)")
    args = parser.parse_args()

    target = Path(args.target).resolve()

    def _resolve(opt, default_rel):
        if opt:
            p = Path(opt)
            return p if p.is_absolute() else (target / p)
        return target.joinpath(*default_rel)

    owl_dir = _resolve(args.out_dir, ("ontology", "owl"))
    inferred_dir = _resolve(args.inferred_dir, ("ontology", "Abox", "_inferred"))

    if not owl_dir.exists():
        _log(f"TTL 디렉토리 없음: {owl_dir} — compile을 먼저 실행하세요.", "err")
        sys.exit(1)

    ttl_files = sorted(owl_dir.glob("*.ttl"))
    if not ttl_files:
        _log("Turtle 파일 없음 — 'msm-ontology compile --target ...' 실행 후 다시 시도하세요.", "warn")
        sys.exit(1)

    owlready2 = _load_owlready2()
    mode = "apply" if args.apply else "dry-run"
    _log(f"reason [{mode}] — {len(ttl_files)}개 TTL 병합 추론 @ {owl_dir}")

    raw_graph = _merge_ttls_to_graph(ttl_files)   # asserted baseline (graph-diff pre)
    if raw_graph is None:
        sys.exit(1)
    nt_path = _graph_to_nt(raw_graph)
    try:
        onto = owlready2.get_ontology(f"file://{nt_path.resolve()}").load()
    except Exception as e:  # noqa: BLE001
        _log(f"온톨로지 로드 실패: {e}", "err")
        sys.exit(1)
    finally:
        try:
            nt_path.unlink()
        except OSError:
            pass

    # reason 전 asserted 타입 스냅샷 (property 는 graph-diff 로 raw_graph vs post 비교)
    pre_types = _snapshot_types(owlready2, onto)
    n_individuals = len(pre_types)

    try:
        reasoner = _run_reasoner(owlready2, onto)
        _log(f"추론 완료 ({reasoner}) — individual {n_individuals}개")
    except Exception:
        sys.exit(1)

    source_label = ",".join(f.name for f in ttl_files)
    records = _extract_inferred(owlready2, onto, pre_types, raw_graph, source_label)
    _write_inferred(inferred_dir, records, args.apply)
    _log(f"총 {len(records)}개 inferred fact / {n_individuals}개 individual")


if __name__ == "__main__":
    main()
