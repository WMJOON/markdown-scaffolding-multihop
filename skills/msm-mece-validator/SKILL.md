---
name: msm-mece-validator
description: >
  graph-ontology.yaml 온톨로지 설계·검증 전용 스킬. Calibrated Validation 루프(light/medium/deep)로
  클래스·관계 구조의 MECE(상호배제·전체포괄) 품질을 보장한다. Bounded Rationality 원칙에 따라
  depth 파라미터 하나로 LLM 호출 수·라운드·게이트·출력물을 동시에 제어한다.
  트리거: "온톨로지 MECE 검증해줘", "graph-ontology 설계", "MECE 인터뷰", "온톨로지 구조 점검",
  "온톨로지 품질 확인", "classes가 겹치는 것 같아", "KB 구조 MECE로 만들어줘".
  md-scaffolding-design의 companion 스킬.
---

# md-mece-validator

`graph-ontology.yaml` 설계·검증 스킬. depth 파라미터 하나로 리소스 투입량을 조절한다.

## 스크립트

```
scripts/
└── mece_interview.py   # MECE Calibrated Validation 루프
```

상세 채점 공식·depth 비교: `references/depth-guide.md`

