"""TTL helpers for MSM workflow SSOT.

MSM workflow execution metadata lives in TTL as the source of truth. YAML is
kept as a migration/edit layer for older workflows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MSMWF_URI = "https://msm.dev/ontology/workflow#"
WFOPS_URI = "https://wmjoon.kb/ontology/workflow-ops#"
MSOWF_URI = "https://mso.dev/ontology/workflow#"


def _safe(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-._" else "_" for c in str(value))


def _require_rdflib():
    try:
        from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RuntimeError("TTL workflow support requires rdflib") from exc
    return BNode, Graph, Literal, Namespace, RDF, URIRef


def _scalar(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


def _local_name(value: Any) -> str:
    text = str(value)
    if "#" in text:
        return text.rsplit("#", 1)[1]
    return text.rstrip("/").rsplit("/", 1)[-1]


def _object_value(g: Any, subj: Any, namespace: Any, pred: str) -> Any:
    vals = list(g.objects(subj, namespace[pred]))
    return vals[0].toPython() if vals else None


def _sort_wfops_steps(g: Any, steps: list[Any], namespace: Any) -> list[Any]:
    remaining = set(steps)
    ordered: list[Any] = []
    step_set = set(steps)
    while remaining:
        ready = []
        for step in remaining:
            deps = set(g.objects(step, namespace.precededBy))
            if not deps.intersection(remaining):
                ready.append(step)
        if not ready:
            ordered.extend(sorted(remaining, key=_local_name))
            break
        for step in sorted(ready, key=_local_name):
            ordered.append(step)
            remaining.remove(step)
    return [step for step in ordered if step in step_set]


def _parse_wfops_ttl(path: Path, g: Any, Graph: Any, Namespace: Any, RDF: Any) -> dict[str, Any] | None:
    WFO = Namespace(WFOPS_URI)
    workflow_subjects = list(g.subjects(RDF.type, WFO.Pipeline))
    workflow_subjects += [s for s in g.subjects(RDF.type, WFO.Workflow) if s not in workflow_subjects]
    if not workflow_subjects:
        return None
    subj = workflow_subjects[0]
    is_pipeline = (subj, RDF.type, WFO.Pipeline) in g
    category = _object_value(g, subj, WFO, "category")
    runtime_tier = _object_value(g, subj, WFO, "runtimeTier")
    out: dict[str, Any] = {
        "path": str(path),
        "raw": path.read_text(encoding="utf-8"),
        "id": _local_name(subj).removeprefix("workflow/"),
        "version": None,
        "category": category,
        "kind": "pipeline" if is_pipeline else "workflow",
        "mode": None,
        "status": None,
        "tool": None,
        "governance": {},
        "pipeline": [],
    }
    if runtime_tier is not None:
        out["runtime_tier"] = runtime_tier

    for gate in g.subjects(RDF.type, WFO.Gate):
        if not _local_name(gate).startswith(out["id"]):
            continue
        oracle_threshold = _object_value(g, gate, WFO, "oracleThreshold")
        judge = _object_value(g, gate, WFO, "judge")
        if oracle_threshold is not None:
            out["governance"]["oracle_threshold"] = oracle_threshold
        if str(judge).upper() == "HITL":
            out["governance"]["hitl_required"] = True
        break

    steps = list(g.objects(subj, WFO.hasStep))
    if steps:
        parsed_steps = []
        for step in _sort_wfops_steps(g, steps, WFO):
            step_id = _object_value(g, step, Namespace("http://www.w3.org/2000/01/rdf-schema#"), "label")
            parsed_steps.append({
                "step_id": step_id or _local_name(step),
                "tool": _object_value(g, step, WFO, "tool"),
                "action": _object_value(g, step, WFO, "action") or "default",
            })
        out["pipeline"] = parsed_steps
        return out

    if category:
        out["tool"] = {
            "evidence": "msm-evidence",
            "maintain": "msm-maintain",
            "ontology": "msm-ontology",
        }.get(str(category))
    return out


def _parse_mso_v07_ttl(path: Path, g: Any, Namespace: Any, RDF: Any) -> dict[str, Any] | None:
    """Read MSO v0.7 wf:Workflow Rail/Stream TTL as dry-run metadata.

    MSO owns topology execution semantics; MSM consumes this shape so the same
    workflow ABox can pass orchestration/CC/gate checks without requiring a
    separate MSMWF mirror file. The harness keeps this as a dry-run metadata
    workflow and leaves actual domain tool execution to explicit MSMWF pipelines.
    """
    W = Namespace(MSOWF_URI)
    workflow_subjects = list(g.subjects(RDF.type, W.Workflow))
    if not workflow_subjects:
        return None
    subj = workflow_subjects[0]
    members = list(g.objects(subj, W.has))
    category = path.parent.name if path.parent.name else None

    def one(pred: str):
        vals = list(g.objects(subj, W[pred]))
        return vals[0].toPython() if vals else None

    return {
        "path": str(path),
        "raw": path.read_text(encoding="utf-8"),
        "id": _local_name(subj).removeprefix("workflow/"),
        "version": None,
        "category": category,
        "kind": "pipeline",
        "mode": "dry-run",
        "status": one("status"),
        "tool": None,
        "governance": {"max_retry": 1},
        "pipeline": [],
        "workflow_type": one("workflowType"),
        "topology": {
            "members": len(members),
            "rail_edges": sum(1 for _ in g.subjects(RDF.type, W.Rail)),
            "stream_edges": sum(1 for _ in g.subjects(RDF.type, W.Stream)),
            "tasks": sum(1 for node in members if (node, RDF.type, W.Task) in g),
            "decisions": sum(1 for node in members if (node, RDF.type, W.Decision) in g),
            "artifacts": sum(1 for node in members if (node, RDF.type, W.Artifact) in g),
        },
    }


def workflow_dict_from_yaml_doc(doc: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    xmsm = doc.get("x_msm") if isinstance(doc.get("x_msm"), dict) else doc
    module = doc.get("module") if isinstance(doc.get("module"), dict) else doc
    gov = xmsm.get("governance") if isinstance(xmsm.get("governance"), dict) else {}
    out: dict[str, Any] = {
        "path": str(path) if path else None,
        "version": module.get("version"),
        "id": module.get("id") or xmsm.get("id") or (path.stem if path else None),
        "category": xmsm.get("category"),
        "kind": xmsm.get("kind"),
        "mode": xmsm.get("mode"),
        "status": xmsm.get("status") or module.get("status"),
        "tool": xmsm.get("tool"),
        "governance": {},
        "pipeline": xmsm.get("pipeline") or [],
    }
    for key in ("hitl_required", "max_retry", "oracle", "oracle_threshold"):
        if key in gov:
            out["governance"][key] = gov[key]
    budget = gov.get("cost_budget")
    if isinstance(budget, dict):
        out["cost_budget"] = {k: v for k, v in budget.items() if _scalar(v)}
    return out


def workflow_dict_to_graph(data: dict[str, Any]):
    BNode, Graph, Literal, Namespace, RDF, URIRef = _require_rdflib()
    g = Graph()
    W = Namespace(MSMWF_URI)
    g.bind("msmwf", W)
    wf_id = data.get("id") or "workflow"
    subj = W["workflow/" + _safe(wf_id)]
    g.add((subj, RDF.type, W.Workflow))
    for key in ("id", "version", "category", "kind", "mode", "status", "tool", "path"):
        value = data.get(key)
        if value is not None:
            g.add((subj, W[key], Literal(value)))
    gov = data.get("governance") or {}
    if gov:
        gb = BNode()
        g.add((subj, W.governance, gb))
        for key, value in gov.items():
            if value is not None:
                g.add((gb, W[key], Literal(value)))
    budget = data.get("cost_budget") or {}
    if budget:
        bb = BNode()
        g.add((subj, W.costBudget, bb))
        for key, value in budget.items():
            if value is not None:
                g.add((bb, W[key], Literal(value)))
    for idx, step in enumerate(data.get("pipeline") or [], 1):
        if not isinstance(step, dict):
            continue
        sb = BNode()
        g.add((subj, W.pipelineStep, sb))
        g.add((sb, W.stepIndex, Literal(idx)))
        for key, value in step.items():
            if _scalar(value) and value is not None:
                g.add((sb, W[key], Literal(value)))
            elif value is not None:
                g.add((sb, W[key + "Json"], Literal(json.dumps(value, ensure_ascii=False, sort_keys=True))))
    return g


def serialize_workflow_ttl(data: dict[str, Any]) -> str:
    return workflow_dict_to_graph(data).serialize(format="turtle")


def parse_workflow_ttl(path: Path) -> dict[str, Any]:
    _, Graph, _, Namespace, RDF, _ = _require_rdflib()
    W = Namespace(MSMWF_URI)
    g = Graph().parse(str(path), format="turtle")
    subjects = list(g.subjects(RDF.type, W.Workflow))
    if not subjects:
        wfops = _parse_wfops_ttl(path, g, Graph, Namespace, RDF)
        if wfops is not None:
            return wfops
        mso_v07 = _parse_mso_v07_ttl(path, g, Namespace, RDF)
        if mso_v07 is not None:
            return mso_v07
        return {"path": str(path), "raw": path.read_text(encoding="utf-8")}
    subj = subjects[0]

    def one(pred: str):
        vals = list(g.objects(subj, W[pred]))
        return vals[0].toPython() if vals else None

    out: dict[str, Any] = {"path": str(path), "raw": path.read_text(encoding="utf-8")}
    for key in ("version", "id", "category", "kind", "mode", "status", "tool"):
        out[key] = one(key)
    gov: dict[str, Any] = {}
    for gb in g.objects(subj, W.governance):
        for key in ("hitl_required", "max_retry", "oracle", "oracle_threshold"):
            vals = list(g.objects(gb, W[key]))
            if vals:
                gov[key] = vals[0].toPython()
    out["governance"] = gov
    budget: dict[str, Any] = {}
    for bb in g.objects(subj, W.costBudget):
        for key in ("tokens", "seconds", "power_wh"):
            vals = list(g.objects(bb, W[key]))
            if vals:
                budget[key] = vals[0].toPython()
    if budget:
        out["cost_budget"] = budget
    steps = []
    for sb in g.objects(subj, W.pipelineStep):
        step: dict[str, Any] = {}
        idx_vals = list(g.objects(sb, W.stepIndex))
        idx = int(idx_vals[0].toPython()) if idx_vals else 0
        for pred, obj in g.predicate_objects(sb):
            key = str(pred).removeprefix(MSMWF_URI)
            if key == "stepIndex":
                continue
            step[key] = obj.toPython()
        steps.append((idx, step))
    out["pipeline"] = [s for _, s in sorted(steps, key=lambda x: x[0])]
    return out


def serialize_index_ttl(workflows: list[dict[str, Any]]) -> str:
    BNode, Graph, Literal, Namespace, RDF, _ = _require_rdflib()
    W = Namespace(MSMWF_URI)
    g = Graph()
    g.bind("msmwf", W)
    idx = W["workflow/index"]
    g.add((idx, RDF.type, W.WorkflowIndex))
    for wf in workflows:
        b = BNode()
        g.add((idx, W.workflowEntry, b))
        for key, value in wf.items():
            if _scalar(value) and value is not None:
                g.add((b, W[key], Literal(value)))
    return g.serialize(format="turtle")


def parse_index_ttl(path: Path) -> list[dict[str, Any]]:
    _, Graph, _, Namespace, RDF, _ = _require_rdflib()
    W = Namespace(MSMWF_URI)
    g = Graph().parse(str(path), format="turtle")
    entries: list[dict[str, Any]] = []
    for idx in g.subjects(RDF.type, W.WorkflowIndex):
        for b in g.objects(idx, W.workflowEntry):
            d: dict[str, Any] = {}
            for pred, obj in g.predicate_objects(b):
                d[str(pred).removeprefix(MSMWF_URI)] = obj.toPython()
            entries.append(d)
    return sorted(entries, key=lambda x: x.get("id", ""))
