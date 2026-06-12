#!/usr/bin/env python3
"""msm-ontology abox-compile — ABox 인스턴스(RDF)를 OWL individual TTL 로 컴파일.

배경 (main PRD §5 / RDF=LLM·OWL=HITL 분업):
  owlgen 은 TBox(클래스/슬롯)만 OWL 로 낸다. ABox 인스턴스(individual + property
  assertion)는 별도 컴파일이 필요하다. 이 인스턴스 사실(RDF)은 evidence/LLM 파싱으로
  채워지는 **자동화 가능한 층**이고, TBox 공리(OWL)는 사람이 대화로 만드는 층이다.

입력 (LinkML-native ABox YAML, 예 ontology/Abox/{domain}.yaml):
    instances:
      gemma4_e4b:
        instance_of: TransformerMLMModel
        canBeUsedFor: [image_generation]     # object property assertion
      image_generation:
        instance_of: ImageGeneration

출력 (ontology/owl/{domain}.abox.ttl):
    :gemma4_e4b a owl:NamedIndividual, :TransformerMLMModel ; :canBeUsedFor :image_generation .
    :image_generation a owl:NamedIndividual, :ImageGeneration .

핵심:
  - **owl:NamedIndividual 명시**: owlready2 의 .individuals() 는 NamedIndividual 만 센다.
  - **네임스페이스 = TBox 와 동일**해야 함(아니면 추론 안 됨). TBox definition YAML 의
    default_prefix URI 를 base 로 사용. ABox YAML 이 자체 prefixes 를 가지면 그걸 우선.
  - reason 이 out-dir 의 *.ttl 을 전부 병합하므로 {domain}.abox.ttl 은 자동 합류.

Usage:
  msm-ontology abox-compile --target REPO [--domain NAME] [--out-dir DIR] [--apply]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TOOL_VERSION = "msm-ontology/0.13.0"
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")  # bare 식별자 → object IRI


def _log(msg: str, level: str = "info") -> None:
    prefix = {"info": "[*]", "ok": "[+]", "warn": "[!]", "err": "[x]"}[level]
    print(f"{prefix} {msg}", file=sys.stderr, flush=True)


def _load_yaml(path: Path) -> dict:
    import yaml
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _namespace_for(abox_doc: dict, def_yaml: Path | None) -> str | None:
    """ABox YAML 자체 prefixes 우선, 없으면 같은 stem 의 definition YAML 에서 도출."""
    def _extract(doc: dict) -> str | None:
        dp = doc.get("default_prefix")
        prefixes = doc.get("prefixes") or {}
        if dp and dp in prefixes:
            val = prefixes[dp]
            # LinkML prefixes 는 str 또는 {prefix_reference: URI}
            return val if isinstance(val, str) else val.get("prefix_reference")
        return None

    ns = _extract(abox_doc)
    if ns:
        return ns
    if def_yaml and def_yaml.exists():
        return _extract(_load_yaml(def_yaml))
    return None


def _compile_abox(abox_path: Path, def_dir: Path, owl_dir: Path, apply: bool) -> bool:
    try:
        from rdflib import Graph, Namespace, Literal
        from rdflib.namespace import RDF, OWL
    except ImportError:
        _log("rdflib 필요: pip install rdflib", "err")
        sys.exit(1)

    doc = _load_yaml(abox_path)
    instances = doc.get("instances") or {}
    if not instances:
        _log(f"{abox_path.name}: instances 없음 — 건너뜀", "warn")
        return False

    def_yaml = def_dir / f"{abox_path.stem}.yaml"
    ns_uri = _namespace_for(doc, def_yaml)
    if not ns_uri:
        _log(f"{abox_path.name}: 네임스페이스를 찾을 수 없음 "
             f"(ABox YAML 에 prefixes/default_prefix 추가하거나 "
             f"definition/{abox_path.stem}.yaml 작성)", "err")
        return False

    NS = Namespace(ns_uri)
    g = Graph()
    g.bind("", NS)

    n_ind = 0
    n_assert = 0
    for inst_id, body in instances.items():
        body = body or {}
        subj = NS[str(inst_id)]
        g.add((subj, RDF.type, OWL.NamedIndividual))
        cls = body.get("instance_of")
        if cls:
            g.add((subj, RDF.type, NS[str(cls)]))
        n_ind += 1
        for slot, val in body.items():
            if slot == "instance_of":
                continue
            values = val if isinstance(val, list) else [val]
            for v in values:
                if isinstance(v, bool) or isinstance(v, (int, float)):
                    g.add((subj, NS[slot], Literal(v)))
                elif isinstance(v, str) and _IDENT_RE.match(v):
                    g.add((subj, NS[slot], NS[v]))        # object property → individual IRI
                else:
                    g.add((subj, NS[slot], Literal(v)))   # data property
                n_assert += 1

    out_path = owl_dir / f"{abox_path.stem}.abox.ttl"
    if apply:
        owl_dir.mkdir(parents=True, exist_ok=True)
        g.serialize(destination=str(out_path), format="turtle")
        _log(f"abox-compile {abox_path.name} → {out_path.name} "
             f"({n_ind} individual / {n_assert} assertion)", "ok")
    else:
        _log(f"[dry] {abox_path.name} → {out_path.name} "
             f"({n_ind} individual / {n_assert} assertion)")
        preview = [l for l in g.serialize(format="turtle").splitlines() if l.strip()][:8]
        for line in preview:
            print(f"      {line}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ABox 인스턴스(LinkML-native YAML) → OWL individual TTL"
    )
    parser.add_argument("--target", required=True, help="KB 루트 경로")
    parser.add_argument("--domain", default=None, help="특정 도메인만 (기본: 전체)")
    parser.add_argument("--out-dir", default=None,
                        help="TTL 출력 디렉토리 (기본: <target>/ontology/owl)")
    parser.add_argument("--apply", action="store_true", help="실제 파일 쓰기 (기본: dry-run)")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    abox_dir = target / "ontology" / "Abox"
    def_dir = target / "ontology" / "definition"
    if args.out_dir:
        _p = Path(args.out_dir)
        owl_dir = _p if _p.is_absolute() else (target / _p)
    else:
        owl_dir = target / "ontology" / "owl"

    if not abox_dir.exists():
        _log(f"ABox 디렉토리 없음: {abox_dir}", "err")
        sys.exit(1)

    if args.domain:
        abox_files = [abox_dir / f"{args.domain}.yaml"]
        if not abox_files[0].exists():
            _log(f"파일 없음: {abox_files[0]}", "err")
            sys.exit(1)
    else:
        abox_files = sorted(abox_dir.glob("*.yaml"))
        if not abox_files:
            _log(f"ABox YAML 없음: {abox_dir}/*.yaml", "warn")
            sys.exit(0)

    mode = "apply" if args.apply else "dry-run"
    _log(f"abox-compile [{mode}] — {len(abox_files)}개 파일 → {owl_dir}")
    ok = sum(_compile_abox(f, def_dir, owl_dir, args.apply) for f in abox_files)
    _log(f"완료: {ok}/{len(abox_files)}개 컴파일")
    sys.exit(0)


if __name__ == "__main__":
    main()
