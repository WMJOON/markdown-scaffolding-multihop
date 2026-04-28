# graph-config.yaml 레퍼런스

## 전체 필드

```yaml
# entity_dirs: entity 타입명 → md 파일 디렉토리 (base_dir 기준 상대경로)
entity_dirs:
  competitor: data/competitor-entities
  industry:   data/industry-entities

# relation_map: frontmatter 필드명 → 엣지 relation명
# frontmatter에서 [[wikilink]]가 있는 필드를 엣지로 변환
relation_map:
  target_industry: targets_industry
  related:         related_to

# scalar_node_attrs: 노드 속성으로 보존할 frontmatter 필드
scalar_node_attrs:
  - name
  - title
  - status
  - tags
  - date

# insight_dir: save_insight.py의 기본 출력 디렉토리 (선택)
insight_dir: insights
```

---

## 프리셋 상세

### personal-memory
제텔카스텐 / 개인 지식 베이스 / 일간노트

```yaml
entity_dirs:
  note:    notes
  project: projects
  person:  people
  topic:   topics
  daily:   daily
relation_map:
  related:  related_to
  see_also: related_to
  part_of:  part_of
  mentions: mentions
scalar_node_attrs: [title, date, tags, status, area]
```

### github-docs
GitHub 프로젝트 docs/ 기반

```yaml
entity_dirs:
  guide:     docs/guides
  reference: docs/reference
  tutorial:  docs/tutorials
  adr:       docs/decisions
  concept:   docs/concepts
relation_map:
  see_also:   related_to
  supersedes: supersedes
  implements: implements
  depends_on: depends_on
scalar_node_attrs: [title, status, date, author, tags]
```

### git-repo
일반 Git 레포 (README, docs, wiki, 전체 구조 포함)

```yaml
entity_dirs:
  doc:      docs
  wiki:     wiki
  guide:    docs/guides
  decision: docs/decisions
  readme:   .
relation_map:
  see_also:   related_to
  depends_on: depends_on
  supersedes: supersedes
  related:    related_to
scalar_node_attrs: [title, status, date, author, tags, version]
```

### obsidian-vault
Obsidian vault (entity 노드 + wikilink)

```yaml
entity_dirs:
  note:   notes
  entity: entities
  area:   areas
  source: sources
relation_map:
  related: related_to
  parent:  child_of
scalar_node_attrs: [title, tags, status, created, area]
```

### any-markdown
임의 Markdown 디렉토리 — 최소 설정

```yaml
entity_dirs:
  doc: .
relation_map:
  related: related_to
  see_also: related_to
scalar_node_attrs: [title, tags, date, status]
```

### wiki
GitHub Wiki / 단일 계층 위키

```yaml
entity_dirs:
  page: .
relation_map: {}
scalar_node_attrs: [title, category, tags]
```

---

## entity md 파일 frontmatter 권장 형식

### insight (save_insight.py 출력)
```yaml
---
title: 제목
entity: insight
date: 2026-02-28
tags: [태그1, 태그2]
status: draft
generated: Claude multihop
related_nodes:
  - "[[node-id-1]]"
  - "[[node-id-2]]"
---
```

### 일반 노드 (personal-memory)
```yaml
---
title: 제목
date: 2026-02-28
tags: [태그]
status: active
area: work
related:
  - "[[other-note]]"
---
```

### GitHub docs 페이지
```yaml
---
title: 가이드 제목
status: stable
date: 2026-02-28
author: username
see_also:
  - "[[reference/api]]"
  - "[[concepts/overview]]"
---
```

### git-repo 페이지
```yaml
---
title: 문서 제목
status: draft
date: 2026-02-28
author: username
version: 1.0
depends_on:
  - "[[setup-guide]]"
see_also:
  - "[[api-reference]]"
---
```
