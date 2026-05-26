#!/usr/bin/env python3
"""msm-ontology materialize — compile + reason 연속 실행.

Usage: msm-ontology materialize --target REPO [--domain NAME] [--apply]
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
    parser.add_argument("--apply", action="store_true", help="실제 파일 쓰기 (기본: dry-run)")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir))

    import compile as _compile
    import reason as _reason

    _log("=== step 1/2: compile ===")
    # compile.main()을 직접 호출하기 위해 sys.argv를 교체
    _orig_argv = sys.argv[:]
    compile_argv = ["compile", "--target", args.target]
    if args.domain:
        compile_argv += ["--domain", args.domain]
    if args.apply:
        compile_argv.append("--apply")
    sys.argv = compile_argv

    try:
        _compile.main()
    except SystemExit as e:
        if e.code != 0:
            _log("compile 실패 — reason 중단", "err")
            sys.exit(int(e.code))
    finally:
        sys.argv = _orig_argv

    _log("=== step 2/2: reason ===")
    reason_argv = ["reason", "--target", args.target]
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
