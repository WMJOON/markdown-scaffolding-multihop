#!/usr/bin/env python3
"""msm-ontology materialize — compile + abox-compile + reason 연속 실행.

Usage: msm-ontology materialize --target REPO [--domain NAME] [--apply]

흐름: TBox(definition→owl/{d}.ttl, +postprocess) → ABox(Abox/{d}.yaml→owl/{d}.abox.ttl)
      → reason(owl/*.ttl 병합 추론 → inferred.jsonl). ABox 디렉토리가 없으면 ABox 단계는 건너뛴다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOL_VERSION = "msm-ontology/0.13.0"


def _log(msg: str, level: str = "info") -> None:
    prefix = {"info": "[*]", "ok": "[+]", "warn": "[!]", "err": "[x]"}[level]
    print(f"{prefix} {msg}", file=sys.stderr, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="compile + reason 연속 실행 (YAML → Turtle → inferred JSONL)"
    )
    parser.add_argument("--target", required=True, help="KB 루트 경로")
    parser.add_argument("--domain", default=None, help="특정 도메인만 처리")
    parser.add_argument("--out-dir", default=None,
                        help="TTL 디렉토리 (compile 출력 = reason 입력, 기본: ontology/owl)")
    parser.add_argument("--inferred-dir", default=None,
                        help="inferred.jsonl 출력 디렉토리 (기본: ontology/Abox/_inferred)")
    parser.add_argument("--no-postprocess", action="store_true",
                        help="compile 단계 owl_postprocess 비활성")
    parser.add_argument("--apply", action="store_true", help="실제 파일 쓰기 (기본: dry-run)")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir))

    import compile as _compile
    import abox_compile as _abox
    import reason as _reason
    import rbox as _rbox

    _orig_argv = sys.argv[:]
    # step 1: compile (TBox) — definition 디렉토리가 있을 때만 (abox/rbox 와 동일한 조건부 패턴).
    # RBox-only / ABox-only KB 도 materialize 가능하도록 비대칭 hard-abort 제거.
    def_dir = Path(args.target).resolve() / "ontology" / "definition"
    if def_dir.exists() and any(def_dir.glob("*.yaml")):
        _log("=== step 1/3: compile (TBox) ===")
        compile_argv = ["compile", "--target", args.target]
        if args.domain:
            compile_argv += ["--domain", args.domain]
        if args.out_dir:
            compile_argv += ["--out-dir", args.out_dir]
        if args.no_postprocess:
            compile_argv.append("--no-postprocess")
        if args.apply:
            compile_argv.append("--apply")
        sys.argv = compile_argv
        try:
            _compile.main()
        except SystemExit as e:
            if e.code not in (0, None):
                _log("compile 실패 — 중단", "err")
                sys.exit(int(e.code))
        finally:
            sys.argv = _orig_argv
    else:
        _log("=== step 1/3: compile (TBox) 건너뜀 (ontology/definition/*.yaml 없음) ===")

    # step 1b: rbox-compile (RBox roles 가 있을 때만) — owl/{d}.rbox.ttl 생성
    # 이게 있어야 reason 의 owl/*.ttl 병합 그래프에 RBox 공리(subPropertyOf/chain/...)가 들어간다.
    rbox_dir = Path(args.target).resolve() / "ontology" / "Rbox" / "roles"
    if rbox_dir.exists() and any(rbox_dir.glob("*.yaml")):
        _log("=== step 1b: rbox-compile (RBox roles) ===")
        rbox_argv = ["compile", "--target", args.target]
        if args.domain:
            rbox_argv += ["--domain", args.domain]
        if args.out_dir:
            rbox_argv += ["--out-dir", args.out_dir]
        if args.no_postprocess:
            rbox_argv.append("--no-postprocess")
        if args.apply:
            rbox_argv.append("--apply")
        rc = _rbox.main(rbox_argv)
        if rc not in (0, None):
            _log("rbox-compile 실패 — 중단", "err")
            sys.exit(int(rc))
    else:
        _log("=== step 1b: rbox-compile 건너뜀 (ontology/Rbox/roles/*.yaml 없음) ===")

    # step 2/3: abox-compile (ABox 디렉토리가 있을 때만)
    abox_dir = Path(args.target).resolve() / "ontology" / "Abox"
    if abox_dir.exists() and any(abox_dir.glob("*.yaml")):
        _log("=== step 2/3: abox-compile (ABox) ===")
        abox_argv = ["abox-compile", "--target", args.target]
        if args.domain:
            abox_argv += ["--domain", args.domain]
        if args.out_dir:
            abox_argv += ["--out-dir", args.out_dir]
        if args.apply:
            abox_argv.append("--apply")
        sys.argv = abox_argv
        try:
            _abox.main()
        except SystemExit as e:
            if e.code not in (0, None):
                _log("abox-compile 실패 — reason 중단", "err")
                sys.exit(int(e.code))
        finally:
            sys.argv = _orig_argv
    else:
        _log("=== step 2/3: abox-compile 건너뜀 (ontology/Abox/*.yaml 없음) ===")

    _log("=== step 3/3: reason (TBox+ABox 병합) ===")
    reason_argv = ["reason", "--target", args.target]
    if args.out_dir:
        reason_argv += ["--out-dir", args.out_dir]
    if args.inferred_dir:
        reason_argv += ["--inferred-dir", args.inferred_dir]
    if args.apply:
        reason_argv.append("--apply")
    sys.argv = reason_argv

    try:
        _reason.main()
    except SystemExit as e:
        sys.exit(int(e.code) if e.code is not None else 0)
    finally:
        sys.argv = _orig_argv

    _log("materialize 완료", "ok")


if __name__ == "__main__":
    main()
