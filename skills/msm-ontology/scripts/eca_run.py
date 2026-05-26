#!/usr/bin/env python3
"""
msm-ontology eca-run — ECA rule_runner 실행
Usage: msm-ontology eca-run --target REPO --table TABLE --row JSON
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ECA rule_runner 실행"
    )
    parser.add_argument("--target", required=True, help="대상 저장소 경로")
    parser.add_argument("--table", required=True, help="대상 테이블 이름")
    parser.add_argument("--row", required=True, metavar="JSON", help="삽입된 행 데이터 (JSON 문자열)")
    args = parser.parse_args()

    # TODO(v1.2.0): ontology/kinetic/rules/*.yaml 로드
    # TODO(v1.2.0): on_insert ECA 규칙 평가·실행 구현
    raise NotImplementedError("eca_run stub — v1.2.0 구현 예정")


if __name__ == "__main__":
    main()
