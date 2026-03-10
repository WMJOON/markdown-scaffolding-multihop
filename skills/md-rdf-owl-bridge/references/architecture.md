# rdf-owl-bridge — 아키텍처 상세

## 패키지 구조

```
<BRIDGE_DIR>/
├── __main__.py              # CLI 진입점 (argparse)
├── router.py                # 모드 자동 감지 (Mode enum)
├── requirements.txt         # rdflib, numpy, pyyaml, scipy
├── rdf-bridge-config.yaml   # 프로젝트별 설정 (선택, 없으면 generic 모드)
├── .venv/                   # Python 가상환경
├── core/
│   ├── rdf_bridge_config.py # config 로더 (BridgeConfig 싱글턴)
│   ├── triple_graph.py      # rdflib 래퍼 + config 기반 네임스페이스/매핑
│   ├── md_to_triple.py      # MD frontmatter → TripleGraph
│   ├── triple_to_md.py      # TripleGraph → MD 파일 출력
│   └── jsonl_io.py          # JSONL I/O 공통 유틸리티
├── modes/
│   ├── import_mode.py       # Mode A: OWL → MD
│   ├── export_mode.py       # Mode B: MD → Triple + 리포트
│   └── placement_mode.py    # Mode C: embed_sim 재계산
└── embed/
    └── kg_embed.py          # TFIDFEmbedder + PyKEENEmbedder
```

## 프로젝트 설정: rdf-bridge-config.yaml

**이 파일만 만들면 됩니다. Python 코드 수정 불필요.**

```yaml
# rdf-bridge-config.yaml  →  BRIDGE_DIR 루트에 배치
namespace_base: "http://your-project.io/"

entity_types:
  - name: Concept       # entity_type 이름
    layer: semantic     # ontology_layer (optional, default: "general")
    dir: Concept        # 출력 디렉토리명 (optional, default: name)
  - name: Instance
    layer: physical
    dir: Instance
  # ...
```

**config가 없으면 generic 모드:**
- namespace: `http://rdf-bridge.local/`
- entity_type: OWL Class URI 로컬명 그대로 사용
- dir: entity_type과 동일
- layer: "general"

즉, config 없이도 어떤 OWL 파일이든 Import/Export/Placement가 동작합니다.

## 설정 탐색 순서

1. `BRIDGE_DIR/rdf-bridge-config.yaml`
2. `cwd/rdf-bridge-config.yaml`
3. 없으면 generic 기본값

## 네임스페이스 구조 (runtime 결정)

```python
# config.namespace_base = "http://your-project.io/"
ONTO   = Namespace("http://your-project.io/ontology/")
ENTITY = Namespace("http://your-project.io/entity/")
REL    = Namespace("http://your-project.io/relation/")
```

## BridgeConfig 로더 (`core/rdf_bridge_config.py`)

```python
cfg = get_config()           # 싱글턴, 최초 1회만 파일 로드
cfg.namespace_base           # → "http://..."
cfg.layer_map                # → {"TypeName": "semantic", ...}
cfg.dir_map                  # → {"TypeName": "DirName", ...}
```

## TripleGraph 주요 API

```python
class TripleGraph:
    def add_entity(self, entity_id, entity_type, label_en, label_ko=None): ...
    def add_relation(self, subject_id, relation_type, object_id, confidence=1.0): ...
    def iter_entities(self) -> Iterator[tuple[uri, eid, etype]]: ...
    def iter_relations(self) -> Iterator[tuple[s_id, p_local, o_id]]: ...
    def entity_exists(self, entity_id) -> bool: ...
    def get_label_en(self, entity_id) -> str: ...
    def serialize(self, fmt="turtle") -> str: ...
    def __len__(self) -> int: ...
```

미등록 entity_type은 `ONTO[entity_type]`으로 자동 생성 → 어떤 타입이든 처리 가능.

## 라우팅 로직 (`router.py`)

```
입력 경로
├── 파일 + RDF 확장자(.ttl/.owl/.rdf 등) → Mode.IMPORT
├── 파일 + 이름 starts_with("placement") + .jsonl → Mode.PLACEMENT
├── 디렉토리 → Mode.EXPORT
└── 그 외 → ValueError
```

## KG Embedding (`embed/kg_embed.py`)

### TFIDFEmbedder (기본, 추가 설치 불필요)

```
fit(graph) → vocab + TF-IDF 행렬 (L2 정규화)
encode(text) → TF-IDF 벡터
top_k(text, k) → 상위 k개 (np.argsort)
```

### PyKEENEmbedder (선택, torch+pykeen 필요)

```
fit(graph) → pykeen.pipeline() → 학습된 model
embed(entity_id) → numpy 벡터
cosine_similarity_to(entity_id) → 유사 엔티티 목록
```

### build_embedder() 폴백

```python
if model_name == "tfidf": return TFIDFEmbedder
# 그 외: PyKEEN 시도 → 실패 시 TF-IDF 폴백
```

## MD → Triple 변환 규칙 (`core/md_to_triple.py`)

```
frontmatter: entity_id, entity_type, label_en, label_ko → add_entity()
relations[].target: "[[EntityType/entity_id]]" → wikilink 파싱 → add_relation()
```

feature_text (TF-IDF 입력용):
```
"{entity_type} {label_en} {label_ko} {aliases} {rel_type target...}"
```

## Triple → MD 변환 (`core/triple_to_md.py`)

```
iter_entities()
  → RDFS label 단일패스 en/ko 분리
  → config.dir_map.get(etype, etype) → 출력 디렉토리
  → config.layer_map.get(etype, "general") → ontology_layer
  → YAML frontmatter → {out_dir}/{dir}/{entity_id}.md
```

## OWL → entity_type 추론 (`infer_entity_type`)

```
1. config.entity_types 역매핑 (URI → 등록된 타입명)
2. 없으면 URI 로컬명 그대로 사용
```

하드코딩 휴리스틱 없음 — config에 없는 타입은 URI에서 자동 추출.

## OWL 관계 매핑 (`modes/import_mode.py`)

| OWL | 내부 rel_type |
|-----|-------------|
| rdfs:subClassOf | subclass_of |
| owl:equivalentClass | equivalent_to |
| owl:disjointWith | disjoint_with |
| skos:broader | subclass_of |
| skos:narrower | has_subclass |
| skos:related | related_to |
| skos:exactMatch | equivalent_to |
| owl:sameAs | equivalent_to |

## JSONL I/O (`core/jsonl_io.py`)

```python
load_jsonl(path)              # 전체 로드 → list[dict]
save_jsonl(records, path)     # 전체 저장
write_jsonl_stream(items, path)  # 스트리밍 (대용량)
```
