#!/usr/bin/env python3
"""msm-ontology compile — LinkML YAML definition을 OWL/Turtle로 변환.

Usage: msm-ontology compile --target REPO [--domain NAME] [--apply]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOL_VERSION = "msm-ontology/0.13.0"


def _log(msg: str, level: str = "info") -> None:
    prefix = {"info": "[*]", "ok": "[+]", "warn": "[!]", "err": "[x]"}[level]
    print(f"{prefix} {msg}", file=sys.stderr, flush=True)


def _compile_yaml(yaml_path: Path, owl_dir: Path, apply: bool) -> bool:
    try:
        from linkml.generators.owlgen import OwlSchemaGenerator
    except ImportError:
        _log("linkml not installed. Run: pip install linkml", "err")
        sys.exit(1)

    try:
        gen = OwlSchemaGenerator(str(yaml_path), use_native_uris=False)
        ttl = gen.serialize()
    except Exception as e:
        _log(f"compile failed for {yaml_path.name}: {e}", "err")
        return False

    out_path = owl_dir / f"{yaml_path.stem}.ttl"

    if apply:
        owl_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_text(ttl, encoding="utf-8")
        _log(f"compiled {yaml_path.name} → {out_path.name}", "ok")
    else:
        _log(f"[dry] would write {out_path.relative_to(out_path.parent.parent.parent)}")
        # print first 5 non-empty lines as preview
        preview = [l for l in ttl.splitlines() if l.strip()][:5]
        for line in preview:
            print(f"      {line}")

    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LinkML YAML definition → OWL/Turtle"
    )
    parser.add_argument("--target", required=True, help="KB 루트 경로")
    parser.add_argument("--domain", default=None, help="특정 도메인만 컴파일 (기본: 전체)")
    parser.add_argument("--apply", action="store_true", help="실제 파일 쓰기 (기본: dry-run)")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    def_dir = target / "ontology" / "definition"
    owl_dir = target / "ontology" / "owl"

    if not def_dir.exists():
        _log(f"definition 디렉토리 없음: {def_dir}", "err")
        _log("ontology/definition/{domain}.yaml 파일을 먼저 작성하세요.")
        sys.exit(1)

    if args.domain:
        yaml_files = [def_dir / f"{args.domain}.yaml"]
        missing = [f for f in yaml_files if not f.exists()]
        if missing:
            _log(f"파일 없음: {missing[0]}", "err")
            sys.exit(1)
    else:
        yaml_files = sorted(def_dir.glob("*.yaml"))
        if not yaml_files:
            _log("definition YAML 파일이 없습니다.", "warn")
            sys.exit(0)

    mode = "apply" if args.apply else "dry-run"
    _log(f"compile [{mode}] — {len(yaml_files)}개 파일")

    ok = sum(_compile_yaml(f, owl_dir, args.apply) for f in yaml_files)
    failed = len(yaml_files) - ok

    _log(f"완료: {ok}개 성공 / {failed}개 실패")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
