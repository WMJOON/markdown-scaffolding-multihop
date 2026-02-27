"""
save_insight.py
Claude의 멀티홉 추론 결과를 md 노드로 저장한다.
wikilink로 연결된 entity와 관계를 frontmatter에 자동 기록한다.

사용:
    python3 save_insight.py \
        --title "채널톡 위협 분석" \
        --content "채널톡은 4개 산업에 동시 진입 중이며..." \
        --links "competitor__채널톡,industry__유통" \
        --tags "경쟁분석,SMB" \
        --output ./insights/

    # stdin으로 content 입력 (파이프 연결)
    echo "내용" | python3 save_insight.py --title "분석" --output ./insights/

    # graph-config.yaml 기반 output 경로 자동 설정
    python3 save_insight.py --title "분석" --config graph-config.yaml
"""

import sys
import argparse
from datetime import date
from pathlib import Path

import yaml

# ──────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────

def slugify(text: str) -> str:
    import re, unicodedata
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[^\w\s\-가-힣]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:60]


def find_insight_dir(config_path: Path) -> Path:
    """graph-config.yaml 기준 insights/ 디렉토리 반환 (없으면 생성)"""
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    base = config_path.parent
    insight_dir = base / cfg.get("insight_dir", "insights")
    insight_dir.mkdir(parents=True, exist_ok=True)
    return insight_dir


def build_frontmatter(title: str, links: list[str],
                      tags: list[str], extra: dict) -> dict:
    fm: dict = {
        "title":      title,
        "entity":     "insight",
        "date":       str(date.today()),
        "tags":       tags,
        "status":     "draft",
        "generated":  "Claude multihop",
    }
    if links:
        fm["related_nodes"] = [f"[[{l.strip()}]]" for l in links if l.strip()]
    fm.update(extra)
    return fm


def build_md(frontmatter: dict, content: str, links: list[str]) -> str:
    fm_str = yaml.dump(frontmatter, allow_unicode=True,
                       default_flow_style=False, sort_keys=False)
    body = content.strip()

    # 본문 하단에 related 섹션 자동 추가
    if links:
        related = "\n\n---\n\n## Related\n\n"
        for link in links:
            link = link.strip()
            if link:
                related += f"- [[{link}]]\n"
        body += related

    return f"---\n{fm_str}---\n\n{body}\n"


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="멀티홉 추론 결과 → md 노드로 저장"
    )
    parser.add_argument("--title",   "-t", required=True, help="인사이트 제목")
    parser.add_argument("--content", "-c", default="",
                        help="내용 (생략 시 stdin에서 읽음)")
    parser.add_argument("--links",   "-l", default="",
                        help="관련 노드 ID (쉼표 구분). 예: competitor__채널톡,industry__유통")
    parser.add_argument("--tags",    "-g", default="",
                        help="태그 (쉼표 구분)")
    parser.add_argument("--output",  "-o", type=Path,
                        help="저장 디렉토리 경로")
    parser.add_argument("--config",  type=Path,
                        help="graph-config.yaml (output 대신 사용)")
    parser.add_argument("--filename", help="파일명 직접 지정 (기본: 날짜_슬러그.md)")
    parser.add_argument("--status",  default="draft",
                        choices=["draft", "reviewed", "final"])
    args = parser.parse_args()

    # 내용 읽기
    content = args.content
    if not content:
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            print("[오류] --content 또는 stdin으로 내용을 제공하세요.")
            sys.exit(1)

    # 출력 디렉토리
    if args.output:
        out_dir = args.output
        out_dir.mkdir(parents=True, exist_ok=True)
    elif args.config and args.config.exists():
        out_dir = find_insight_dir(args.config)
    else:
        out_dir = Path("insights")
        out_dir.mkdir(exist_ok=True)

    # 파일명
    today = str(date.today())
    slug  = slugify(args.title)
    filename = args.filename or f"{today}_{slug}.md"
    if not filename.endswith(".md"):
        filename += ".md"
    out_path = out_dir / filename

    # 링크 / 태그 파싱
    links = [l.strip() for l in args.links.split(",") if l.strip()]
    tags  = [t.strip() for t in args.tags.split(",")  if t.strip()]

    fm = build_frontmatter(
        title=args.title,
        links=links,
        tags=tags,
        extra={"status": args.status},
    )
    md = build_md(fm, content, links)

    out_path.write_text(md, encoding="utf-8")
    print(f"저장 완료: {out_path}")
    print(f"  제목   : {args.title}")
    print(f"  링크   : {links}")
    print(f"  태그   : {tags}")
    print(f"\n다음 단계: graph_builder.py 재실행 시 이 노드가 그래프에 포함됩니다.")
