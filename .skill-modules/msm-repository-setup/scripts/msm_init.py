#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import stat
import sys
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    yaml = None


GENERATED_MARKER = "msm:generated:file skill=\"msm-repository-setup\" version=\"1.0.0\""

BASE_DIRS = [
    "ontology/Tbox",
    "ontology/Abox",
    "evidence/md",
    "planning/research",
    "planning/ontology",
    "report/paper",
    "report/maintenance",
    "report/explorer",
    "docs/guideline",
    "workflow/evidence",
    "workflow/ontology",
    "workflow/maintain",
    "workflow/explorer",
    "memory/task-context/work-log",
    "memory/task-context/decision-history",
    "memory/task-context/troubleshooting",
    "memory/task-context/release-note",
    "memory/ontology-index",
    "harness/tiers/L0_static",
    "harness/fixtures",
    "harness/trajectory",
    ".claude/skills",
    ".claude/hooks",
    ".codex/skills",
    ".codex/hooks",
]

REQUIRED_FILES = [
    "canonical_root_hub.yaml",
    "workflow/index.yaml",
    "harness/run.sh",
    "memory/ontology-index/index.md",
    "docs/index.md",
]

ALLOWED_TOOLS = {
    "evidence": {"msm-evidence"},
    "ontology": {"msm-ontology"},
    "maintain": {"msm-maintain"},
    "explorer": {"msm-semantic-search", "msm-graph-reasoning"},
}


def utc_date():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def slug_label(slug):
    return " ".join(part.capitalize() for part in slug.split("_"))


def read_text(path):
    return path.read_text(encoding="utf-8")


