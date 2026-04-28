# Obsidian 폴더 계층 구조 패턴

복잡한 지식 그래프(온톨로지, 멀티홉 KB 등)를 Obsidian에 구성할 때
그래프 뷰와 파일 트리 가시성을 보장하는 패턴.

## 핵심 원칙: 폴더 레벨마다 대표 `.md` 파일

Obsidian 그래프는 `.md` 파일만 노드로 인식한다. 폴더 자체는 노드가 아니므로,
**각 폴더 레벨에 해당 레벨을 대표하는 허브 파일**이 있어야 그래프·파일 트리에서 보인다.

## 표준 3단계 허브-리프 구조

```
{Domain}/
├── {Domain}.md              ← L0 허브 (최상위, 전체 연결)
├── {category-a}.md          ← L1 카테고리 허브 (폴더 밖!)
├── {category-a}/            ← L1 하위 폴더
│   ├── {item}__a1.md        ← L2 개별 항목
│   └── {item}__a2.md
├── {category-b}.md          ← L1 카테고리 허브
└── {category-b}/
    └── {item}__b1.md
```

**L1 허브 파일 위치 규칙 (자주 틀리는 부분)**

```
❌ {Domain}/{category}/{category}.md   ← L1 허브가 폴더 안에 묻힘
✅ {Domain}/{category}.md              ← L1 허브는 폴더 밖(같은 레벨)
✅ {Domain}/{category}/item.md         ← L2 항목은 폴더 안
```

L1 허브가 하위 폴더 안에 들어가면 그래프에서 L2 항목과 같은 레벨로 평탄화되어
계층이 보이지 않는다.

## 양방향 wikilink 패턴

그래프에서 위→아래 방향이 보이려면 허브가 자식 링크를 명시적으로 포함해야 한다.

| 레벨 | 파일 | 포함해야 할 링크 |
|------|------|----------------|
| L0 허브 | `{Domain}.md` | `- [[{category-a}]]`, `- [[{category-b}]]` (모든 L1 허브) |
| L1 허브 | `{category}.md` | `- [[{item}__a1]]`, `- [[{item}__a2]]` (모든 L2 항목) |
| L2 항목 | `{item}.md` | frontmatter `parent: "[[{category}]]"` (위 방향) |

## frontmatter 계층 스키마

```yaml
# L0 허브
level: L0
tags: [hub, L0]

# L1 카테고리 허브
level: L1
parent: "[[{Domain}]]"
tags: [hub, L1]

# L2 개별 항목
level: L2
parent: "[[{category}]]"
tags: [L2]
```

## 구조 검증 bash 패턴

```bash
BASE="path/to/{Domain}"

# 레벨 분포 확인 (L0:1, L1:N, L2:M 이어야 함)
grep -rh "^level:" "$BASE" | sort | uniq -c

# L0 허브가 모든 L1 허브를 링크하는지 확인
grep "^\- \[\[" "$BASE/{Domain}.md"

# L1 허브가 자식 항목을 링크하는지 확인
grep "^\- \[\[" "$BASE/{category}.md"

# L0 폴더 직속에 항목 파일이 없는지 확인 (허브 파일만 있어야 함)
ls "$BASE/"*.md
```

**완료 기준:** L0 폴더 직속에는 `{Domain}.md`(L0)와 L1 허브 파일만 존재,
항목 파일은 하위 폴더 안에만 위치.

## md-graph-multihop 연동 (md-scaffolding-design)

이 계층 구조를 `md-graph-multihop`으로 RAG 인덱싱할 때는
`md-scaffolding-design`의 `obsidian-vault` 프리셋을 아래와 같이 확장한다.

### graph-config.yaml

```yaml
entity_dirs:
  # 도메인 루트를 지정하면 L0·L1·L2 파일이 모두 인덱싱됨
  {domain}: path/to/{Domain}

relation_map:
  # frontmatter의 parent: "[[...]]" 필드 → child_of 엣지
  parent: child_of

scalar_node_attrs: [level, title, tags, status]
```

`parent: "[[...]]"` 단일 필드를 쓰는 이유: `md-scaffolding-design`의 `relation_map`은
`fieldName: relationName` 형식의 flat 매핑만 지원하므로, 중첩 구조(`relations:` 리스트)는
엣지로 변환되지 않는다.

### 레이어 역할 요약

| 레이어 | 역할 |
|--------|------|
| Obsidian 그래프 뷰 | hub `.md` 파일의 `[[wikilink]]`로 시각적 계층 표현 |
| md-graph-multihop | `parent: "[[...]]"` → `child_of` 엣지로 RAG 추론에 활용 |
