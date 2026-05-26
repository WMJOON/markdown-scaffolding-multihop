#!/usr/bin/env python3
"""msm-ontology reason — OWL2 DL reasoning 실행 후 inferred facts를 JSONL에 역주입.

Usage: msm-ontology reason --target REPO [--apply]

의존성:
  pip install owlready2
  Java 런타임 (Pellet/HermiT reasoner용) — java -version 으로 확인

추론 결과 저장 경로:
  ontology/Abox/{cluster}/inferred.jsonl
  (기존 instances.jsonl은 수정하지 않음)
"""

from __future__ import annotations

import argparse
import json
import sys
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


def _extract_inferred(owlready2, onto, source_ttl: str) -> list[dict]:
    """추론된 type assertion + property assertion 추출."""
    records: list[dict] = []

    for ind in onto.individuals():
        ind_id = ind.name

        # inferred type assertions
        inferred_types = [
            c.name for c in ind.is_a
            if isinstance(c, owlready2.ThingClass) and c is not owlready2.Thing
        ]

        # inferred property assertions
        inferred_props: dict[str, list] = {}
        for prop in ind.get_properties():
            vals = list(prop[ind])
            if vals:
                inferred_props[prop.name] = [
                    v.name if hasattr(v, "name") else str(v) for v in vals
                ]

        if inferred_types or inferred_props:
            records.append({
                "id": ind_id,
                "inferred_types": inferred_types,
                "inferred_properties": inferred_props,
                "inferred": True,
                "source_ontology": source_ttl,
            })

    return records


def _write_inferred(target: Path, records: list[dict], apply: bool) -> None:
    if not records:
        _log("추론된 fact 없음.")
        return

    # cluster별로 그룹핑 없이 루트 Abox에 저장
    out_dir = target / "ontology" / "Abox" / "_inferred"
    out_path = out_dir / INFERRED_FILE

    if apply:
        out_dir.mkdir(parents=True, exist_ok=True)
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


def _reason_file(owlready2, ttl_path: Path, target: Path, apply: bool) -> int:
    _log(f"로드: {ttl_path.name}")
    try:
        onto = owlready2.get_ontology(f"file://{ttl_path.resolve()}").load()
    except Exception as e:
        _log(f"온톨로지 로드 실패: {e}", "err")
        return 0

    try:
        reasoner = _run_reasoner(owlready2, onto)
        _log(f"추론 완료 ({reasoner})")
    except Exception:
        return 0

    records = _extract_inferred(owlready2, onto, ttl_path.name)
    _write_inferred(target, records, apply)
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OWL2 DL reasoning → inferred facts JSONL 역주입"
    )
    parser.add_argument("--target", required=True, help="KB 루트 경로")
    parser.add_argument("--apply", action="store_true", help="실제 파일 쓰기 (기본: dry-run)")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    owl_dir = target / "ontology" / "owl"

    if not owl_dir.exists():
        _log("ontology/owl/ 디렉토리 없음 — compile을 먼저 실행하세요.", "err")
        sys.exit(1)

    ttl_files = sorted(owl_dir.glob("*.ttl"))
    if not ttl_files:
        _log("Turtle 파일 없음 — 'msm-ontology compile --target ...' 실행 후 다시 시도하세요.", "warn")
        sys.exit(1)

    owlready2 = _load_owlready2()
    mode = "apply" if args.apply else "dry-run"
    _log(f"reason [{mode}] — {len(ttl_files)}개 Turtle 파일")

    total = sum(_reason_file(owlready2, f, target, args.apply) for f in ttl_files)
    _log(f"총 {total}개 inferred fact 처리")


if __name__ == "__main__":
    main()
