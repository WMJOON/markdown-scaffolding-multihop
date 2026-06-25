#!/usr/bin/env python3
"""msm-explain list — generated 파일 목록 (v0.12.0 skeleton)"""
import argparse, pathlib, sys

def main():
    ap = argparse.ArgumentParser(description="msm-explain list")
    ap.add_argument("--target", required=True)
    args = ap.parse_args()

    target = pathlib.Path(args.target)
    projection_dir = target / "ontology" / "explain"

    print(f"[msm-explain list] target={target}")

    if not projection_dir.exists():
        print(f"[WARNING] ontology/explain/ 디렉토리가 없습니다: {projection_dir}")
        return

    domains = [d for d in projection_dir.iterdir() if d.is_dir()]
    if not domains:
        print(f"[WARNING] domain 디렉토리가 없습니다.")
        return

    for domain_dir in sorted(domains):
        md_files = list(domain_dir.glob("*.md"))
        base_files = list(domain_dir.glob("*.base.json"))
        print(f"\n{domain_dir.name}:")
        print(f"  MD files: {len(md_files)}")
        for md_file in sorted(md_files)[:5]:
            print(f"    - {md_file.name}")
        if len(md_files) > 5:
            print(f"    ... and {len(md_files) - 5} more")
        print(f"  Base manifests: {len(base_files)}")
        for base_file in sorted(base_files):
            print(f"    - {base_file.name}")

if __name__ == "__main__":
    main()
