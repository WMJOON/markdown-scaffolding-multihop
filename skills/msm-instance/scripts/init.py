#!/usr/bin/env python3
"""msm-instance init — SQLite runtime.db 초기화 (v0.12.0 skeleton)"""
import argparse, pathlib, sqlite3, sys

DDL = """
CREATE TABLE IF NOT EXISTS market_signal (
    signal_id TEXT PRIMARY KEY,
    value REAL NOT NULL,
    source TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS eca_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT,
    row_json TEXT,
    rule_id TEXT,
    action TEXT,
    fired_at TEXT DEFAULT (datetime('now'))
);
"""

def main():
    ap = argparse.ArgumentParser(description="msm-instance init")
    ap.add_argument("--target", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    target = pathlib.Path(args.target)
    instance_dir = target / "instance"
    db_path = instance_dir / "runtime.db"
    snapshots_dir = instance_dir / "snapshots"

    print(f"[msm-instance init] target={target}")
    print(f"  runtime.db  → {db_path}")
    print(f"  snapshots/  → {snapshots_dir}")

    if not args.apply:
        print("[dry-run] --apply 없이 실행 — 파일을 생성하지 않습니다.")
        return

    instance_dir.mkdir(parents=True, exist_ok=True)
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.executescript(DDL)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.commit()
    conn.close()
    print("[msm-instance init] OK")

if __name__ == "__main__":
    main()
