# module.graph-build

## 목적

Markdown 파일 → NetworkX DiGraph 변환 정책을 정의한다.

## 파싱 규칙

1. **frontmatter**: `---...---` YAML 블록에서 추출
2. **본문**: frontmatter 이후 전체 텍스트
3. **node ID**: 파일 stem (확장자 제거), NFC 정규화 필수

## NFC 정규화

macOS HFS+는 NFD, Python 문자열은 NFC. 한글 파일명 비교 시 반드시 정규화.

```python
unicodedata.normalize("NFC", filename_stem)
```

## Edge 분류

| 우선순위 | 소스 | relation | field |
|---------|------|----------|-------|
| 1 | frontmatter RELATION_MAP 필드 | 설정값 | 해당 필드명 |
| 2 | 본문 `[[wikilink]]` | `links_to` | `body_wikilink` |
| 3 | 본문 `[text](path.md)` | `links_to` | `body_mdlink` |

규칙: 동일 (src, tgt) 쌍에 이미 edge가 있으면 우선순위 낮은 edge는 추가하지 않는다.

## Config 필드

```yaml
entity_dirs:       # entity 타입 → 디렉토리 경로
relation_map:      # frontmatter 필드명 → relation명
scalar_node_attrs: # 노드 속성으로 보존할 필드 목록
```

## OWL 온톨로지 연동

`graph-ontology.yaml`의 `classes[*].entity_dir`과 `datatype_properties`에서
entity_dirs, scalar_node_attrs를 자동 도출한다.
→ `md-frontmatter-rollup`의 `rollup_engine.py --ontology` 참조
