# msm-repository-setup Core

## Responsibility

Create and validate the MSM v1.0.0 repository scaffold.

This skill owns setup-time structure only. It does not create real ontology content beyond optional starter hub records.

## Required Scaffold

```text
ontology/
evidence/
planning/
report/
docs/
workflow/
memory/
harness/
.claude/
.codex/
canonical_root_hub.yaml
```

## Modes

| Mode | Behavior |
|------|----------|
| `dry-run` | Plan only. No filesystem writes. |
| `apply` | Create missing directories and generated files. |
| `validate-only` | Validate an existing target. No writes except optional trajectory when called through harness. |

## HITL

HITL is required for:

- non-generated file overwrite
- locked canonical hub mutation
- broken symlink replacement
- existing venv mutation
- skill link path collision

