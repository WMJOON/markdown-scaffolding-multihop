#!/usr/bin/env python3
"""
obsidian_cli.py — Obsidian CLI Python 래퍼

실행 중인 Obsidian 앱의 CLI(`obsidian` 바이너리)를 Python에서 호출하는 유틸리티.
복잡한 배치 자동화·출력 파싱에 사용한다.

전제 조건:
  - Obsidian 1.12+ 설치 및 실행 중
  - Settings → General → Command line interface 활성화
  - `obsidian` 바이너리가 PATH에 등록됨

사용법:
  python3 obsidian_cli.py <subcommand> [options]

서브커맨드:
  run <command> [param=value ...] [flag ...]  — 단일 명령 실행
  batch-create --names NAME [NAME ...] [--vault VAULT] [--template TMPL]
  search-json --query QUERY [--vault VAULT] [--folder FOLDER]
  tasks-json [--daily] [--todo] [--done] [--file FILE] [--vault VAULT]
"""

import argparse
import json
import subprocess
import sys
from typing import Optional


# ── 핵심 실행기 ──────────────────────────────────────────────────────────────

def run_obsidian(args: list[str], vault: Optional[str] = None) -> str:
    """
    `obsidian` CLI를 실행하고 stdout을 반환한다.

    Args:
        args: CLI 인자 목록 (예: ["read", "file=Note"])
        vault: vault 이름/ID (None이면 기본 vault 사용)

    Returns:
        stdout 문자열 (strip 처리)

    Raises:
        RuntimeError: CLI 실행 실패 시
    """
    cmd = ["obsidian"]
    if vault:
        cmd.append(f"vault={vault}")
    cmd.extend(args)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"obsidian 명령 실패 (exit {result.returncode})\n"
            f"명령: {' '.join(cmd)}\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def run_obsidian_json(args: list[str], vault: Optional[str] = None) -> list | dict:
    """JSON 출력을 파싱해 반환한다."""
    # format=json이 없으면 추가
    if not any(a.startswith("format=") for a in args):
        args = args + ["format=json"]
    raw = run_obsidian(args, vault=vault)
    return json.loads(raw)


# ── 서브커맨드 구현 ──────────────────────────────────────────────────────────

def cmd_run(argv: list[str]) -> None:
    """단일 obsidian 명령 실행 후 출력 표시."""
    parser = argparse.ArgumentParser(prog="obsidian_cli run")
    parser.add_argument("command", help="obsidian 명령 (예: read, daily:append)")
    parser.add_argument("params", nargs="*", help="파라미터/플래그 (예: file=Note open)")
    parser.add_argument("--vault", help="대상 vault 이름")
    args = parser.parse_args(argv)

    output = run_obsidian([args.command] + args.params, vault=args.vault)
    print(output)


def cmd_batch_create(argv: list[str]) -> None:
    """여러 노트를 일괄 생성한다."""
    parser = argparse.ArgumentParser(prog="obsidian_cli batch-create")
    parser.add_argument("--names", nargs="+", required=True, help="노트 이름 목록")
    parser.add_argument("--vault", help="대상 vault 이름")
    parser.add_argument("--template", help="사용할 템플릿 이름")
    parser.add_argument("--folder", help="생성할 폴더 경로 (path= 접두어로 사용)")
    parser.add_argument("--content", help="초기 내용")
    args = parser.parse_args(argv)

    results = []
    for name in args.names:
        cli_args = ["create"]
        if args.folder:
            cli_args.append(f"path={args.folder}/{name}.md")
        else:
            cli_args.append(f"name={name}")
        if args.template:
            cli_args.append(f"template={args.template}")
        if args.content:
            cli_args.append(f'content={args.content}')

        try:
            run_obsidian(cli_args, vault=args.vault)
            results.append({"name": name, "status": "created"})
            print(f"✓ {name}")
        except RuntimeError as e:
            results.append({"name": name, "status": "error", "error": str(e)})
            print(f"✗ {name}: {e}", file=sys.stderr)

    success = sum(1 for r in results if r["status"] == "created")
    print(f"\n완료: {success}/{len(args.names)}개 생성")


def cmd_search_json(argv: list[str]) -> None:
    """검색 결과를 JSON으로 출력한다."""
    parser = argparse.ArgumentParser(prog="obsidian_cli search-json")
    parser.add_argument("--query", required=True, help="검색 쿼리")
    parser.add_argument("--vault", help="대상 vault")
    parser.add_argument("--folder", help="검색 범위 폴더")
    parser.add_argument("--limit", type=int, help="최대 결과 수")
    parser.add_argument("--context", action="store_true", help="컨텍스트 포함 (search:context)")
    args = parser.parse_args(argv)

    command = "search:context" if args.context else "search"
    cli_args = [command, f"query={args.query}"]
    if args.folder:
        cli_args.append(f"path={args.folder}")
    if args.limit:
        cli_args.append(f"limit={args.limit}")

    results = run_obsidian_json(cli_args, vault=args.vault)
    print(json.dumps(results, ensure_ascii=False, indent=2))


def cmd_tasks_json(argv: list[str]) -> None:
    """태스크 목록을 JSON으로 출력한다."""
    parser = argparse.ArgumentParser(prog="obsidian_cli tasks-json")
    parser.add_argument("--vault", help="대상 vault")
    parser.add_argument("--file", help="파일 이름으로 필터")
    parser.add_argument("--daily", action="store_true", help="일간 노트 태스크만")
    parser.add_argument("--todo", action="store_true", help="미완료 태스크만")
    parser.add_argument("--done", action="store_true", help="완료 태스크만")
    args = parser.parse_args(argv)

    cli_args = ["tasks"]
    if args.file:
        cli_args.append(f"file={args.file}")
    if args.daily:
        cli_args.append("daily")
    if args.todo:
        cli_args.append("todo")
    if args.done:
        cli_args.append("done")

    results = run_obsidian_json(cli_args, vault=args.vault)
    print(json.dumps(results, ensure_ascii=False, indent=2))


# ── main ─────────────────────────────────────────────────────────────────────

COMMANDS = {
    "run": cmd_run,
    "batch-create": cmd_batch_create,
    "search-json": cmd_search_json,
    "tasks-json": cmd_tasks_json,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        print("서브커맨드:", ", ".join(COMMANDS))
        sys.exit(0)

    subcmd = sys.argv[1]
    if subcmd not in COMMANDS:
        print(f"알 수 없는 서브커맨드: {subcmd}", file=sys.stderr)
        print("사용 가능:", ", ".join(COMMANDS))
        sys.exit(1)

    COMMANDS[subcmd](sys.argv[2:])


if __name__ == "__main__":
    main()
