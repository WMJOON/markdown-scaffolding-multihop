---
name: msm-instance
version: "0.13.4"
description: |
  Legacy alias for `msm-record-archive`.
  Use `msm-record-archive` for record archive, runtime DB, events, derived
  records, snapshots, and archive-time semantics.
triggers:
  - "msm-instance"
  - "instance DB 초기화"
  - "instance insert"
  - "instance query"
---

# msm-instance (legacy)

`msm-instance` is retained for backward compatibility.
The canonical skill is now `msm-record-archive`.

Migration:

| Legacy | Canonical |
|--------|-----------|
| `instance/runtime.db` | `record-archive/runtime/runtime.db` |
| `instance/snapshots/` | `record-archive/snapshots/` |
| `msm-instance <command>` | `msm-record-archive <command>` |

All new workflows should route to `msm-record-archive`.
