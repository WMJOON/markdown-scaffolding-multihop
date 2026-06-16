#!/usr/bin/env python
"""msm-ontology rbox — RBox(role / object-property) first-class layer.

SPEC: planning/msm-ontology_v0.13.0/msm-ontology_v0.13.0-RBox-firstclass-SPEC.md

서브명령:
  add-relation : role 선언 (LLM/evidence 제안, status=draft). **추론 0 → 안전**.
  list         : 선언된 role + status 조회.
  compile      : Rbox/roles/{domain}.yaml → owl/{domain}.rbox.ttl (+owl_postprocess).

role 정본: {target}/ontology/Rbox/roles/{domain}.yaml — LinkML schema (ruamel 라운드트립).
각 role = LinkML slot. 선언부(description/aliases/status/source_refs annotations)만 add-relation 이 쓴다.
공리부(owl_characteristic/subproperty_of/property_chain/domain/range)는 `axiom property`(P2)가 주입.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ex prefix base. RBox role IRI 는 도메인 TBox 와 **동일 네임스페이스**여야 reason 병합이 동작한다
# (core.md §7.3). 기존 definition/{domain}.yaml 의 ex prefix 가 있으면 그것을 재사용한다.
DEFAULT_NS_BASE = "https://example.org/msm"  # → ex: {base}/{domain}/


def _log(msg: str, level: str = "info") -> None:
    icon = {"info": "[*]", "ok": "[+]", "warn": "[!]", "err": "[x]"}.get(level, "[*]")
    print(f"{icon} {msg}", file=sys.stderr)


def _snake(label: str) -> str:
    s = re.sub(r"[^\w\s]", "", label.strip())
    s = re.sub(r"[\s\-]+", "_", s)
    return s.lower()


def _roles_path(target: Path, domain: str) -> Path:
    return target / "ontology" / "Rbox" / "roles" / f"{domain}.yaml"


def _yamlrt():
    from ruamel.yaml import YAML
    y = YAML()
    y.preserve_quotes = True
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def _resolve_ex_prefix(target: Path, domain: str) -> str:
    """도메인 TBox definition 의 ex prefix 를 재사용(네임스페이스 정렬). 없으면 기본 컨벤션."""
    for cand in (target / "ontology" / "definition" / f"{domain}.yaml",
                 target / "definition" / f"{domain}.yaml"):
        if cand.exists():
            try:
                from ruamel.yaml import YAML
                d = YAML().load(cand.read_text(encoding="utf-8")) or {}
                pref = (d.get("prefixes") or {}).get("ex")
                if pref:
                    return str(pref)
            except Exception:  # noqa: BLE001
                pass
    return f"{DEFAULT_NS_BASE}/{domain}/"


def _skeleton(domain: str, ex_prefix: str):
    """신규 roles YAML 스켈레톤 (LinkML). Thing = role domain/range anchor용 carrier class."""
    from ruamel.yaml.comments import CommentedMap
    doc = CommentedMap()
    doc["id"] = f"{DEFAULT_NS_BASE}/rbox/{domain}"
    doc["name"] = f"{domain}-rbox"
    doc["description"] = f"RBox role layer for domain '{domain}' (msm-ontology, first-class)"
    prefixes = CommentedMap()
    prefixes["linkml"] = "https://w3id.org/linkml/"
    prefixes["ex"] = ex_prefix
    prefixes["skos"] = "http://www.w3.org/2004/02/skos/core#"
    doc["prefixes"] = prefixes
    doc["default_prefix"] = "ex"
    doc["default_range"] = "string"
    doc["imports"] = ["linkml:types"]
    classes = CommentedMap()
    thing = CommentedMap()
    thing["class_uri"] = "ex:Thing"
    thing["description"] = "Generic role anchor (domain/range carrier)."
    classes["Thing"] = thing
    doc["classes"] = classes
    doc["slots"] = CommentedMap()
    return doc


def _load_or_init(path: Path, domain: str, target: Path):
    y = _yamlrt()
    if path.exists():
        with path.open(encoding="utf-8") as f:
            return y, y.load(f)
    return y, _skeleton(domain, _resolve_ex_prefix(target, domain))


# ─────────────────────────────────────────────────────── add-relation

def cmd_add_relation(args) -> int:
    target = Path(args.target)
    domain = args.domain
    if not args.evidence:
        _log("source_refs_missing: --evidence 1개 이상 필수 (선언도 evidence 강제)", "err")
        return 1

    label = args.label
    name = _snake(label)
    path = _roles_path(target, domain)
    y, doc = _load_or_init(path, domain, target)

    slots = doc.setdefault("slots", {})
    if name in slots:
        _log(f"role '{name}' 이미 존재 — 중복 선언 거부 (변경은 axiom property)", "err")
        return 1

    from ruamel.yaml.comments import CommentedMap
    slot = CommentedMap()
    if args.description:
        slot["description"] = args.description
    if args.alt:
        slot["aliases"] = list(args.alt)
    ann = CommentedMap()
    ann["status"] = args.status
    ann["source_refs"] = ",".join(args.evidence)
    slot["annotations"] = ann
    slots[name] = slot

    if not args.apply:
        _log(f"[dry] would declare role '{name}' (status={args.status}) in {path}")
        print(f'  slots.{name}: status={args.status}, evidence={len(args.evidence)}')
        _log("[dry] --apply 후 기록. 공리부(chain/characteristic)는 axiom property 로 별도 저작.")
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        y.dump(doc, f)
    _log(f"role_declared: {name} (status={args.status}) → {path}", "ok")
    return 0


# ─────────────────────────────────────────────────────── list

def cmd_list(args) -> int:
    path = _roles_path(Path(args.target), args.domain)
    if not path.exists():
        _log(f"roles 파일 없음: {path}", "warn")
        return 0
    y = _yamlrt()
    with path.open(encoding="utf-8") as f:
        doc = y.load(f)
    slots = doc.get("slots") or {}
    rows = []
    for name, body in slots.items():
        body = body or {}
        ann = (body.get("annotations") or {})
        status = ann.get("status", "?")
        # 모든 RBox 공리는 annotation 단일 경로 (axiom property → owl_postprocess). native 키 스캔 불필요.
        axioms = [k for k in ("owl_characteristic", "inverse_of", "subproperty_of", "property_chain")
                  if k in ann]
        rows.append((name, status, "axiomatized" if axioms else "declared-only", ",".join(axioms)))
    if args.status:
        rows = [r for r in rows if r[1] == args.status]
    print(f"# RBox roles — domain={args.domain}  ({len(rows)})")
    for name, status, tier, ax in rows:
        print(f"  {name:24s} [{status:9s}] {tier}" + (f"  <{ax}>" if ax else ""))
    return 0


# ─────────────────────────────────────────────────────── validate

def cmd_validate(args) -> int:
    """RBox 정합 게이트 (AC-R7):
      G1 gate    — Abox 에서 쓰는 object-property 술어가 모두 roles/ 에 선언돼 있는가
      G2 status  — Abox 에서 쓰는 role 이 accepted+ 인가 (draft 면 warn)
      G3 mece    — role 간 normalized label 중복 / alias↔label 충돌
    violation ≥ 1 → exit 1.
    """
    target = Path(args.target)
    domain = args.domain
    path = _roles_path(target, domain)
    if not path.exists():
        _log(f"roles 파일 없음: {path}", "err")
        return 1
    y = _yamlrt()
    with path.open(encoding="utf-8") as f:
        doc = y.load(f)
    slots = doc.get("slots") or {}
    declared = set(slots.keys())
    status_of = {n: ((slots[n] or {}).get("annotations") or {}).get("status", "?") for n in declared}

    violations: list[str] = []
    warns: list[str] = []

    # G3 MECE — label 중복 / alias 충돌
    seen_norm: dict = {}
    for name, body in slots.items():
        body = body or {}
        if name in seen_norm:
            violations.append(f"label_duplicate: '{name}' 중복")
        seen_norm[name] = True
        for alias in (body.get("aliases") or []):
            an = _snake(alias)
            if an in declared and an != name:
                violations.append(f"alias_collision: '{name}' 의 alias '{alias}'가 다른 role '{an}' 과 충돌")

    # G1/G2 — Abox object-property 술어 정합
    owl_dir = target / "ontology" / "owl"
    abox_ttls = sorted(owl_dir.glob("*.abox.ttl")) if owl_dir.exists() else []
    used_preds: set = set()
    if abox_ttls:
        import rdflib
        OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")
        g = rdflib.Graph()
        for t in abox_ttls:
            g.parse(str(t), format="turtle")
        inds = set(g.subjects(rdflib.RDF.type, OWL.NamedIndividual))
        for s, p, o in g:
            if s in inds and o in inds:
                used_preds.add(str(p).rsplit("#", 1)[-1].rsplit("/", 1)[-1])
        for pred in sorted(used_preds):
            if pred not in declared:
                violations.append(f"undeclared_role: Abox 술어 '{pred}' 미선언 (rbox add-relation 필요)")
            elif status_of.get(pred) not in ("accepted", "stable"):
                warns.append(f"draft_role_in_use: Abox 술어 '{pred}' status={status_of.get(pred)} (accepted 권장)")
    else:
        warns.append("Abox TTL 없음 (owl/*.abox.ttl) — gate G1/G2 생략 (abox-compile 후 재검증)")

    for w in warns:
        _log(w, "warn")
    for v in violations:
        _log(v, "err")
    print(f"# RBox validate — domain={domain}: roles={len(declared)}, abox_preds={len(used_preds)}, "
          f"violations={len(violations)}, warnings={len(warns)}")
    if violations:
        _log(f"validation_failed: {len(violations)} violation(s)", "err")
        return 1
    _log("validate OK", "ok")
    return 0


# ─────────────────────────────────────────────────────── compile

def cmd_compile(args) -> int:
    target = Path(args.target)
    domains = [args.domain] if args.domain else _all_domains(target)
    if not domains:
        _log("컴파일할 roles 도메인 없음", "warn")
        return 0
    owl_dir = Path(args.out_dir) if args.out_dir else target / "ontology" / "owl"
    rc = 0
    for domain in domains:
        rc |= _compile_one(target, domain, owl_dir, args.apply, not args.no_postprocess)
    return rc


def _all_domains(target: Path) -> list[str]:
    rdir = target / "ontology" / "Rbox" / "roles"
    if not rdir.exists():
        return []
    return sorted(p.stem for p in rdir.glob("*.yaml"))


def _compile_one(target: Path, domain: str, owl_dir: Path, apply: bool, postprocess: bool) -> int:
    src = _roles_path(target, domain)
    if not src.exists():
        _log(f"roles 파일 없음: {src}", "err")
        return 1
    try:
        from linkml.generators.owlgen import OwlSchemaGenerator
    except ImportError:
        _log("linkml not installed. Run: pip install linkml", "err")
        return 1
    import warnings
    warnings.filterwarnings("ignore")
    try:
        ttl = OwlSchemaGenerator(str(src), use_native_uris=False).serialize()
    except Exception as e:  # noqa: BLE001
        _log(f"rbox compile 실패 ({domain}): {e}", "err")
        return 1

    out_path = owl_dir / f"{domain}.rbox.ttl"
    if apply:
        owl_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_text(ttl, encoding="utf-8")
        _log(f"compiled {src.name} → {out_path.name}", "ok")
        if postprocess:
            _run_postprocess(out_path)
    else:
        _log(f"[dry] would write {out_path}")
        for line in [l for l in ttl.splitlines() if "ObjectProperty" in l][:5]:
            print(f"      {line.strip()}")
    return 0


def _run_postprocess(ttl_path: Path) -> None:
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import owl_postprocess as pp  # type: ignore
    except Exception as e:  # noqa: BLE001
        _log(f"owl_postprocess 로드 실패 — 후처리 생략 ({e})", "warn")
        return
    fn = getattr(pp, "postprocess_ttl", None)
    if fn is None:
        _log("owl_postprocess.postprocess_ttl 미발견 — 후처리 생략", "warn")
        return
    try:
        fn(ttl_path, apply=True, keep_carriers=False)
    except Exception as e:  # noqa: BLE001
        _log(f"owl_postprocess 실행 실패 ({e})", "warn")


# ─────────────────────────────────────────────────────── argparse

def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="rbox")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add-relation", help="role 선언 (LLM/evidence, status=draft)")
    a.add_argument("--target", required=True)
    a.add_argument("--domain", required=True)
    a.add_argument("--label", required=True)
    a.add_argument("--alt", nargs="*", default=[], help="동의어 (→ aliases/skos:altLabel)")
    a.add_argument("--description", default=None)
    a.add_argument("--evidence", nargs="+", default=[], help="source_refs (1개 이상 필수)")
    a.add_argument("--status", default="draft", choices=["draft", "accepted", "stable"])
    a.add_argument("--apply", action="store_true")
    a.set_defaults(func=cmd_add_relation)

    l = sub.add_parser("list", help="선언된 role 조회")
    l.add_argument("--target", required=True)
    l.add_argument("--domain", required=True)
    l.add_argument("--status", default=None)
    l.set_defaults(func=cmd_list)

    c = sub.add_parser("compile", help="roles YAML → {domain}.rbox.ttl")
    c.add_argument("--target", required=True)
    c.add_argument("--domain", default=None)
    c.add_argument("--out-dir", default=None)
    c.add_argument("--no-postprocess", action="store_true")
    c.add_argument("--apply", action="store_true")
    c.set_defaults(func=cmd_compile)

    v = sub.add_parser("validate", help="RBox 정합 게이트 (Abox 술어 ↔ roles ↔ MECE)")
    v.add_argument("--target", required=True)
    v.add_argument("--domain", required=True)
    v.set_defaults(func=cmd_validate)

    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
