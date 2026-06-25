#!/usr/bin/env python3
"""msm-explain run — DuckDB snapshot → explain Markdown+Base (v0.12.0 skeleton)"""
import argparse, json, pathlib, sys
from datetime import datetime

def main():
    ap = argparse.ArgumentParser(description="msm-explain run")
    ap.add_argument("--target", required=True)
    ap.add_argument("--domain", default="instance")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    target = pathlib.Path(args.target)
    snapshots_dir = target / "record-archive" / "snapshots"
    output_dir = target / "ontology" / "explain" / args.domain

    try:
        import duckdb
    except ImportError:
        print("duckdb 패키지가 필요합니다. pip install duckdb 를 실행해주세요.", file=sys.stderr)
        sys.exit(1)

    try:
        import jinja2
    except ImportError:
        print("jinja2 패키지가 필요합니다. pip install jinja2 를 실행해주세요.", file=sys.stderr)
        sys.exit(1)

    print(f"[msm-explain run] target={target}")
    print(f"  snapshots/ → {snapshots_dir}")
    print(f"  output: ontology/explain/{args.domain}/")

    if not snapshots_dir.exists():
        print(f"[ERROR] snapshots/ 디렉토리가 없습니다: {snapshots_dir}", file=sys.stderr)
        sys.exit(1)

    parquets = list(snapshots_dir.glob("*.parquet"))
    if not parquets:
        print(f"[ERROR] parquet 파일이 없습니다: {snapshots_dir}", file=sys.stderr)
        sys.exit(1)

    conn = duckdb.connect(":memory:")
    latest_parquet = sorted(parquets)[-1]

    try:
        df = conn.execute(f"SELECT * FROM read_parquet('{latest_parquet}')").fetch_df()
    except Exception as e:
        print(f"[ERROR] parquet 읽기 실패: {e}", file=sys.stderr)
        sys.exit(1)

    files_to_create = []
    for idx, row in df.iterrows():
        entity_id = row.get("id", f"entity_{idx}")
        entity_name = row.get("name", "Untitled")
        tags = row.get("tags", "").split(",") if "tags" in row else []

        md_path = output_dir / f"{entity_id}.md"
        base_path = output_dir / f"{entity_id}.base.json"

        files_to_create.append((md_path, base_path, entity_id, entity_name, tags))

    print(f"[dry-run] {len(files_to_create)} 파일을 생성합니다:")
    for md_path, _, eid, ename, _ in files_to_create:
        print(f"  - {md_path.relative_to(target)}")

    if not args.apply:
        print("[dry-run] --apply 없이 실행 — 파일을 생성하지 않습니다.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    template = jinja2.Template("""---
# msm:generated
title: {{ name }}
id: {{ id }}
tags: {{ tags | join(", ") }}
generated_at: {{ timestamp }}
---

<!-- msm:generated -->

# {{ name }}

entity_id: {{ id }}

## Properties

- tags: {{ tags | join(", ") }}
- generated: {{ timestamp }}
""")

    base_entries = []
    for md_path, base_path, entity_id, entity_name, tags in files_to_create:
        if md_path.exists() and "<!-- msm:generated -->" not in md_path.read_text(encoding="utf-8", errors="replace"):
            print(f"[ERROR] generated marker 없는 기존 파일은 덮어쓰지 않습니다: {md_path}", file=sys.stderr)
            sys.exit(2)
        timestamp = datetime.now().isoformat()
        content = template.render(
            name=entity_name,
            id=entity_id,
            tags=tags,
            timestamp=timestamp
        )

        md_path.write_text(content, encoding="utf-8")
        base_entries.append({
            "id": entity_id,
            "title": entity_name,
            "path": f"ontology/explain/{args.domain}/{entity_id}.md",
            "tags": tags
        })

    base_manifest = {
        "version": "1.0.0",
        "name": args.domain,
        "generated_at": datetime.now().isoformat(),
        "entries": base_entries
    }

    base_index_path = output_dir / f"_manifest.base.json"
    base_index_path.write_text(json.dumps(base_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[msm-explain run] OK → {output_dir}")
    print(f"  - {len(base_entries)} MD 파일 생성")
    print(f"  - manifest: {base_index_path.relative_to(target)}")

if __name__ == "__main__":
    main()
