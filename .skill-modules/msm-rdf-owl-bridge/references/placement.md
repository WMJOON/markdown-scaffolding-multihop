# Mode C — Placement embed_sim 보강

Ralph ETL의 `placement_report.jsonl`에서 `embed_sim == 0.0` 항목을 재계산하고,
임계값 이상인 `merge_candidate`를 `merge`로 승격한다.

## 입력 파일

| 파일 | 설명 |
|------|------|
| `placement_report.jsonl` | Ralph ETL E_PLACE 단계 출력 (필수) |
| `entity_candidates.jsonl` | Ralph ETL D_PARSE 단계 출력 (선택, feature_text 구성용) |

`entity_candidates.jsonl`이 없으면 candidate feature_text를 `label_en`만으로 구성 (성능 저하).

## placement_report.jsonl 필드

```json
{
  "candidate_id": "model__gpt-4o",
  "label": "merge_candidate",
  "target_existing_id": "model__gpt-4",
  "alias_sim": 0.82,
  "embed_sim": 0.0,
  "evidence_count": 3,
  "conflict_layer": null,
  "reason": "alias 유사도 0.82 (threshold=0.7)"
}
```

## 재계산 대상 label

`_RECALC_LABELS = {"merge_candidate", "merge", "extend", "new"}`
이미 `embed_sim > 0.0`이면 건너뜀.

## merge 승격 조건

label이 `merge_candidate`이고 재계산된 `embed_sim >= threshold`이면 → `label: merge`로 변경

## 파이프라인

```
placement_report.jsonl
  → embed_sim == 0.0 항목 필터
  → entity_candidates.jsonl에서 feature_text 구성
  → TFIDFEmbedder.encode(feature_text)
  → cosine_similarity vs target_existing_id
  → embed_sim 갱신
  → merge_candidate + sim >= threshold → label: merge
  → *_enriched.jsonl 저장
  → placement_enrichment_report.md 생성
```

## feature_text 구성 규칙

```
"{entity_type} {label_en} {label_ko} {aliases...} {relation_type target...}"
```

`entity_candidates.jsonl`의 `aliases`(list), `relations`(list of {type, target}) 활용.

## 출력 파일

| 파일 | 설명 |
|------|------|
| `*_enriched.jsonl` | 원본 + embed_sim/label 갱신 버전 |
| `placement_enrichment_report.md` | 처리 통계 + label 분포 + embed_sim 분포 |

## 실행 예시

```bash
PYTHON="03_platform/tools/rdf-owl-bridge/.venv/bin/python"
BRIDGE="03_platform/tools/rdf-owl-bridge/__main__.py"

# 기본 실행 (임계값 0.80)
${PYTHON} ${BRIDGE} archive/history/ralph-runs/RUN-001/placement_report.jsonl

# 임계값 조정
${PYTHON} ${BRIDGE} archive/history/ralph-runs/RUN-001/placement_report.jsonl \
  --threshold 0.75

# 파일 경로 명시
${PYTHON} ${BRIDGE} placement_report.jsonl \
  --candidates entity_candidates.jsonl \
  --entity-dir 01_ontology-data/data/ontology-entities \
  --output placement_report_enriched.jsonl \
  --threshold 0.80

# PyKEEN 임베딩 (torch 설치 필요)
${PYTHON} ${BRIDGE} placement_report.jsonl \
  --embed --embed-model TransE --threshold 0.70
```

## Ralph ETL 연동

Mode C 출력(`*_enriched.jsonl`)은 Ralph ETL F_SEAL 단계에서 직접 입력으로 사용 가능:

```bash
# enriched 결과를 seal 단계 입력으로
python3 01_ontology-data/tools/ralph_cli.py run \
  --checkpoint F_SEAL \
  --placement-report archive/history/ralph-runs/RUN-001/placement_report_enriched.jsonl
```

## 주의사항

- `target_existing_id`가 없는 항목(new/reject/hold 라벨)은 embed_sim 계산 불가 → 건너뜀
- 엔티티 디렉토리가 없으면 TFIDFEmbedder fit 불가 → embed_sim 재계산 전체 건너뜀
- PyKEEN 모드에서 candidate(그래프 외부)는 유사도 0.0 반환 (그래프 내 엔티티만 임베딩 가능)
