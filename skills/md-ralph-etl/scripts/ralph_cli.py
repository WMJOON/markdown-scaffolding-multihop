#!/usr/bin/env python3
"""Ralph ETL Coordinator CLI.

Usage Examples:

  1) URL 기반 전체 파이프라인 (기존 TSV manifest):
     python3 tools/ralph_cli.py run --manifest data.tsv

  2) JSONL manifest로 다양한 소스 처리:
     python3 tools/ralph_cli.py run --manifest sources.jsonl --format jsonl

  3) 로컬 디렉토리의 파일들을 직접 처리:
     python3 tools/ralph_cli.py run --input-dir ./docs/ --mode local

  4) 특정 entity type만 추출:
     python3 tools/ralph_cli.py run --manifest data.tsv --scope Model,Dataset

  5) 기존 엔티티의 관계만 보강:
     python3 tools/ralph_cli.py run --manifest data.tsv --mode enrich

  6) 이전 run 재개:
     python3 tools/ralph_cli.py run --resume R-20260303-0001

  7) 상태 확인 / 리포트 생성:
     python3 tools/ralph_cli.py status --run-id R-20260303-0001
     python3 tools/ralph_cli.py report --run-id R-20260303-0001
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Support both direct execution and symlink-from-semantic-atlas
# 1. Resolved path (real file location — skill repo scripts/)
_RESOLVED_DIR = Path(__file__).resolve().parent
# 2. Unresolved path (symlink location — semantic-atlas tools/)
_LINK_DIR = Path(__file__).parent.resolve()

for d in (_LINK_DIR, _RESOLVED_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from ralph.common import EmbedMode, FetcherMode, RunConfig, RunMode, RUNS_ARCHIVE_DIR, StepName
from ralph.coordinator import RalphCoordinator, register_step


def _default_root() -> Path:
    # If called via symlink from semantic-atlas, use that project root
    link_parent = Path(__file__).parent.resolve()
    if (link_parent.parent / "data" / "ontology-entities").exists():
        return link_parent.parent
    # Otherwise, try resolved path
    return Path(__file__).resolve().parents[1]


def _register_all_steps() -> None:
    from ralph.step_intake import run_intake
    from ralph.step_crawl import run_crawl
    from ralph.step_preprocess import run_preprocess
    from ralph.step_parse import run_parse
    from ralph.step_placement import run_placement
    from ralph.step_seal import run_seal

    register_step(StepName.A_INTAKE, run_intake)
    register_step(StepName.B_CRAWL, run_crawl)
    register_step(StepName.C_PREPROCESS, run_preprocess)
    register_step(StepName.D_PARSE, run_parse)
    register_step(StepName.E_PLACE, run_placement)
    register_step(StepName.F_SEAL, run_seal)


def _add_common_args(p: argparse.ArgumentParser) -> None:
    """Add arguments shared by run and step subcommands."""
    p.add_argument("--root", default=str(_default_root()),
                   help="Ontology root directory")
    p.add_argument("--apply", action="store_true",
                   help="Write output files (default: dry-run)")
    p.add_argument("--batch-size", type=int, default=20,
                   help="Max URLs/files per batch")
    p.add_argument("--max-retry", type=int, default=3)
    p.add_argument("--timeout", type=int, default=40,
                   help="HTTP timeout seconds")
    # --- 확장 옵션 ---
    p.add_argument("--mode", choices=[m.value for m in RunMode], default=RunMode.FULL,
                   help="full: URL→crawl→전체 | local: 로컬 파일→전체 | enrich: 관계 보강만")
    p.add_argument("--format", choices=["tsv", "jsonl", "auto"], default="auto",
                   help="Manifest format (auto-detected by default)")
    p.add_argument("--scope", default="",
                   help="Comma-separated entity types to extract (e.g. Model,Work,Dataset)")
    p.add_argument("--extensions", default=".md,.txt,.html",
                   help="File extensions for directory scan (local mode)")
    p.add_argument("--embed-mode", choices=[m.value for m in EmbedMode], default=EmbedMode.AUTO,
                   help="Similarity engine: auto(BERT if available) | bert | tfidf")
    p.add_argument("--bert-model", default="sentence-transformers/all-MiniLM-L6-v2",
                   help="BERT model for embeddings (default: all-MiniLM-L6-v2)")
    p.add_argument("--fetcher", choices=[m.value for m in FetcherMode], default=FetcherMode.AUTO,
                   help="Scrapling fetcher tier (auto: source_type 기반 자동 선택 | "
                        "basic: TLS 스푸핑 HTTP | stealthy: 반봇 우회 | dynamic: JS 렌더링)")


def build_config(args: argparse.Namespace) -> RunConfig:
    scope = [s.strip() for s in args.scope.split(",") if s.strip()] if args.scope else []
    exts = [e.strip() for e in args.extensions.split(",") if e.strip()]
    input_format = args.format if hasattr(args, "format") else "auto"

    # auto-detect directory mode
    manifest = getattr(args, "manifest", "") or ""
    input_dir = getattr(args, "input_dir", "") or ""
    if input_dir or (manifest and Path(manifest).is_dir()):
        input_format = "directory"

    return RunConfig(
        batch_size=args.batch_size,
        max_retry=args.max_retry,
        http_timeout=args.timeout,
        run_mode=args.mode,
        input_format=input_format,
        scope_targets=scope,
        file_extensions=exts,
        embed_mode=getattr(args, "embed_mode", "auto"),
        bert_model=getattr(args, "bert_model", "sentence-transformers/all-MiniLM-L6-v2"),
        fetcher_mode=getattr(args, "fetcher", "auto"),
    )


def cmd_run(args: argparse.Namespace) -> None:
    _register_all_steps()
    root = Path(args.root)
    config = build_config(args)
    coord = RalphCoordinator(root, config, apply=args.apply)

    if args.resume:
        state = coord.resume_run(args.resume)
        state = coord.execute(state)
    else:
        # determine input path
        input_path = ""
        if getattr(args, "input_dir", ""):
            input_path = args.input_dir
            config.input_format = "directory"
        elif args.manifest:
            input_path = args.manifest
        else:
            print("[Ralph] Error: --manifest, --input-dir, or --resume required")
            sys.exit(1)

        manifest = Path(input_path)
        if not manifest.exists():
            print(f"[Ralph] Input not found: {manifest}")
            sys.exit(1)

        state = coord.init_run(manifest)
        state = coord.execute(state, manifest_path=manifest)

    if state.status == "RUN_FAILED":
        sys.exit(1)


def cmd_step(args: argparse.Namespace, step: StepName) -> None:
    _register_all_steps()
    root = Path(args.root)
    config = build_config(args)
    coord = RalphCoordinator(root, config, apply=args.apply)

    if args.run_id:
        state = coord.resume_run(args.run_id)
    else:
        manifest = Path(args.manifest or args.input_dir)
        state = coord.init_run(manifest)
        run_dir = coord.runs_dir / state.ralph_run_id
        (run_dir / ".manifest_path").write_text(
            str(manifest), encoding="utf-8"
        )

    state = coord.execute(state, from_step=step)


def cmd_status(args: argparse.Namespace) -> None:
    root = Path(args.root)
    runs_dir = root / RUNS_ARCHIVE_DIR
    state_path = runs_dir / args.run_id / "run_state.yaml"
    if not state_path.exists():
        print(f"[Ralph] Run not found: {args.run_id}")
        sys.exit(1)

    from ralph.yaml_io import load_run_state
    d = load_run_state(state_path)
    print(f"Run ID:  {d.get('ralph_run_id')}")
    print(f"Status:  {d.get('status')}")
    print(f"Started: {d.get('started_at')}")
    print(f"Attempt: {d.get('attempt')}/{d.get('max_retry')}")
    cps = d.get("checkpoints", [])
    if cps:
        print("Checkpoints:")
        for cp in cps:
            print(f"  {cp.get('step')}: {cp.get('artifact')} ({cp.get('completed_at', '')})")
    metrics = d.get("metrics", {})
    if metrics:
        print("Metrics:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")


def cmd_report(args: argparse.Namespace) -> None:
    _register_all_steps()
    root = Path(args.root)
    runs_dir = root / RUNS_ARCHIVE_DIR
    run_dir = runs_dir / args.run_id
    if not run_dir.exists():
        print(f"[Ralph] Run not found: {args.run_id}")
        sys.exit(1)

    from ralph.reporter import generate_reports
    generate_reports(root, run_dir)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ralph ETL Coordinator — evidence-based ontology expansion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    # --- run ---
    run_p = sub.add_parser("run", help="Execute pipeline (full/local/enrich)")
    run_p.add_argument("--manifest", default="",
                       help="Manifest file path (TSV or JSONL)")
    run_p.add_argument("--input-dir", default="",
                       help="Local directory to scan (alternative to --manifest)")
    run_p.add_argument("--resume", metavar="RUN_ID", default="",
                       help="Resume a previous run")
    _add_common_args(run_p)

    # --- individual steps ---
    for step_name in ("intake", "crawl", "preprocess", "parse", "place", "seal"):
        sp = sub.add_parser(step_name, help=f"Run step {step_name} only")
        sp.add_argument("--run-id", default="",
                        help="Existing run ID to continue")
        sp.add_argument("--manifest", default="")
        sp.add_argument("--input-dir", default="")
        _add_common_args(sp)

    # --- status ---
    status_p = sub.add_parser("status", help="Show run status")
    status_p.add_argument("--run-id", required=True)
    status_p.add_argument("--root", default=str(_default_root()))

    # --- report ---
    report_p = sub.add_parser("report", help="Generate cost + run reports")
    report_p.add_argument("--run-id", required=True)
    report_p.add_argument("--root", default=str(_default_root()))

    args = parser.parse_args()

    step_map = {
        "intake": StepName.A_INTAKE,
        "crawl": StepName.B_CRAWL,
        "preprocess": StepName.C_PREPROCESS,
        "parse": StepName.D_PARSE,
        "place": StepName.E_PLACE,
        "seal": StepName.F_SEAL,
    }

    if args.command == "run":
        if not args.resume and not args.manifest and not args.input_dir:
            parser.error("--manifest, --input-dir, or --resume is required")
        cmd_run(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command in step_map:
        cmd_step(args, step_map[args.command])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
