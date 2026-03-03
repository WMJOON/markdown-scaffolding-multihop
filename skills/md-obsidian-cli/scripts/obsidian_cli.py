#!/usr/bin/env python3
"""
obsidian_cli.py — obsidian:// URI 빌더 + 플랫폼별 실행기

사용법:
  python3 obsidian_cli.py [--dry-run] <action> [options]
  python3 obsidian_cli.py --dry-run open --vault "my vault" --file "note"
  python3 obsidian_cli.py new --vault "my vault" --name "새 노트" --content "내용"
  python3 obsidian_cli.py search --vault "my vault" --query "keyword"
  python3 obsidian_cli.py daily --vault "my vault"
  python3 obsidian_cli.py exec "obsidian://open?vault=my%20vault"

임포트해서 사용할 수도 있음:
  from obsidian_cli import build_uri, run_uri
"""

import argparse
import os
import platform
import subprocess
import sys
import unicodedata
from urllib.parse import quote


# ── 인코딩 유틸 ──────────────────────────────────────────────

def nfc(s: str) -> str:
    """macOS HFS+ NFC 정규화 (한글 경로 대응)"""
    return unicodedata.normalize("NFC", s)


def enc(value: str) -> str:
    """URI 퍼센트 인코딩. NFC 정규화 후 인코딩."""
    return quote(nfc(value), safe="")


# ── URI 빌더 ─────────────────────────────────────────────────

def _params(**kwargs) -> str:
    """kwargs → URI 쿼리 문자열 (None 값 제외)"""
    parts = []
    for k, v in kwargs.items():
        if v is None:
            continue
        if isinstance(v, bool):
            parts.append(f"{k}={str(v).lower()}")
        else:
            parts.append(f"{k}={enc(str(v))}")
    return "&".join(parts)


def build_uri(action: str, **kwargs) -> str:
    """obsidian:// URI를 빌드해 반환한다."""
    query = _params(**kwargs)
    if query:
        return f"obsidian://{action}?{query}"
    return f"obsidian://{action}"


# ── 실행기 ───────────────────────────────────────────────────

def _open_command() -> list[str]:
    """플랫폼별 URI 실행 명령 반환"""
    system = platform.system()
    if system == "Darwin":
        return ["open"]
    elif system == "Linux":
        return ["xdg-open"]
    elif system == "Windows":
        return ["cmd", "/c", "start", ""]
    else:
        raise RuntimeError(f"지원하지 않는 플랫폼: {system}")


def run_uri(action: str, dry_run: bool = False, **kwargs) -> str:
    """URI를 빌드하고 실행한다. dry_run=True면 출력만."""
    uri = build_uri(action, **kwargs)
    print(f"→ {uri}")
    if not dry_run:
        cmd = _open_command() + [uri]
        subprocess.run(cmd, check=True)
    return uri


def exec_uri(uri: str, dry_run: bool = False) -> None:
    """미리 완성된 URI를 직접 실행한다."""
    print(f"→ {uri}")
    if not dry_run:
        cmd = _open_command() + [uri]
        subprocess.run(cmd, check=True)


# ── 액션 핸들러 ──────────────────────────────────────────────

def handle_open(args) -> None:
    run_uri(
        "open",
        dry_run=args.dry_run,
        vault=args.vault,
        file=args.file,
        path=args.path,
        paneType=args.pane,
    )


def handle_new(args) -> None:
    if args.append and args.overwrite:
        print("오류: --append와 --overwrite는 동시에 사용할 수 없습니다.", file=sys.stderr)
        sys.exit(1)
    if args.content and args.clipboard:
        print("오류: --content와 --clipboard는 동시에 사용할 수 없습니다.", file=sys.stderr)
        sys.exit(1)

    run_uri(
        "new",
        dry_run=args.dry_run,
        vault=args.vault,
        name=args.name,
        file=args.file,
        path=args.path,
        content=args.content,
        clipboard=True if args.clipboard else None,
        silent=True if args.silent else None,
        append=True if args.append else None,
        overwrite=True if args.overwrite else None,
    )


