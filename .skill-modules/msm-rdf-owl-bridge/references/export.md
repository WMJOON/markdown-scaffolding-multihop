# Mode B — MD Export + KG 분석

MD 엔티티 디렉토리를 읽어 Triple JSONL + Turtle + 분석 리포트를 생성한다.

## 출력 파일

| 파일 | 설명 |
|------|------|
| `triples.jsonl` | `{subject, predicate, object}` 전체 Triple |
| `entities.jsonl` | `{entity_id, entity_type, label_en}` 엔티티 목록 |
| `ontology.ttl` | Turtle 직렬화 (rdflib 표준) |
| `report.md` | 그래프 통계 + 연결성 분석 |
| `embed_report.md` | `--embed` 시: 엔티티별 유사도 상위 쌍 |

기본 출력 경로: `<entity_dir_parent>/export/`

## 파이프라인

```
MD 엔티티 디렉토리
  → load_entity_dir() → TripleGraph 구축
  → triples.jsonl (write_jsonl_stream)
  → entities.jsonl
  → ontology.ttl (graph.serialize("turtle"))
  → report.md (_build_report)
  → [--embed] embed_report.md (TFIDFEmbedder 또는 PyKEENEmbedder)
```

## report.md 포함 항목

- 기본 통계: 총 엔티티 수, Triple 수, 관계 유형 수, 고립 엔티티, max/avg out-degree
- 엔티티 타입별 분포
- 관계 타입별 빈도 (상위 20개)
- 허브 엔티티 (out-degree 상위 10개)

## embed_report.md 생성 조건

`--embed` 플래그 활성화 시:

| Embedder | 처리 수 | 출력 |
|----------|---------|------|
| TFIDFEmbedder | 최대 100개 엔티티 | 각 엔티티 top-5 유사 엔티티 |
| PyKEENEmbedder | 최대 50개 엔티티 | 각 엔티티 top-5 유사 엔티티 |

## 실행 예시

```bash
PYTHON="03_platform/tools/rdf-owl-bridge/.venv/bin/python"
BRIDGE="03_platform/tools/rdf-owl-bridge/__main__.py"

# 기본 Export
${PYTHON} ${BRIDGE} 01_ontology-data/data/ontology-entities

# 출력 경로 지정
${PYTHON} ${BRIDGE} 01_ontology-data/data/ontology-entities \
  --output 03_platform/export/$(date +%Y%m%d)

# TF-IDF 유사도 리포트 포함
${PYTHON} ${BRIDGE} 01_ontology-data/data/ontology-entities \
  --embed --embed-model tfidf

# PyKEEN TransE (torch+pykeen 필요)
${PYTHON} ${BRIDGE} 01_ontology-data/data/ontology-entities \
  --embed --embed-model TransE
```

## 성능 가이드라인

- 엔티티 2000개 + Triple 5000개 수준: 수초 내 완료 (TF-IDF)
- PyKEEN `--epochs 100` 기준: 수분 소요 (GPU 없을 경우)
- `--verbose`로 진행 단계별 로그 확인 가능
