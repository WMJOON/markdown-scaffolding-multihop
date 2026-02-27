"""
rollup_engine.py
OWL 기반 graph-ontology.yaml을 읽어 그래프 엣지를 따라
frontmatter 값을 집계하고 상위 노드에 기록한다.

graph-config.yaml + rollup-config.yaml도 하위 호환으로 지원한다.

사용:
    # OWL 온톨로지 방식 (권장)
    python3 rollup_engine.py --ontology graph-ontology.yaml
    python3 rollup_engine.py --ontology graph-ontology.yaml --dry-run
    python3 rollup_engine.py --ontology graph-ontology.yaml --show-rules
    python3 rollup_engine.py --ontology graph-ontology.yaml --property hasSegment

    # 레거시 방식
    python3 rollup_engine.py
    python3 rollup_engine.py --config graph-config.yaml --rollup rollup-config.yaml
    python3 rollup_engine.py --rule industry_market_size
"""

import sys
import argparse
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Optional

import yaml

# ──────────────────────────────────────────────
# 그래프 빌더 import
# ──────────────────────────────────────────────
REPO_DIR = Path(__file__).parent.parent.parent.parent
LIGHT_SCRIPTS = REPO_DIR / "skills" / "md-graph-multihop" / "scripts"
if str(LIGHT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(LIGHT_SCRIPTS))

from graph_builder import load_config, nfc   # type: ignore
import networkx as nx


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", str(s))


# ──────────────────────────────────────────────
# 온톨로지 로더
# ──────────────────────────────────────────────

ONTOLOGY_NAME   = "graph-ontology.yaml"
ROLLUP_CFG_NAME = "rollup-config.yaml"
GRAPH_CFG_NAME  = "graph-config.yaml"


def _find_file(name: str, start: Path) -> Optional[Path]:
    for d in [start, *start.parents]:
        p = d / name
        if p.exists():
            return p
    return None


