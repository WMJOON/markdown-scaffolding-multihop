#!/usr/bin/env python3
"""
msm-ontology gen-ddl — definition YAML → DuckDB DDL 생성
Usage: msm-ontology gen-ddl --target REPO --domain NAME [--apply]
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="definition YAML → DuckDB DDL 생성"
    )
    parser.add_argument("--target", required=True, help="대상 저장소 경로")
    parser.add_argument("--domain", required=True, help="도메인 이름")
    parser.add_argument("--apply", action="store_true", help="생성된 DDL을 DuckDB에 실제 적용")
    args = parser.parse_args()

    # TODO(v0.12.0): definition.yaml의 entity/property 로드
    # TODO(v0.12.0): CREATE TABLE SQL 생성 구현
    # TODO(v0.12.0): --apply 시 DuckDB에 DDL 실행
    raise NotImplementedError("gen_ddl stub — v0.12.0 구현 예정")


if __name__ == "__main__":
    main()
