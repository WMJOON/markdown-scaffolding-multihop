#!/usr/bin/env python3
"""
msm-ontology definition — definition YAML 로드·검증·조회
Usage: msm-ontology definition --target REPO --domain NAME [--list | --get ENTITY]
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="definition YAML 로드·검증·조회"
    )
    parser.add_argument("--target", required=True, help="대상 저장소 경로")
    parser.add_argument("--domain", required=True, help="도메인 이름")
    parser.add_argument("--list", action="store_true", help="entity/relation 타입 목록 출력")
    parser.add_argument("--get", metavar="ENTITY", help="특정 entity 타입 상세 조회")
    args = parser.parse_args()

    # TODO(v1.2.0): ontology/definition/{domain}.yaml 로드
    # TODO(v1.2.0): entity/relation 타입 조회 구현
    raise NotImplementedError("definition stub — v1.2.0 구현 예정")


if __name__ == "__main__":
    main()
