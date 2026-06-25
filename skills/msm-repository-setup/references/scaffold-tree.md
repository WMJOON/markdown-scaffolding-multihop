# Scaffold Tree

`msm init --apply`가 생성하는 최소 트리. SPEC §5.1 / §5.3.

```text
<repo-root>/
├── ontology/
│   ├── Tbox/
│   │   └── {cluster}/
│   │       ├── md/{cluster}__hub.md
│   │       ├── entities.jsonl
│   │       └── relations.jsonl
│   └── Abox/
│       └── {cluster}/
│           ├── md/
│           └── instances.jsonl
├── evidence/
│   ├── md/
│   └── seeds.jsonl
├── planning/{research,ontology}/
├── report/paper/
├── docs/{index.md,guideline/}
├── agent-context/
│   ├── index/index.yaml
│   └── workflow/
│       ├── index.yaml
│       ├── evidence/evidence-collection.yaml
│       ├── ontology/ontology-construction.yaml
│       ├── maintain/validation.yaml
│       └── explorer/search-reason.yaml
├── memory/
│   ├── task-context/{work-log,decision-history,troubleshooting,release-note}/
│   └── ontology-index/index.md
├── harness/
│   ├── run.sh
│   ├── tiers/{L0_static,L1_fixture,L2_integration,L3_eval}/
│   ├── fixtures/
│   └── trajectory/
├── .claude/{skills,hooks}/
├── .codex/{skills,hooks}/         # --targets에 codex 포함 시
└── canonical_root_hub.yaml
```

domain 없이 init하면 `domains: []`인 빈 hub만 생성된다.
