"""
router: 입력 유형 자동 감지 → Mode 분기
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path

RDF_SUFFIXES = frozenset({".owl", ".ttl", ".rdf", ".n3", ".nt", ".jsonld", ".trig"})


class Mode(Enum):
    IMPORT    = "import"
    EXPORT    = "export"
    PLACEMENT = "placement"


def detect_mode(input_path: str, explicit_mode: str | None = None) -> Mode:
    """
    입력 경로로부터 실행 모드를 결정.

    우선순위:
      1. explicit_mode 명시 → 그대로 사용
      2. 파일 확장자가 RDF_SUFFIXES → Mode.IMPORT
      3. 파일명에 'placement' 포함 + .jsonl → Mode.PLACEMENT
      4. 디렉토리 + .md 파일 존재 → Mode.EXPORT
    """
    if explicit_mode:
        try:
            return Mode(explicit_mode.lower())
        except ValueError:
            raise ValueError(
                f"유효하지 않은 mode: '{explicit_mode}'. "
                f"선택지: {[m.value for m in Mode]}"
            )

    p = Path(input_path)

    if p.is_file():
        suffix = p.suffix.lower()
        if suffix in RDF_SUFFIXES:
            return Mode.IMPORT
        if suffix == ".jsonl" and "placement" in p.name.lower():
            return Mode.PLACEMENT
        raise ValueError(
            f"파일 유형 자동 감지 실패: '{p.name}'\n"
            f"지원 확장자: {', '.join(sorted(RDF_SUFFIXES))} (Import)\n"
            f"또는 'placement*.jsonl' (Placement)\n"
            f"--mode 플래그로 명시하세요."
        )

    if p.is_dir():
        md_files = list(p.rglob("*.md"))
        if md_files:
            return Mode.EXPORT
        raise ValueError(
            f"디렉토리에 .md 파일이 없습니다: '{p}'\n"
            f"엔티티 디렉토리인지 확인하세요."
        )

    raise ValueError(
        f"입력 경로가 존재하지 않거나 감지 불가: '{input_path}'"
    )
