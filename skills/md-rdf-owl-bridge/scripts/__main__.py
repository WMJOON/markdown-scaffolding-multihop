"""
rdf-owl-bridge: RDF/OWL ↔ Semantic Atlas MD 변환 + Ralph ETL placement 보강

사용법:
  python -m rdf-owl-bridge <input> [옵션]

모드 (자동 감지 또는 --mode 명시):
  import     : RDF/OWL 파일 → MD 엔티티 파일
  export     : MD 엔티티 디렉토리 → Triple Export + KG 분석 리포트
  placement  : placement_report.jsonl → embed_sim 재계산 + merge 승격

예시:
  # Mode A: Wikidata 온톨로지 임포트
  python -m rdf-owl-bridge wikidata.ttl --output /path/to/ontology-entities

  # Mode B: 전체 그래프 Export + KG 분석
  python -m rdf-owl-bridge 01_ontology-data/data/ontology-entities --embed

  # Mode C: placement 보강
  python -m rdf-owl-bridge placement_report.jsonl --threshold 0.75
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


def _setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        format="%(levelname)s %(name)s: %(message)s",
        level=level,
    )


def main():
    parser = argparse.ArgumentParser(
        prog="rdf-owl-bridge",
        description="RDF/OWL ↔ Semantic Atlas MD 브리지 + Ralph ETL 강화",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "input",
        help=(
            "입력 경로.\n"
            "  Import : .owl/.ttl/.rdf/.n3/.nt/.jsonld/.trig 파일\n"
            "  Export : MD 엔티티 디렉토리\n"
            "  Placement: placement_report.jsonl"
        ),
    )
    from router import Mode
    parser.add_argument(
        "--mode", "-m",
        choices=[m.value for m in Mode],
        help="모드 강제 지정 (미입력 시 자동 감지)",
    )
    parser.add_argument(
        "--output", "-o",
        help="출력 경로 (기본값: 모드별 자동 결정)",
    )
    parser.add_argument(
        "--embed",
        action="store_true",
        help="KG Embedding 활성화 (Mode B/C 공통). Mode C는 기본 tfidf 사용.",
    )
    parser.add_argument(
        "--embed-model",
        default="tfidf",
        choices=["tfidf", "TransE", "RotatE", "ComplEx"],
        help="Embedding 모델 (기본값: tfidf). TransE/RotatE/ComplEx는 pykeen+torch 필요.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.80,
        help="Mode C: merge 승격 embed_sim 임계값 (기본값: 0.80)",
    )
    parser.add_argument(
        "--entity-dir",
        help=(
            "MD 엔티티 루트 디렉토리.\n"
            "  Mode A: 출력 위치 지정\n"
            "  Mode C: 기존 엔티티 로드 경로 지정"
        ),
    )
    parser.add_argument(
        "--candidates",
        help="Mode C: entity_candidates.jsonl 경로 (기본값: placement_report와 같은 디렉토리)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="디버그 로그 출력",
    )

    args = parser.parse_args()
    _setup_logging(args.verbose)

    # ── 입력 경로 검증 ────────────────────────────────────────────────────────
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] 입력 경로가 존재하지 않습니다: {input_path}", file=sys.stderr)
        sys.exit(1)

    # ── 모드 감지 ─────────────────────────────────────────────────────────────
    # router 모듈은 패키지 루트에 있으므로 sys.path 조정
    import os
    sys.path.insert(0, str(Path(__file__).parent))

    from router import detect_mode, Mode
    try:
        mode = detect_mode(str(input_path), args.mode)
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[rdf-owl-bridge] 모드: {mode.value.upper()}")
    print(f"[rdf-owl-bridge] 입력: {input_path.resolve()}")

    # ── 모드별 실행 ───────────────────────────────────────────────────────────
    if mode == Mode.IMPORT:
        from modes.import_mode import run_import
        run_import(input_path, args.output, args.entity_dir)

    elif mode == Mode.EXPORT:
        from modes.export_mode import run_export
        run_export(input_path, args.output, args.embed, args.embed_model)

    elif mode == Mode.PLACEMENT:
        from modes.placement_mode import run_placement
        run_placement(
            input_path  = input_path,
            output      = args.output,
            candidates  = args.candidates,
            use_embed   = args.embed,
            embed_model = args.embed_model,
            threshold   = args.threshold,
            entity_dir  = args.entity_dir,
        )


if __name__ == "__main__":
    main()
