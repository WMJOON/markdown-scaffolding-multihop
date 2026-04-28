# Ralph ETL Modules

## Pipeline Steps

| Module | File | Role |
|--------|------|------|
| [Intake](module.intake.md) | `step_intake.py` | URL/파일 정규화, dedup, 배치 |
| [Crawl](module.crawl.md) | `step_crawl.py` | curl+pandoc 크롤링 |
| [Preprocess](module.preprocess.md) | `step_preprocess.py` | 헤딩 경계 청킹 |
| [Parse](module.parse.md) | `step_parse.py` | 규칙+패턴 엔티티 추출 |
| [Placement](module.placement.md) | `step_placement.py` | 3-tier 유사도 판정 |
| [Seal](module.seal.md) | `step_seal.py` | V1-V8 검증 + Seed 봉인 |

## Workflow Protocol

| Module | Role |
|--------|------|
| [Workflow Design & Termination](module.workflow-design.md) | 설계→실행→판단→종료 프로토콜. Claude가 Ralph 실행 전 반드시 참조. |
