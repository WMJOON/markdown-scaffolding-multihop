#!/usr/bin/env python3
"""msm-ontology compile — LinkML YAML definition을 OWL/Turtle로 변환.

Usage: msm-ontology compile --target REPO [--domain NAME] [--out-dir DIR]
                            [--no-postprocess] [--apply]

기본 동작: owlgen 으로 base TTL 생성 후 owl_postprocess 자동 적용
  (FunctionalProperty/다국어 label 등 owlgen 미지원 OWL 보강 — addendum PRD §3.1).
  --no-postprocess 시 base owlgen 출력 그대로(AC-A3: v0.13.0 동일).
출력 경로: --out-dir 미지정 시 <target>/ontology/owl (v0.13.0 기본 유지).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOL_VERSION = "msm-ontology/0.13.0"


def _log(msg: str, level: str = "info") -> None:
    prefix = {"info": "[*]", "ok": "[+]", "warn": "[!]", "err": "[x]"}[level]
    print(f"{prefix} {msg}", file=sys.stderr, flush=True)


def _compile_yaml(yaml_path: Path, owl_dir: Path, apply: bool, postprocess: bool) -> bool:
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
        if postprocess:
            _run_postprocess(out_path)
    else:
        _log(f"[dry] would write {out_path}")
        # print first 5 non-empty lines as preview
        preview = [l for l in ttl.splitlines() if l.strip()][:5]
        for line in preview:
            print(f"      {line}")
        if postprocess:
            _log("[dry] --apply 후 owl_postprocess 자동 적용 예정 "
                 "(FunctionalProperty/다국어 label 보강)")

    return True


def _run_postprocess(ttl_path: Path) -> None:
    """compile 직후 owl_postprocess 를 인라인 적용 (addendum §3.4-1 결정 (a))."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import owl_postprocess as _pp
    except ImportError as e:  # noqa: BLE001
        _log(f"owl_postprocess 임포트 실패 ({e}) — base TTL 유지", "warn")
        return
    _pp.postprocess_ttl(ttl_path, apply=True, keep_carriers=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LinkML YAML definition → OWL/Turtle (+ owl_postprocess)"
    )
    parser.add_argument("--target", required=True, help="KB 루트 경로")
    parser.add_argument("--domain", default=None, help="특정 도메인만 컴파일 (기본: 전체)")
    parser.add_argument("--out-dir", default=None,
                        help="TTL 출력 디렉토리 (기본: <target>/ontology/owl)")
    parser.add_argument("--no-postprocess", action="store_true",
                        help="owl_postprocess 비활성 (base owlgen 출력 그대로)")
    parser.add_argument("--apply", action="store_true", help="실제 파일 쓰기 (기본: dry-run)")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    def_dir = target / "ontology" / "definition"
    if args.out_dir:
        _p = Path(args.out_dir)
        owl_dir = _p if _p.is_absolute() else (target / _p)
    else:
        owl_dir = target / "ontology" / "owl"

    postprocess = not args.no_postprocess

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
    pp_note = "owl_postprocess 자동" if postprocess else "postprocess off"
    _log(f"compile [{mode}] — {len(yaml_files)}개 파일 → {owl_dir} ({pp_note})")

    ok = sum(_compile_yaml(f, owl_dir, args.apply, postprocess) for f in yaml_files)
    failed = len(yaml_files) - ok

    _log(f"완료: {ok}개 성공 / {failed}개 실패")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
