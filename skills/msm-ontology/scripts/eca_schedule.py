#!/usr/bin/env python3
"""
msm-ontology eca-schedule — scheduled ECA 규칙 실행 (cron runner)
Usage: msm-ontology eca-schedule --target REPO [--domain NAME] [--dry-run]
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="scheduled ECA 규칙 실행 (cron runner)"
    )
    parser.add_argument("--target", required=True, help="대상 저장소 경로")
    parser.add_argument("--domain", default=None, help="특정 도메인만 실행 (생략 시 전체)")
    parser.add_argument("--dry-run", action="store_true", help="실제 실행 없이 대상 규칙만 출력")
    args = parser.parse_args()

    # TODO(v1.2.0): trigger.type=scheduled 규칙 중 현재 시각에 해당하는 것 조회
    # TODO(v1.2.0): dry-run 모드 구현
    # TODO(v1.2.0): 해당 규칙 실행 구현
    raise NotImplementedError("eca_schedule stub — v1.2.0 구현 예정")


if __name__ == "__main__":
    main()
