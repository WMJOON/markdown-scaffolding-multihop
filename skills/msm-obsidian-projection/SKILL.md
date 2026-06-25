---
name: msm-obsidian-projection
version: "0.13.4"
description: |
  Legacy alias for `msm-explain`.
  Obsidian/Base output remains supported as a compatibility target, but the
  canonical skill identity is now the provider-neutral explain layer.
triggers:
  - "msm-obsidian-projection"
  - "obsidian projection"
  - "DuckDB → Obsidian"
---

# msm-obsidian-projection (legacy)

`msm-obsidian-projection` is retained for backward compatibility.
The canonical skill is now `msm-explain`.

Migration:

| Legacy | Canonical |
|--------|-----------|
| `msm-obsidian-projection run` | `msm-explain run` |
| `obsidian-projection/` | `ontology/explain/` |
| `instance/snapshots/` | `record-archive/snapshots/` |

New workflows should route to `msm-explain`.