def write_text(path, text, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def has_generated_marker(path):
    if not path.exists() or not path.is_file():
        return False
    try:
        return GENERATED_MARKER in read_text(path) or "x_msm_generated:" in read_text(path)
    except UnicodeDecodeError:
        return False


def canonical_hub_template(domain):
    if domain:
        label = slug_label(domain)
        domains = f"""  - name: {domain}
    label: "{label}"
    root_hub: "ontology/Tbox/{domain}/md/{domain}__hub.md"
    description: "{label} ontology cluster"
    status: draft
    owner: null
    created_at: "{utc_date()}"
    updated_at: "{utc_date()}"
"""
    else:
        domains = ""
    domains_block = domains if domains else "  []\n"
    return f"""version: "1.0"
locked: true

domains:
{domains_block}
scan:
  include:
    - "ontology/Tbox/**/*.md"
    - "ontology/Abox/**/*.md"
  exclude:
    - "ontology/**/_*.md"
    - "ontology/**/.*/**"
  orphan_exit_code: 1

sync:
  structural_ssot: jsonl
  projection_target: md
  auto_apply_md_to_jsonl: false

x_msm_generated:
  skill: msm-repository-setup
  version: "1.0.0"
"""


def docs_index_template(name):
    return f"""<!-- {GENERATED_MARKER} -->

# {name}

## Structure

- `ontology/`
- `evidence/`
- `workflow/`
- `memory/`
- `harness/`
"""


def workflow_index_template():
    return """version: "1.0"

workflows:
  - id: evidence.collection.default
    path: workflow/evidence/evidence-collection.yaml
    category: evidence
    kind: single
    tool: msm-evidence
    status: draft

  - id: ontology.construction.default
    path: workflow/ontology/ontology-construction.yaml
    category: ontology
    kind: single
    tool: msm-ontology
    status: draft

  - id: maintain.validation.default
    path: workflow/maintain/validation.yaml
    category: maintain
    kind: single
    tool: msm-maintain
    status: draft

  - id: explorer.search_reason.default
    path: workflow/explorer/search-reason.yaml
    category: explorer
    kind: pipeline
    status: draft
"""


def evidence_workflow_template():
    return """version: "1.0"
id: evidence.collection.default
name: Evidence Collection Default
category: evidence
kind: single
tool: msm-evidence
mode: dry-run
status: draft

inputs:
  sources: []
  target_cluster: null
  chunking:
    strategy: semantic
    max_chars: 3000

outputs:
  seeds: evidence/seeds.jsonl
  notes: evidence/md/

runtime:
  tier: L1
  timeout_seconds: 900
  max_concurrency: 1

governance:
  hitl_required: false
  max_retry: 1
  oracle: evidence_seed_readiness
  oracle_threshold: 0.85
  cost_budget:
    tokens: 20000
    seconds: 900
    power_wh: null
"""


def ontology_workflow_template(domain):
    target = domain if domain else None
    target_yaml = "null" if target is None else target
    return f"""version: "1.0"
id: ontology.construction.default
name: Ontology Construction Default
category: ontology
kind: single
tool: msm-ontology
mode: dry-run
status: draft

inputs:
  source_seeds: evidence/seeds.jsonl
  target_cluster: {target_yaml}
  strategy: bottom-up

outputs:
  entity_plan: ".msm-context/active/${{run_id}}/entity-plan.jsonl"
  relation_plan: ".msm-context/active/${{run_id}}/relation-plan.jsonl"

runtime:
  tier: L1
  timeout_seconds: 900
  max_concurrency: 1

governance:
  hitl_required: true
  max_retry: 1
  oracle: ontology_plan_readiness
  oracle_threshold: 0.85
  cost_budget:
    tokens: 30000
    seconds: 900
    power_wh: null
"""


def maintain_workflow_template(domain):
    clusters = f"\n    - {domain}" if domain else " []"
    return f"""version: "1.0"
id: maintain.validation.default
name: Maintenance Validation Default
category: maintain
kind: single
tool: msm-maintain
mode: validate-only
status: draft

inputs:
  target_clusters:{clusters}
  checks:
    - orphan
    - stale_projection
    - boundary_violation

outputs:
  report: report/maintenance/validation-report.md

runtime:
  tier: L0
  timeout_seconds: 300
  max_concurrency: 1

governance:
  hitl_required: false
  max_retry: 0
  oracle: maintenance_validation_readiness
  oracle_threshold: 0.90
  cost_budget:
    tokens: 0
    seconds: 300
    power_wh: null
"""


def explorer_workflow_template(domain):
    clusters = f"\n    - {domain}" if domain else " []"
    return f"""version: "1.0"
id: explorer.search_reason.default
name: Search Then Reason
category: explorer
kind: pipeline
mode: dry-run
status: draft

inputs:
  query: null
  target_clusters:{clusters}
  max_hops: 3

pipeline:
  - step_id: retrieve
    tool: msm-semantic-search
    action: retrieve
    inputs:
      query: "${{inputs.query}}"
      target_clusters: "${{inputs.target_clusters}}"
    outputs:
      results: ".msm-context/active/${{run_id}}/retrieve.results.jsonl"

  - step_id: multihop
    tool: msm-graph-reasoning
    action: multihop
    depends_on:
      - retrieve
    inputs:
      candidates: "${{steps.retrieve.outputs.results}}"
      max_hops: "${{inputs.max_hops}}"
    outputs:
      report: ".msm-context/active/${{run_id}}/multihop.report.md"

outputs:
  report: report/explorer/search-reason-report.md

runtime:
  tier: L1
  timeout_seconds: 900
  max_concurrency: 1

governance:
  hitl_required: false
  max_retry: 1
  oracle: explorer_answer_readiness
  oracle_threshold: 0.80
  cost_budget:
    tokens: 30000
    seconds: 900
    power_wh: null
"""


def harness_run_template():
    return """#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT_DIR/harness/tiers/L0_static/validate_repository_setup.py"

python3 "$SCRIPT" --root "$ROOT_DIR" "$@"
"""


def validator_template():
    return """#!/usr/bin/env python3
import argparse
import json
import pathlib
import sys

try:
    import yaml
except ImportError:
    yaml = None

REQUIRED = [
    "canonical_root_hub.yaml",
    "workflow/index.yaml",
    "harness/run.sh",
    "memory/ontology-index/index.md",
    "docs/index.md",
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args, _ = parser.parse_known_args()
    root = pathlib.Path(args.root).resolve()
    errors = []
    if yaml is None:
        errors.append("PyYAML is not installed")
    for rel in REQUIRED:
        if not (root / rel).exists():
            errors.append(f"missing: {rel}")
    if yaml and (root / "canonical_root_hub.yaml").exists():
        hub = yaml.safe_load((root / "canonical_root_hub.yaml").read_text())
        if hub.get("version") != "1.0":
            errors.append("canonical hub version must be 1.0")
        if hub.get("sync", {}).get("structural_ssot") != "jsonl":
            errors.append("structural_ssot must be jsonl")
    event = {"event_type":"repository_setup_readiness","score": 1.0 if not errors else 0.0, "gate_passed": not errors, "errors": errors}
    print(json.dumps(event, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    sys.exit(main())
"""


def readme_template(title):
    return f"# {title}\n\nGenerated MSM v1.0.0 scaffold slot.\n"


def domain_files(domain):
    if not domain:
        return {}
    label = slug_label(domain)
    return {
        f"ontology/Tbox/{domain}/md/{domain}__hub.md": f"""---
id: hub:{domain}
label: {label} Hub
cluster: {domain}
layer: Tbox
status: draft
generated_from: canonical_root_hub.yaml
---

# {label} Hub

<!-- msm:generated:start source="canonical_root_hub.yaml" -->
Canonical cluster: `{domain}`
<!-- msm:generated:end -->
""",
        f"ontology/Tbox/{domain}/entities.jsonl": "",
        f"ontology/Tbox/{domain}/relations.jsonl": "",
        f"ontology/Abox/{domain}/instances.jsonl": "",
    }


def file_templates(name, domain):
    templates = {
        "canonical_root_hub.yaml": canonical_hub_template(domain),
        "docs/index.md": docs_index_template(name),
        "docs/guideline/README.md": readme_template("guideline"),
        "workflow/index.yaml": workflow_index_template(),
        "workflow/evidence/evidence-collection.yaml": evidence_workflow_template(),
        "workflow/ontology/ontology-construction.yaml": ontology_workflow_template(domain),
        "workflow/maintain/validation.yaml": maintain_workflow_template(domain),
        "workflow/explorer/search-reason.yaml": explorer_workflow_template(domain),
        "memory/ontology-index/index.md": f"<!-- {GENERATED_MARKER} -->\n\n# Ontology Index\n",
        "memory/task-context/work-log/README.md": readme_template("work-log"),
        "memory/task-context/decision-history/README.md": readme_template("decision-history"),
        "memory/task-context/troubleshooting/README.md": readme_template("troubleshooting"),
        "memory/task-context/release-note/README.md": readme_template("release-note"),
        "planning/research/README.md": readme_template("research"),
        "planning/ontology/README.md": readme_template("ontology planning"),
        "report/paper/README.md": readme_template("paper"),
        "harness/run.sh": harness_run_template(),
        "harness/tiers/L0_static/validate_repository_setup.py": validator_template(),
        "harness/fixtures/minimal_init_plan.yaml": f'version: "1.0"\ntarget: "."\ndomain: {domain if domain else "null"}\n',
        "evidence/seeds.jsonl": "",
    }
    templates.update(domain_files(domain))
    return templates


def plan(root, name, domain):
    dirs = list(BASE_DIRS)
    if domain:
        dirs.extend([
            f"ontology/Tbox/{domain}/md",
            f"ontology/Abox/{domain}/md",
        ])
    files = file_templates(name, domain)
    creates, skips, conflicts = [], [], []
    for directory in dirs:
        path = root / directory
        (skips if path.exists() else creates).append(directory + "/")
    for rel in files:
        path = root / rel
        if not path.exists():
            creates.append(rel)
        elif path.is_file() and read_text(path) == files[rel]:
            skips.append(rel)
        elif has_generated_marker(path) or path.stat().st_size == 0:
            skips.append(rel)
        else:
            conflicts.append(rel)
    return {"dirs": dirs, "files": files, "creates": creates, "skips": skips, "conflicts": conflicts}


def apply_plan(root, plan_data, yes):
    if plan_data["conflicts"] and not yes:
        return False
    for directory in plan_data["dirs"]:
        (root / directory).mkdir(parents=True, exist_ok=True)
    for rel, text in plan_data["files"].items():
        path = root / rel
        executable = rel.endswith(".sh") or rel.endswith(".py")
        if path.exists() and not (has_generated_marker(path) or path.stat().st_size == 0):
            continue
        if path.exists() and text == "":
            continue
        write_text(path, text, executable=executable)
    return True


def check_jsonl(path, errors):
    if not path.exists():
        return
    for idx, line in enumerate(read_text(path).splitlines(), start=1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid jsonl {path}:{idx}: {exc}")


def load_yaml(path):
    if yaml is None:
        raise RuntimeError("PyYAML is required")
    return yaml.safe_load(read_text(path))


def validate_workflow(path, errors):
    data = load_yaml(path)
    for key in ["version", "id", "category", "kind", "mode", "status", "inputs", "outputs", "runtime", "governance"]:
        if key not in data:
            errors.append(f"{path}: missing {key}")
    if data.get("version") != "1.0":
        errors.append(f"{path}: version must be 1.0")
    category = data.get("category")
    kind = data.get("kind")
    if kind == "single":
        tool = data.get("tool")
        if tool not in ALLOWED_TOOLS.get(category, set()):
            errors.append(f"{path}: invalid tool {tool}")
    elif kind == "pipeline":
        if "tool" in data:
            errors.append(f"{path}: pipeline must not have top-level tool")
        for step in data.get("pipeline", []):
            if step.get("tool") not in ALLOWED_TOOLS["explorer"]:
                errors.append(f"{path}: invalid pipeline tool {step.get('tool')}")
    else:
        errors.append(f"{path}: invalid kind {kind}")
    gov = data.get("governance", {})
    if "max_retry" not in gov or not isinstance(gov.get("max_retry"), int) or gov.get("max_retry") < 0:
        errors.append(f"{path}: invalid max_retry")


def validate(root):
    errors, warnings = [], []
    if yaml is None:
        errors.append("PyYAML is not installed")
        return errors, warnings
    for directory in BASE_DIRS:
        if not (root / directory).is_dir():
            errors.append(f"missing directory: {directory}")
    for file_path in REQUIRED_FILES:
        if not (root / file_path).is_file():
            errors.append(f"missing file: {file_path}")
    if (root / "canonical_root_hub.yaml").exists():
        hub = load_yaml(root / "canonical_root_hub.yaml")
        if hub.get("version") != "1.0":
            errors.append("canonical_root_hub.yaml: version must be 1.0")
        if hub.get("locked") is not True:
            errors.append("canonical_root_hub.yaml: locked must be true")
        sync = hub.get("sync", {})
        if sync.get("structural_ssot") != "jsonl":
            errors.append("canonical_root_hub.yaml: structural_ssot must be jsonl")
        for domain in hub.get("domains", []) or []:
            root_hub = domain.get("root_hub")
            if root_hub and not (root / root_hub).is_file():
                errors.append(f"canonical_root_hub.yaml: missing root_hub {root_hub}")
    if (root / "workflow/index.yaml").exists():
        index = load_yaml(root / "workflow/index.yaml")
        seen = set()
        for item in index.get("workflows", []):
            workflow_id = item.get("id")
            if workflow_id in seen:
                errors.append(f"workflow/index.yaml: duplicate id {workflow_id}")
            seen.add(workflow_id)
            path = item.get("path")
            if not path or not (root / path).is_file():
                errors.append(f"workflow/index.yaml: missing workflow {path}")
            else:
                validate_workflow(root / path, errors)
    for jsonl in root.glob("**/*.jsonl"):
        check_jsonl(jsonl, errors)
    return errors, warnings


def emit(event):
    print(json.dumps(event, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="MSM v1.0.0 repository setup")
    parser.add_argument("--target", default=".")
    parser.add_argument("--name", default=None)
    parser.add_argument("--domain", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--with-skill-links", action="store_true")
    parser.add_argument("--targets", default="claude,codex")
    args = parser.parse_args()

    root = pathlib.Path(args.target).expanduser().resolve()
    name = args.name or root.name
    mode_count = sum([args.dry_run, args.apply, args.validate_only])
    if mode_count == 0:
        args.dry_run = True
    elif mode_count > 1:
        print("Choose only one mode", file=sys.stderr)
        return 2

    mode = "apply" if args.apply else "validate-only" if args.validate_only else "dry-run"
    plan_data = plan(root, name, args.domain)

    if mode == "apply":
        if args.with_skill_links:
            plan_data["conflicts"].append("skill link installation is not implemented in v1.0.0 beta")
        applied = apply_plan(root, plan_data, args.yes)
        if not applied:
            emit({"event_type": "hitl_request", "requires_manual_confirmation": True, "conflicts": plan_data["conflicts"]})
            return 1

    errors, warnings = validate(root) if mode != "dry-run" else ([], [])
    score = 1.0 if not errors else max(0.0, 1.0 - min(len(errors) * 0.1, 1.0))
    effective_conflicts = plan_data["conflicts"] if mode != "validate-only" else []
    event = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "event_type": "repository_setup_plan" if mode == "dry-run" else "repository_setup_readiness",
        "target": str(root),
        "mode": mode,
        "creates": plan_data["creates"],
        "skips": plan_data["skips"],
        "conflicts": effective_conflicts,
        "score": score,
        "gate_passed": score >= 0.85 and not effective_conflicts,
        "requires_manual_confirmation": bool(effective_conflicts),
        "errors": errors,
        "warnings": warnings,
    }
    emit(event)
    return 0 if event["gate_passed"] or mode == "dry-run" else 1


if __name__ == "__main__":
    sys.exit(main())