def load_ontology(ontology_path: Optional[Path]) -> dict:
    """graph-ontology.yaml 로드"""
    if ontology_path is None:
        ontology_path = _find_file(ONTOLOGY_NAME, Path.cwd())
    if ontology_path is None:
        ontology_path = _find_file(ONTOLOGY_NAME, Path(__file__).parent)
    if ontology_path is None:
        raise FileNotFoundError(
            f"{ONTOLOGY_NAME}을 찾지 못했습니다. "
            "--ontology 옵션으로 경로를 지정하거나 "
            "graph-ontology.yaml을 프로젝트 루트에 생성하세요.\n"
            "예시: cp graph-ontology.example.yaml graph-ontology.yaml"
        )
    with open(ontology_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_legacy_rollup(rollup_path: Optional[Path]) -> dict:
    """rollup-config.yaml (레거시) 로드"""
    if rollup_path is None:
        rollup_path = _find_file(ROLLUP_CFG_NAME, Path.cwd())
    if rollup_path is None:
        return {}
    with open(rollup_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ──────────────────────────────────────────────
# 온톨로지 → 그래프 config + 롤업 규칙 도출
# ──────────────────────────────────────────────

def ontology_to_graph_config(ontology: dict) -> dict:
    """
    graph-ontology.yaml → graph_builder 호환 graph-config dict 도출.
    entity_dirs, relation_map, scalar_node_attrs를 자동 생성한다.
    """
    classes    = ontology.get("classes", {})
    obj_props  = ontology.get("object_properties", {})
    dt_props   = ontology.get("datatype_properties", {})

    entity_dirs = {
        cls_name: cls_def["entity_dir"]
        for cls_name, cls_def in classes.items()
        if "entity_dir" in cls_def
    }

    # datatype_properties 도메인에서 scalar_node_attrs 수집
    scalar_attrs: set[str] = set()
    for prop_name in dt_props:
        scalar_attrs.add(prop_name)
    # graph-ontology에 명시된 scalar_node_attrs도 병합
    scalar_attrs.update(ontology.get("scalar_node_attrs", []))

    # object_properties의 rollup에서 집계 필드도 scalar_attrs에 포함
    for prop_def in obj_props.values():
        for agg in prop_def.get("rollup", []):
            scalar_attrs.add(agg.get("field", ""))
            if agg.get("weight_field"):
                scalar_attrs.add(agg["weight_field"])
    scalar_attrs.discard("")

    return {
        "entity_dirs":       entity_dirs,
        "relation_map":      {},   # wikilink 필드 매핑은 별도 (기존 graph-config 병용 권장)
        "scalar_node_attrs": sorted(scalar_attrs),
    }


def ontology_to_rollup_rules(ontology: dict) -> list[dict]:
    """
    graph-ontology.yaml의 object_properties.rollup 선언 →
    rollup_rules 리스트로 변환 (rollup-config.yaml 포맷 호환).
    """
    obj_props = ontology.get("object_properties", {})
    rules: list[dict] = []

    for prop_name, prop_def in obj_props.items():
        rollup_defs = prop_def.get("rollup", [])
        if not rollup_defs:
            continue

        domain        = prop_def.get("domain", "")
        relation_name = prop_def.get("relation_name", prop_name)

        rules.append({
            "id":            prop_name,
            "description":   prop_def.get("label", f"{prop_name} 롤업"),
            "source_entity": domain,
            "edge_relation": relation_name,
            "direction":     "out",   # domain --[prop]--> range, aggregate range→domain
            "aggregations":  rollup_defs,
        })

    return rules


# ──────────────────────────────────────────────
# 그래프 로더 (ontology 기반 + legacy config 하위 호환)
# ──────────────────────────────────────────────

def load_graph(config_path: Optional[Path],
               ontology: Optional[dict]) -> nx.DiGraph:
    """
    그래프 구축은 graph-config.yaml이 담당한다.
    ontology는 롤업 규칙 도출에만 사용하며 그래프 구조에 개입하지 않는다.

    config_path 미지정 시: graph-config.yaml 자동 탐색.
    graph-config.yaml 없고 ontology만 있으면: ontology에서 entity_dirs를 도출해 빌드.
    """
    from graph_builder import build_graph  # type: ignore

    # Case 1: graph-config.yaml 있음 → 그대로 사용
    if config_path and config_path.exists():
        return build_graph(config_path)

    # Case 2: 자동 탐색
    auto = _find_file(GRAPH_CFG_NAME, Path.cwd())
    if auto:
        return build_graph(auto)

    # Case 3: ontology만 있음 → 임시 config 작성 후 빌드
    if ontology:
        import tempfile, yaml as _yaml
        derived = ontology_to_graph_config(ontology)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as tf:
            _yaml.dump(derived, tf, allow_unicode=True)
            tmp_path = Path(tf.name)
        try:
            G = build_graph(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
        return G

    raise FileNotFoundError(
        "graph-config.yaml 또는 graph-ontology.yaml이 필요합니다."
    )


# ──────────────────────────────────────────────
# Frontmatter 업데이터
# ──────────────────────────────────────────────

def read_fm_body(filepath: Path) -> tuple[dict, str]:
    text = filepath.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("---", 3)
        if end >= 0:
            try:
                fm = yaml.safe_load(text[3:end]) or {}
            except Exception:
                fm = {}
            return fm, text[end + 3:]
    return {}, text


def write_fm(filepath: Path, fm: dict, body: str) -> None:
    fm_str = yaml.dump(fm, allow_unicode=True,
                       default_flow_style=False, sort_keys=False)
    filepath.write_text(f"---\n{fm_str}---{body}", encoding="utf-8")


# ──────────────────────────────────────────────
# 집계 함수
# ──────────────────────────────────────────────

def aggregate(values: list[Any], func: str,
              weights: Optional[list[Any]] = None) -> Optional[float]:
    if func == "count":
        return float(len(values))

    nums, ws = [], []
    for i, v in enumerate(values):
        try:
            n = float(v)
            nums.append(n)
            if weights is not None:
                try:
                    ws.append(float(weights[i]))
                except (TypeError, ValueError, IndexError):
                    ws.append(None)
        except (TypeError, ValueError):
            pass

    if not nums:
        return None

    if func == "sum":
        return sum(nums)
    if func == "avg":
        return sum(nums) / len(nums)
    if func == "max":
        return max(nums)
    if func == "min":
        return min(nums)
    if func == "weighted_avg":
        pairs = [(n, w) for n, w in zip(nums, ws or [None]*len(nums))
                 if w is not None and w != 0]
        if not pairs:
            return None
        tw = sum(w for _, w in pairs)
        return sum(n * w for n, w in pairs) / tw if tw else None

    raise ValueError(f"지원하지 않는 집계 함수: {func}")


# ──────────────────────────────────────────────
# 롤업 실행
# ──────────────────────────────────────────────

def run_rule(G: nx.DiGraph, rule: dict, dry_run: bool) -> list[str]:
    source_entity = rule["source_entity"]
    edge_relation  = rule["edge_relation"]
    direction      = rule.get("direction", "out")
    aggregations   = rule.get("aggregations", [])
    changed: list[str] = []

    source_entity_lower = source_entity.lower()
    source_nodes = [
        (nid, data) for nid, data in G.nodes(data=True)
        if (data.get("type") or "").lower() == source_entity_lower
    ]

    for src_id, src_data in source_nodes:
        if direction == "out":
            neighbors = [
                s for s in G.successors(src_id)
                if G[src_id][s].get("relation") == edge_relation
            ]
        else:  # in
            neighbors = [
                p for p in G.predecessors(src_id)
                if G[p][src_id].get("relation") == edge_relation
            ]

        if not neighbors:
            continue

        source_file = Path(src_data.get("source_file", ""))
        if not source_file.exists():
            print(f"  [경고] 파일 없음: {source_file}")
            continue

        fm, body = read_fm_body(source_file)
        updated  = False

        for agg in aggregations:
            field        = agg["field"]
            func         = agg["func"]
            write_to     = agg["write_to"]
            weight_field = agg.get("weight_field")
            updated_at   = agg.get("updated_at_field")

            values  = [G.nodes[n].get(field) for n in neighbors]
            weights = ([G.nodes[n].get(weight_field) for n in neighbors]
                       if func == "weighted_avg" and weight_field else None)

            result = aggregate(values, func, weights)
            if result is None:
                continue
            result = round(result, 2)
            if result == int(result):
                result = int(result)

            old = fm.get(write_to)
            if old != result:
                fm[write_to] = result
                if updated_at:
                    fm[updated_at] = str(date.today())
                updated = True
                label = nfc(src_data.get("name", src_id))
                print(f"  {label:35s}  {write_to} = {result}  (이전: {old})")

        if updated:
            if not dry_run:
                write_fm(source_file, fm, body)
            changed.append(str(source_file))

    return changed


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OWL 기반 frontmatter rollup 엔진 (graph-ontology.yaml 또는 rollup-config.yaml)"
    )
    # 온톨로지 기반 (권장)
    parser.add_argument("--ontology", "-o", type=Path,
                        help="graph-ontology.yaml 경로 (자동 탐색)")
    # 레거시 호환
    parser.add_argument("--config",  "-c", type=Path,
                        help="graph-config.yaml (레거시)")
    parser.add_argument("--rollup",  "-r", type=Path,
                        help="rollup-config.yaml (레거시)")
    parser.add_argument("--property", "-p",
                        help="실행할 object_property 이름 (생략 시 전체)")
    parser.add_argument("--rule",
                        help="실행할 rule id (레거시 rollup-config용, --property와 동일)")
    parser.add_argument("--dry-run",  action="store_true")
    parser.add_argument("--show-rules", action="store_true",
                        help="도출된 롤업 규칙 목록 출력 후 종료")
    args = parser.parse_args()

    # ── 온톨로지 또는 레거시 config 로드 ──
    ontology: Optional[dict] = None
    rules: list[dict] = []

    try:
        ontology = load_ontology(args.ontology)
        rules = ontology_to_rollup_rules(ontology)
        print(f"온톨로지 로드 완료 "
              f"(클래스 {len(ontology.get('classes',{}))}, "
              f"프로퍼티 {len(ontology.get('object_properties',{}))})")
    except FileNotFoundError:
        # 레거시 rollup-config.yaml fallback
        legacy = load_legacy_rollup(args.rollup)
        rules  = legacy.get("rollup_rules", [])
        if not rules:
            print("[오류] graph-ontology.yaml 또는 rollup-config.yaml이 필요합니다.")
            print("  OWL 방식: cp graph-ontology.example.yaml graph-ontology.yaml")
            sys.exit(1)
        print("레거시 rollup-config.yaml 로드 완료")

    # --property 또는 --rule (별칭)
    filter_id = args.property or args.rule
    if filter_id:
        rules = [r for r in rules if r.get("id") == filter_id]
        if not rules:
            print(f"[오류] '{filter_id}'에 대한 롤업 규칙이 없습니다.")
            sys.exit(1)

    if args.show_rules:
        print("\n[ 도출된 롤업 규칙 ]")
        for r in rules:
            print(f"  {r['id']:30s}  {r.get('description','')}")
            print(f"    source: {r['source_entity']}  relation: {r['edge_relation']}  direction: {r.get('direction','out')}")
            for a in r.get("aggregations", []):
                print(f"    └ {a['field']:20s} --[{a['func']}]--> {a['write_to']}")
        sys.exit(0)

    # ── 그래프 로드 ──
    print("그래프 로딩 중...", end=" ", flush=True)
    G = load_graph(args.config, ontology)
    print(f"완료 ({G.number_of_nodes()}노드 / {G.number_of_edges()}엣지)")

    # ── 규칙 실행 ──
    total: list[str] = []
    for rule in rules:
        rid  = rule.get("id", "?")
        desc = rule.get("description", "")
        print(f"\n▶ {rid}" + (f"  ({desc})" if desc else ""))
        changed = run_rule(G, rule, dry_run=args.dry_run)
        total.extend(changed)

    print(f"\n{'[dry-run] ' if args.dry_run else ''}완료: {len(total)}개 파일 "
          f"{'업데이트 예정' if args.dry_run else '업데이트됨'}")
