#!/usr/bin/env python3
"""ID generation utilities for msm-ontology.

Provides:
- snake_case conversion
- entity / relation / instance id generation
- collision resolution (suffix _2, _3, ...)
"""

from __future__ import annotations

import re


def to_snake(label: str) -> str:
    """Convert a label to snake_case.

    'AI Agent' -> 'ai_agent'
    'some-Thing Here' -> 'some_thing_here'
    """
    # Replace non-alphanumeric with underscore
    s = re.sub(r"[^a-zA-Z0-9]+", "_", label.strip())
    s = s.strip("_").lower()
    return s or "unknown"


def make_entity_id(label: str, existing_ids: set[str] | None = None) -> str:
    """Return a unique entity id for the given label."""
    base = f"entity:{to_snake(label)}"
    return _resolve_collision(base, existing_ids or set())


def make_instance_id(label: str, existing_ids: set[str] | None = None) -> str:
    """Return a unique instance id for the given label."""
    base = f"instance:{to_snake(label)}"
    return _resolve_collision(base, existing_ids or set())


def make_relation_id(
    source_id: str,
    predicate: str,
    target_id: str,
    existing_ids: set[str] | None = None,
) -> str:
    """Return a unique relation id.

    rel:<src_local>:<predicate>:<tgt_local>
    where src_local = source_id minus 'entity:' prefix, first word only.
    """
    src_local = _local_part(source_id)
    tgt_local = _local_part(target_id)
    pred = to_snake(predicate)
    base = f"rel:{src_local}:{pred}:{tgt_local}"
    return _resolve_collision(base, existing_ids or set())


def _local_part(entity_id: str) -> str:
    """Extract local part: 'entity:ai_agent' -> 'ai_agent'."""
    for prefix in ("entity:", "instance:"):
        if entity_id.startswith(prefix):
            return entity_id[len(prefix):]
    return entity_id


def _resolve_collision(base: str, existing: set[str]) -> str:
    if base not in existing:
        return base
    counter = 2
    while True:
        candidate = f"{base}_{counter}"
        if candidate not in existing:
            return candidate
        counter += 1
