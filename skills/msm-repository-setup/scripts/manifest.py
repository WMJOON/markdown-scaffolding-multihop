"""Scaffold manifest for msm-repository-setup.

Source of truth for the 5-Layer tree that `msm init --apply` produces.
SPEC: msm-repository-setup-SPEC §5.1, §5.3, §6.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal


FileKind = Literal["dir", "file_template", "file_empty", "file_executable"]
MarkerKind = Literal["yaml", "markdown", "shell", "none"]


@dataclass(frozen=True)
class Entry:
    path: str
    kind: FileKind
    template: str | None = None          # relative to templates/
    marker: MarkerKind = "none"
    requires: tuple[str, ...] = field(default_factory=tuple)  # gated options


BASE_DIRS: tuple[str, ...] = (
    "ontology",
    "ontology/Tbox",
    "ontology/Abox",
    "evidence",
    "evidence/md",
    "planning",
    "planning/research",
    "planning/ontology",
    "report",
    "report/paper",
    "docs",
    "docs/guideline",
    "agent-context",
    "agent-context/index",
    "agent-context/workflow",
    "agent-context/workflow/evidence",
    "agent-context/workflow/ontology",
    "agent-context/workflow/maintain",
    "agent-context/workflow/explorer",
    "memory",
    "memory/task-context",
    "memory/task-context/work-log",
    "memory/task-context/decision-history",
    "memory/task-context/troubleshooting",
    "memory/task-context/release-note",
    "memory/ontology-index",
    "harness",
    "harness/tiers",
    "harness/tiers/L0_static",
    "harness/tiers/L1_fixture",
    "harness/tiers/L2_integration",
    "harness/tiers/L3_eval",
    "harness/fixtures",
    "harness/trajectory",
    "harness/reports",
    "harness/oracle",
    ".msm-context",
    ".msm-context/active",
    ".msm-context/archive",
    ".claude",
    ".claude/skills",
    ".claude/hooks",
)


CODEX_DIRS: tuple[str, ...] = (
    ".codex",
    ".codex/skills",
    ".codex/hooks",
)


BASE_FILES: tuple[Entry, ...] = (
    Entry("canonical_root_hub.yaml", "file_template", "canonical_root_hub.yaml", "yaml"),
    Entry("agent-context/index/index.yaml", "file_template", "agent-context/index/index.yaml", "yaml"),
    Entry("agent-context/workflow/index.yaml", "file_template", "agent-context/workflow/index.yaml", "yaml"),
    Entry(
        "agent-context/workflow/evidence/evidence-collection.yaml",
        "file_template",
        "agent-context/workflow/evidence/evidence-collection.yaml",
        "yaml",
    ),
    Entry(
        "agent-context/workflow/ontology/ontology-construction.yaml",
        "file_template",
        "agent-context/workflow/ontology/ontology-construction.yaml",
        "yaml",
    ),
    Entry(
        "agent-context/workflow/maintain/validation.yaml",
        "file_template",
        "agent-context/workflow/maintain/validation.yaml",
        "yaml",
    ),
    Entry(
        "agent-context/workflow/explorer/search-reason.yaml",
        "file_template",
        "agent-context/workflow/explorer/search-reason.yaml",
        "yaml",
    ),
    Entry("docs/index.md", "file_template", "docs/index.md", "markdown"),
    Entry(
        "memory/ontology-index/index.md",
        "file_template",
        "memory/ontology-index/index.md",
        "markdown",
    ),
    Entry("harness/run.sh", "file_executable", "harness/run.sh", "shell"),
    Entry(
        "harness/fixtures/repository_setup_minimal.yaml",
        "file_template",
        "harness/fixtures_repository_setup_minimal.yaml",
        "yaml",
    ),
    Entry("evidence/seeds.jsonl", "file_empty", None, "none"),
)


def domain_entries(cluster: str) -> tuple[Entry, ...]:
    base = f"ontology/Tbox/{cluster}"
    abox = f"ontology/Abox/{cluster}"
    return (
        Entry(f"{base}", "dir"),
        Entry(f"{base}/md", "dir"),
        Entry(f"{abox}", "dir"),
        Entry(f"{abox}/md", "dir"),
        Entry(f"{base}/md/{cluster}__hub.md", "file_template", "domain_hub.md", "markdown"),
        Entry(f"{base}/entities.jsonl", "file_empty"),
        Entry(f"{base}/relations.jsonl", "file_empty"),
        Entry(f"{abox}/instances.jsonl", "file_empty"),
    )


def build_manifest(
    targets: Iterable[str] = ("claude",),
    domain: str | None = None,
) -> list[Entry]:
    out: list[Entry] = []
    out.extend(Entry(p, "dir") for p in BASE_DIRS)
    if "codex" in targets:
        out.extend(Entry(p, "dir") for p in CODEX_DIRS)
    out.extend(BASE_FILES)
    if domain:
        out.extend(domain_entries(domain))
    return out


MARKER_RE = {
    "yaml": "x_msm_generated:",
    "markdown": "msm:generated:file",
    "shell": "msm:generated:file",
}


def has_marker(content: str, marker: MarkerKind) -> bool:
    if marker == "none":
        return True
    needle = MARKER_RE.get(marker)
    return bool(needle and needle in content)
