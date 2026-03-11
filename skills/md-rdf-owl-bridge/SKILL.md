---
name: md-rdf-owl-bridge
description: >
  RDF/OWL 온톨로지와 MD-frontmatter 기반 지식 그래프 간 양방향 변환 도구.
  MD-frontmatter+wikilink 구조라면 어떤 프로젝트에도 적용 가능.
  세 가지 모드를 자동 감지해 라우팅한다:
  (A) Import: 외부 RDF/OWL(.ttl/.owl/.rdf 등) → MD frontmatter 엔티티 파일,
  (B) Export: MD 엔티티 디렉토리 → Triple JSONL + Turtle + KG 분석 리포트,
  (C) Placement: placement_report.jsonl → embed_sim 재계산 + merge 승격.
  트리거 예시: "RDF 온톨로지 임포트해줘", "Triple로 Export해줘", "OWL 파일 변환해줘",
  "placement embed_sim 보강해줘", "KG 분석 리포트 만들어줘", "rdf-owl-bridge 실행해줘".
---

# md-rdf-owl-bridge

RDF/OWL ↔ MD-frontmatter 지식 그래프 변환 + KG 분석 + placement 보강 패키지.

아키텍처 상세: [references/architecture.md](references/architecture.md)

## 전제 조건

- Python 3.10+, `rdflib>=7.0.0`, `numpy>=1.26.0`, `pyyaml>=6.0`
- Semantic/Hybrid: `sentence-transformers` 추가 필요 (없으면 TF-IDF 자동 폴백)
- PyKEEN(TransE/RotatE/ComplEx): `pykeen`, `torch` 추가 필요 (없으면 TF-IDF 자동 폴백)

```bash
# 1. 스킬의 scripts/ → 프로젝트 tools/rdf-owl-bridge/ 에 복사
cp -r <SKILL_DIR>/scripts/ <프로젝트>/tools/rdf-owl-bridge/

# 2. 가상환경 설치
export BRIDGE_DIR="<프로젝트>/tools/rdf-owl-bridge"
cd ${BRIDGE_DIR} && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 3. (선택) config 복사 후 수정
cp rdf-bridge-config.example.yaml rdf-bridge-config.yaml
```

## 프로토콜

1. **MODE 확인** — 입력 경로로 모드 결정 (또는 `--mode` 명시)
2. **실행** — 명령 확인 후 실행
3. **검증** — 출력 파일 + 통계 보고

## 실행

```bash
PYTHON="${BRIDGE_DIR}/.venv/bin/python"
MAIN="${BRIDGE_DIR}/__main__.py"

${PYTHON} ${MAIN} <file.ttl|.owl|.rdf>           # Mode A: Import
${PYTHON} ${MAIN} <entity_dir> [--embed]          # Mode B: Export
${PYTHON} ${MAIN} <placement_report.jsonl>        # Mode C: Placement
```

## 모드별 입/출력

| 모드 | 입력 | 출력 |
|------|------|------|
| **A Import** | `.ttl`/`.owl`/`.rdf`/`.n3`/`.nt`/`.jsonld`/`.trig` | MD 엔티티 파일 |
| **B Export** | MD 엔티티 디렉토리 | `triples.jsonl`, `entities.jsonl`, `ontology.ttl`, `report.md` |
| **C Placement** | `placement_report.jsonl` | `*_enriched.jsonl`, `placement_enrichment_report.md` |

자동 감지: RDF 확장자 → Import / `placement*.jsonl` → Placement / 디렉토리 → Export

## 공통 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--mode` / `-m` | 자동 감지 | `import` / `export` / `placement` |
| `--output` / `-o` | 자동 결정 | 출력 경로 |
| `--embed` | 비활성 | KG Embedding 활성화 |
| `--embed-model` | `tfidf` | `tfidf` / `semantic` / `hybrid` / `TransE` / `RotatE` / `ComplEx` |
| `--threshold` | `0.80` | Mode C: merge 승격 임계값 |
| `--entity-dir` | 자동 탐색 | MD 엔티티 루트 |
| `--candidates` | 자동 탐색 | Mode C: entity_candidates.jsonl |
| `--verbose` / `-v` | 비활성 | 디버그 로그 |

## 프로젝트 적용

`BRIDGE_DIR/rdf-bridge-config.yaml` 파일 하나로 설정. Python 코드 수정 불필요.

```yaml
namespace_base: "http://your-project.io/"
entity_types:
  - name: Concept
    layer: semantic
    dir: Concept
```

config 없으면 generic 모드 동작 (URI 로컬명 → entity_type, layer="general").

## KG Embedding 백엔드

| 백엔드 | `--embed-model` | 의존성 | 특징 |
|--------|-----------------|--------|------|
| **TF-IDF** | `tfidf` | 없음 (numpy만) | 어휘 겹침 기반 baseline. 의미 구분력 낮음 |
| **Semantic** | `semantic` | `sentence-transformers` | SentenceTransformer(`all-MiniLM-L6-v2`) 의미 임베딩. 그래프 밖 candidate도 처리 가능 |
| **Hybrid** | `hybrid` | `sentence-transformers` + `pykeen`(선택) | 3-tier scoring: Semantic(Tier 1) + PyKEEN 구조(Tier 2). PyKEEN 없으면 Semantic 단독 |
| **PyKEEN** | `TransE`/`RotatE`/`ComplEx` | `pykeen`, `torch` | KG 구조 임베딩. inductive embed로 candidate 근사 지원 |

### Hybrid 3-tier scoring

```
candidate (그래프 外)              target (그래프 內)
     │                                  │
     ├─ feature_text ──→ SentenceTransformer ──→ sem_sim     (Tier 1: 항상)
     │                                  │
     └─ relations[] ──→ inductive embed ────→ struct_sim    (Tier 2: PyKEEN 있을 때)
                                        │
                               w_sem·sem + w_struct·struct = final_sim
                               (struct 불가 시 sem만 사용)
```

| 가중치 | 기본값 | 설명 |
|--------|--------|------|
| `w_sem` | 0.6 | Semantic 유사도 가중치 |
| `w_struct` | 0.4 | Structural 유사도 가중치 (Tier 2 불가 시 0.0으로 재정규화) |

### 폴백 체인

```
hybrid → Semantic 실패 → TF-IDF (ultimate fallback)
hybrid → PyKEEN 실패 → Semantic 단독 (w_struct=0)
semantic → 실패 → TF-IDF
TransE/RotatE/ComplEx → 실패 → TF-IDF
```

## 모드 상세

- Mode A: [references/import.md](references/import.md)
- Mode B: [references/export.md](references/export.md)
- Mode C: [references/placement.md](references/placement.md)
