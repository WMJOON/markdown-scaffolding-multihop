---
name: msm-orchestration
description: |
  MSM(Markdown Scaffolding Multihop) 스킬 팩의 진입점.
  다음 상황에 사용한다:
  (1) MSM 스킬 팩 설치·설치 상태 확인
  (2) 특정 요청을 어떤 MSM 스킬이 처리해야 하는지 판단
  (3) MSM 팩 거버넌스 검증 실행
  팩 정의(required_skills, version 등)는 references/pack_config.json이 단일 소스.
---

# msm-orchestration

팩 정의: [references/pack_config.json](references/pack_config.json)

## 설치

```bash
git clone https://github.com/WMJOON/markdown-scaffolding-multihop.git
cd markdown-scaffolding-multihop
./install.sh
```

## 거버넌스 검증

```bash
python3 ~/.claude/skills/mso-skill-governance/scripts/validate_gov.py \
  --pack-root ~/.claude --pack msm --json
```

## 스킬 라우팅

| 요청 유형 | 담당 스킬 |
|----------|----------|
| KB 데이터 분석 · 인사이트 추출 | `msm-data-analysis` |
| KB 그래프 구조 설계 · 멀티홉 추론 | `msm-kb-graph` |
| KB 노트 재작성 · 구조 유지보수 | `msm-kb-rewrite` |
| MECE 검증 · 온톨로지 구조 점검 | `msm-mece-validator` |
| Obsidian 파일 · 폴더 CLI 조작 | `msm-obsidian-cli` |
| Evidence ETL · Rollup 집계 | `msm-ralph-etl` |
| RDF/OWL 온톨로지 브릿지 | `msm-rdf-owl-bridge` |