def handle_search(args) -> None:
    run_uri(
        "search",
        dry_run=args.dry_run,
        vault=args.vault,
        query=args.query,
    )


def handle_daily(args) -> None:
    run_uri(
        "daily",
        dry_run=args.dry_run,
        vault=args.vault,
    )


def handle_exec(args) -> None:
    exec_uri(args.uri, dry_run=args.dry_run)


# ── CLI 정의 ─────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="obsidian_cli",
        description="obsidian:// URI 빌더 — Obsidian vault를 CLI에서 조작",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  %(prog)s open --vault "my vault" --file "Projects/Note"
  %(prog)s --dry-run new --vault "my vault" --name "Quick Note" --content "내용"
  %(prog)s search --vault "my vault" --query "GraphRAG"
  %(prog)s daily --vault "my vault"
  %(prog)s exec "obsidian://open?vault=my%%20vault&file=Dashboard"
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="URI만 출력하고 Obsidian을 실행하지 않음",
    )

    sub = parser.add_subparsers(dest="action", required=True, metavar="action")

    # ── open ──────────────────────────────────────────────────
    p_open = sub.add_parser("open", help="노트 또는 볼트 열기")
    p_open.add_argument("--vault", metavar="NAME", help="볼트 이름 또는 ID")
    p_open.add_argument("--file", metavar="PATH", help="볼트 내 상대 경로 (확장자 생략 가능)")
    p_open.add_argument("--path", metavar="ABSPATH", help="절대 파일 경로")
    p_open.add_argument(
        "--pane",
        choices=["tab", "split", "window"],
        metavar="tab|split|window",
        help="열기 위치 (기본: 현재 탭)",
    )
    p_open.set_defaults(func=handle_open)

    # ── new ───────────────────────────────────────────────────
    p_new = sub.add_parser("new", help="새 노트 생성")
    p_new.add_argument("--vault", metavar="NAME", help="볼트 이름 또는 ID")
    p_new.add_argument("--name", metavar="NAME", help="노트 이름 (경로 없이 이름만)")
    p_new.add_argument("--file", metavar="PATH", help="볼트 내 상대 경로 (폴더/이름)")
    p_new.add_argument("--path", metavar="ABSPATH", help="절대 파일 경로")
    p_new.add_argument("--content", metavar="TEXT", help="노트 초기 내용")
    p_new.add_argument("--clipboard", action="store_true", help="클립보드 내용을 content로 사용")
    p_new.add_argument("--silent", action="store_true", help="에디터에서 열지 않고 생성만")
    p_new.add_argument("--append", action="store_true", help="기존 파일 끝에 content 추가")
    p_new.add_argument("--overwrite", action="store_true", help="기존 파일 내용 교체")
    p_new.set_defaults(func=handle_new)

    # ── search ────────────────────────────────────────────────
    p_search = sub.add_parser("search", help="검색 패널 열기")
    p_search.add_argument("--vault", metavar="NAME", help="볼트 이름 또는 ID")
    p_search.add_argument("--query", metavar="TEXT", help="검색 쿼리")
    p_search.set_defaults(func=handle_search)

    # ── daily ─────────────────────────────────────────────────
    p_daily = sub.add_parser("daily", help="오늘 일간 노트 열기 (Daily notes 플러그인 필요)")
    p_daily.add_argument("--vault", metavar="NAME", help="볼트 이름 또는 ID")
    p_daily.set_defaults(func=handle_daily)

    # ── exec ──────────────────────────────────────────────────
    p_exec = sub.add_parser("exec", help="obsidian:// URI를 직접 실행")
    p_exec.add_argument("uri", metavar="URI", help="obsidian:// URI 문자열")
    p_exec.set_defaults(func=handle_exec)

    return parser


def main() -> None:
    # 환경변수로 기본 볼트 설정 지원
    default_vault = os.environ.get("OBSIDIAN_VAULT")

    parser = build_parser()
    args = parser.parse_args()

    # 환경변수 기본값 주입 (--vault 미지정 시)
    if hasattr(args, "vault") and args.vault is None and default_vault:
        args.vault = default_vault

    args.func(args)


if __name__ == "__main__":
    main()
