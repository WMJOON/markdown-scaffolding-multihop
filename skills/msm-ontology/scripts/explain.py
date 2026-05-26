#!/usr/bin/env python3
"""msm-ontology explain — 특정 instance의 추론 근거 출력.

Usage: msm-ontology explain --target REPO --instance ID

예시:
  msm-ontology explain --target ./my-kb --instance gemma4_e2b

출력:
  instance가 어떤 type으로 분류됐는지, 어떤 property가 inferred됐는지
  근거가 된 ontology 파일도 함께 표시.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

INFERRED_FILE = "ontology/Abox/_inferred/inferred.jsonl"


def _log(msg: str, level: str = "info") -> None:
    prefix = {"info": "[*]", "ok": "[+]", "warn": "[!]", "err": "[x]"}[level]
    print(f"{prefix} {msg}", file=sys.stderr, flush=True)


def _load_inferred(target: Path) -> list[dict]:
    path = target / INFERRED_FILE
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return records


def _load_original(target: Path, instance_id: str) -> dict | None:
    """Abox JSONL에서 원본 instance 레코드 탐색."""
    abox_root = target / "ontology" / "Abox"
    for jsonl_file in abox_root.rglob("*.jsonl"):
        if "_inferred" in str(jsonl_file):
            continue
        for line in jsonl_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                if r.get("id") == instance_id or r.get("entity_id") == instance_id:
                    return r
            except json.JSONDecodeError:
                pass
    return None


def _print_explain(instance_id: str, original: dict | None, inferred: dict | None) -> None:
    print(f"\n{'='*60}")
    print(f"instance: {instance_id}")
    print(f"{'='*60}")

    if original:
        print("\n[원본 레코드]")
        orig_type = original.get("entity_type") or original.get("type", "—")
        print(f"  type       : {orig_type}")
        for k, v in original.items():
            if k not in ("id", "entity_id", "entity_type", "type"):
                print(f"  {k:<16}: {v}")

    if inferred:
        print("\n[추론 결과]")
        print(f"  source     : {inferred.get('source_ontology', '—')}")

        types = inferred.get("inferred_types", [])
        if types:
            print(f"  inferred types:")
            for t in types:
                print(f"    + {t}")

        props = inferred.get("inferred_properties", {})
        if props:
            print(f"  inferred properties:")
            for prop, vals in props.items():
                print(f"    {prop}: {vals}")

        print("\n[근거 axiom 조회]")
        print("  owlready2 axiomatic trace는 'reason --apply' 후 Turtle 파일에서 확인 가능:")
        ttl_path = Path(inferred.get("source_ontology", ""))
        print(f"  ontology/owl/{ttl_path.name if ttl_path.name else '*.ttl'}")
    else:
        print("\n[추론 결과 없음]")
        print("  'msm-ontology materialize --target ...' 실행 후 다시 시도하세요.")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="instance의 OWL 추론 근거 출력"
    )
    parser.add_argument("--target", required=True, help="KB 루트 경로")
    parser.add_argument("--instance", required=True, help="조회할 instance ID")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    instance_id = args.instance

    all_inferred = _load_inferred(target)
    inferred = next((r for r in all_inferred if r.get("id") == instance_id), None)
    original = _load_original(target, instance_id)

    if not original and not inferred:
        _log(f"instance '{instance_id}' 를 찾을 수 없습니다.", "err")
        _log("Abox JSONL 또는 inferred.jsonl에 해당 ID가 없습니다.")
        sys.exit(1)

    _print_explain(instance_id, original, inferred)


if __name__ == "__main__":
    main()
