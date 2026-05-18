---
name: msm-repository-setup
description: |-
  MSM v1.0.0 repository setup Fat Skill.
  Creates and validates the 5-layer MSM KB scaffold: ontology, evidence, workflow,
  memory, harness, docs, canonical_root_hub.yaml, and workflow templates.
  Triggers: "msm init", "MSM v1 repo setup", "repository setup",
  "canonical hub scaffold", "workflow template scaffold".
---

# msm-repository-setup

`msm-repository-setup` bootstraps an MSM v1.0.0 KB project.

It is the implementation home for `msm init`.

## Protocol

### DESIGN

Confirm:

- target directory
- KB name
- optional domain
- mode: `dry-run`, `apply`, or `validate-only`
- whether skill links should be installed

Default mode is `dry-run`.

### EXECUTE

Use the local CLI:

```bash
python3 scripts/msm_init.py --target ./my-kb --domain ai_agent --dry-run
python3 scripts/msm_init.py --target ./my-kb --domain ai_agent --apply --yes
python3 scripts/msm_init.py --target ./my-kb --validate-only
```

Harness-compatible entrypoint:

```bash
harness/run.sh --skill msm-repository-setup --tier L0 --mode validate-only --target ./my-kb
```

### EVALUATE

Report:

- created files
- skipped files
- conflicts
- readiness score
- whether a HITL gate is required

## Safety

- Dry-run is the default.
- Existing non-generated files are never overwritten.
- Generated files are updated only when they contain an MSM generated marker.
- `canonical_root_hub.yaml` is locked by default.
- Skill links are not installed unless `--with-skill-links` is explicitly provided.

## Files

| Path | Purpose |
|------|---------|
| `scripts/msm_init.py` | Main `msm init` implementation |
| `harness/run.sh` | L0 harness wrapper |
| `references/scaffold-tree.md` | Scaffold contract summary |
| `fixtures/minimal_init_plan.yaml` | Minimal fixture |

