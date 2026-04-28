"""
mece_interview.py
graph-ontology.yaml 설계·검증 시 MECE(상호배제·전체포괄) 구조를 보장하는 Calibrated Validation 루프.

설계 철학: Bounded Rationality — 검증 깊이를 고정하지 않고 리소스 투입량을 명시적으로 조절한다.

  Depth   LLM 호출     라운드   게이트      중단 기준
  light   0            0       heuristic   구조 존재 확인 1회 pass
  medium  2/라운드     2-3     ≥0.75       2회 이내 pass
  deep    3/라운드     5-8     ≥0.85       score + open_questions 소진

사용:
    # 새 온톨로지 설계 (Medium)
    python3 mece_interview.py --domain "시장 분석 KB" --depth medium --output ./graph-ontology.yaml

    # 기존 초안 구조 확인만 (Light, LLM 호출 없음)
    python3 mece_interview.py --draft ./graph-ontology.yaml --depth light

    # 기존 초안 개선 (Deep)
    python3 mece_interview.py --draft ./graph-ontology.yaml --depth deep --output ./graph-ontology.yaml
"""

import json
import re
import sys
import argparse
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

# ── 의존성 ─────────────────────────────────────────────────────────────────────

try:
    import anthropic as _anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False

# ── 상수 ──────────────────────────────────────────────────────────────────────

MODEL = "claude-sonnet-4-6"
TODAY = date.today().isoformat()

DEPTH_CONFIG: dict[str, dict] = {
    "light": {
        "max_rounds":         0,
        "gate":               None,
        "scoring_mode":       None,
        "llm_calls_estimate": 0,
        "description":        "LLM 호출 없음 — 구조 존재 체크리스트만",
    },
    "medium": {
        "max_rounds":         3,
        "gate":               0.75,
        "scoring_mode":       "two_bucket",
        "llm_calls_estimate": "4-6",
        "description":        "ME/CE 두 묶음 채점, 2-3 라운드",
    },
    "deep": {
        "max_rounds":         8,
        "gate":               0.85,
        "scoring_mode":       "six_dim",
        "llm_calls_estimate": "15-24",
        "description":        "6차원 전체 채점 + Contrarian, 5-8 라운드",
    },
}

# ME 차원 가중치
ME_WEIGHTS = {
    "class_boundary_clarity": 0.40,
    "property_uniqueness":    0.35,
    "constraint_consistency": 0.25,
}

# CE 차원 가중치
CE_WEIGHTS = {
    "entity_coverage":    0.40,
    "relation_coverage":  0.35,
    "attribute_coverage": 0.25,
}

# 취약 차원 → 질문 관점
PERSPECTIVE: dict[str, str] = {
    "me":                     "BOUNDARY_TESTER: 두 클래스가 동시에 적용될 수 있는 실체나 domain/range 충돌을 찾아라",
    "ce":                     "EXHAUSTIVENESS_PROBER: 어떤 클래스·관계에도 속하지 않는 도메인 실체를 찾아라",
    "class_boundary_clarity": "BOUNDARY_TESTER: 두 클래스 경계가 겹치는 반례를 찾아라",
    "property_uniqueness":    "REDUNDANCY_HUNTER: 같은 의미를 가진 중복 관계를 찾아라",
    "constraint_consistency": "CONSTRAINT_CHECKER: domain/range 제약이 실제 인스턴스와 충돌하는 케이스를 찾아라",
    "entity_coverage":        "EXHAUSTIVENESS_PROBER: 어떤 클래스에도 안 들어가는 도메인 실체를 찾아라",
    "relation_coverage":      "RELATION_MAPPER: 아직 정의되지 않은 의미 있는 관계를 찾아라",
    "attribute_coverage":     "ATTRIBUTE_AUDITOR: 중요한데 datatype_property로 정의 안 된 속성을 찾아라",
}

# ── 데이터 구조 ────────────────────────────────────────────────────────────────

@dataclass
class OntologyDraft:
    classes:             dict = field(default_factory=dict)
    object_properties:   dict = field(default_factory=dict)
    datatype_properties: dict = field(default_factory=dict)
    namespace:           str  = ""
    extra:               dict = field(default_factory=dict)  # morphism_types 등 보존

    @classmethod
    def from_yaml(cls, path: Path) -> "OntologyDraft":
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        known = {"classes", "object_properties", "datatype_properties",
                 "namespace", "mece_assessment", "scalar_node_attrs"}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            classes=data.get("classes") or {},
            object_properties=data.get("object_properties") or {},
            datatype_properties=data.get("datatype_properties") or {},
            namespace=data.get("namespace", ""),
            extra=extra,
        )

    def to_dict(self) -> dict:
        d: dict = {}
        if self.namespace:
            d["namespace"] = self.namespace
        d["classes"]             = self.classes
        d["object_properties"]   = self.object_properties
        d["datatype_properties"] = self.datatype_properties
        d.update(self.extra)
        return d

    def summary(self) -> str:
        return (
            f"  classes: {list(self.classes.keys())}\n"
            f"  object_properties: {list(self.object_properties.keys())}\n"
            f"  datatype_properties: {list(self.datatype_properties.keys())}"
        )

    def as_yaml_str(self) -> str:
        return yaml.dump(
            self.to_dict(), allow_unicode=True,
            default_flow_style=False, sort_keys=False,
        )

    def is_empty(self) -> bool:
        return not self.classes and not self.object_properties


@dataclass
class InterviewRound:
    perspective: str
    question:    str
    answer:      str


@dataclass
class MeceAssessment:
    depth:          str
    score:          float = 0.0
    me_score:       float = 0.0
    ce_score:       float = 0.0
    gate:           float = 0.0
    rounds_used:    int   = 0
    status:         str   = "draft"   # draft | reviewing | seed_ready
    weakest:        str   = ""
    breakdown:      dict  = field(default_factory=dict)
    open_questions: list  = field(default_factory=list)
    assessed_at:    str   = ""

    def to_dict(self) -> dict:
        d: dict = {
            "depth":          self.depth,
            "score":          round(self.score, 3),
            "me_score":       round(self.me_score, 3),
            "ce_score":       round(self.ce_score, 3),
            "gate_threshold": self.gate,
            "rounds_used":    self.rounds_used,
            "status":         self.status,
            "assessed_at":    self.assessed_at,
        }
        if self.breakdown:
            d["breakdown"] = {k: round(v, 3) for k, v in self.breakdown.items()}
        d["open_questions"] = self.open_questions
        return d


# ── Light: Heuristic 체크 ──────────────────────────────────────────────────────

def check_light(draft: OntologyDraft) -> tuple[bool, list[str]]:
    """LLM 없이 구조 존재 여부와 domain/range 선언을 확인한다."""
    issues: list[str] = []

    if len(draft.classes) < 2:
        issues.append(f"클래스 최소 2개 필요 (현재: {len(draft.classes)}개)")

    if len(draft.object_properties) < 1:
        issues.append("object_property 최소 1개 필요")

    for name, cls in draft.classes.items():
        if not (cls or {}).get("entity_dir"):
            issues.append(f"클래스 '{name}': entity_dir 미정의")

    for name, prop in draft.object_properties.items():
        prop = prop or {}
        if not prop.get("domain"):
            issues.append(f"관계 '{name}': domain 미선언")
        if not prop.get("range"):
            issues.append(f"관계 '{name}': range 미선언")
        domain = prop.get("domain", "")
        rng    = prop.get("range", "")
        if domain and domain not in draft.classes:
            issues.append(f"관계 '{name}': domain '{domain}'이 classes에 없음")
        if rng and rng not in draft.classes:
            issues.append(f"관계 '{name}': range '{rng}'이 classes에 없음")

    return len(issues) == 0, issues


# ── LLM 클라이언트 ──────────────────────────────────────────────────────────────

def _require_anthropic() -> "_anthropic.Anthropic":
    if not _HAS_ANTHROPIC:
        print("[오류] medium/deep 모드는 anthropic 패키지가 필요합니다.")
        print("       pip install anthropic")
        sys.exit(1)
    return _anthropic.Anthropic()


def _call(client, system: str, user: str, max_tokens: int = 512) -> str:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


def _parse_json(text: str) -> dict:
    """코드블록 포함 LLM 응답에서 JSON 추출."""
    for pattern in (r'```(?:json)?\s*(\{.*?\})\s*```', r'\{.*\}'):
        m = re.search(pattern, text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1) if m.lastindex else m.group())
            except json.JSONDecodeError:
                continue
    raise ValueError(f"JSON 파싱 실패:\n{text[:400]}")


# ── Scoring ────────────────────────────────────────────────────────────────────

_TWO_BUCKET_SYS = """\
온톨로지 MECE 평가자다. 초안과 인터뷰 내역을 보고 아래 JSON만 반환해라.
{
  "me_score": 0.0~1.0,
  "ce_score": 0.0~1.0,
  "weakest": "me" 또는 "ce",
  "reasoning": "핵심 문제 한 줄"
}
me_score: 클래스 경계 비중복 + 관계 의미 고유 + 제약 일관성 (높을수록 좋음)
ce_score: 도메인 실체 누락 없음 + 관계 커버리지 + 속성 정의 (높을수록 좋음)"""

_SIX_DIM_SYS = """\
온톨로지 MECE 평가자다. 6차원을 개별 평가해 아래 JSON만 반환해라.
{
  "class_boundary_clarity": 0.0~1.0,
  "property_uniqueness":    0.0~1.0,
  "constraint_consistency": 0.0~1.0,
  "entity_coverage":        0.0~1.0,
  "relation_coverage":      0.0~1.0,
  "attribute_coverage":     0.0~1.0,
  "weakest": "가장 낮은 차원 이름",
  "reasoning": "핵심 문제 한 줄"
}
높을수록 좋음 (1.0 = 완벽한 MECE)."""

_CONTRARIAN_SYS = """\
온톨로지 MECE 비판자다. 이 설계가 틀렸다는 근거를 찾아 아래 JSON만 반환해라.
{
  "finding": "가장 심각한 MECE 위반 한 줄 (없으면 빈 문자열)",
  "open_question": "반드시 명확히 해야 할 미결 질문 (없으면 빈 문자열)"
}"""

_CRYSTALLIZE_SYS = """\
온톨로지 설계자다. 인터뷰 내용을 반영해 graph-ontology.yaml용 구조를 만든다.
아래 JSON만 반환해라:
{
  "classes": {
    "ClassName": {"label": "...", "entity_dir": "data/[slug]", "description": "..."}
  },
  "object_properties": {
    "propName": {
      "label": "...", "domain": "ClassName", "range": "ClassName",
      "relation_name": "snake_case", "rollup": []
    }
  },
  "datatype_properties": {
    "propName": {"label": "...", "domain": ["ClassName"], "range": "xsd:string"}
  }
}"""


def _history_text(history: list[InterviewRound]) -> str:
    if not history:
        return "(아직 없음)"
    return "\n".join(f"Q{i+1}: {r.question}\nA{i+1}: {r.answer}" for i, r in enumerate(history))


def score_two_bucket(client, draft: OntologyDraft,
                     history: list[InterviewRound]) -> dict:
    user = f"온톨로지 초안:\n{draft.as_yaml_str()}\n\n인터뷰 내역:\n{_history_text(history)}"
    data = _parse_json(_call(client, _TWO_BUCKET_SYS, user, max_tokens=300))

    me = float(data.get("me_score", 0))
    ce = float(data.get("ce_score", 0))
    return {
        "score":     round((me + ce) / 2, 3),
        "me_score":  round(me, 3),
        "ce_score":  round(ce, 3),
        "weakest":   str(data.get("weakest", "ce")),
        "reasoning": str(data.get("reasoning", "")),
        "breakdown": {},
    }


def score_six_dim(client, draft: OntologyDraft,
                  history: list[InterviewRound]) -> dict:
    user = f"온톨로지 초안:\n{draft.as_yaml_str()}\n\n인터뷰 내역:\n{_history_text(history)}"
    data = _parse_json(_call(client, _SIX_DIM_SYS, user, max_tokens=400))

    me = sum(float(data.get(k, 0)) * w for k, w in ME_WEIGHTS.items())
    ce = sum(float(data.get(k, 0)) * w for k, w in CE_WEIGHTS.items())
    breakdown = {k: float(data.get(k, 0)) for k in list(ME_WEIGHTS) + list(CE_WEIGHTS)}
    return {
        "score":     round((me + ce) / 2, 3),
        "me_score":  round(me, 3),
        "ce_score":  round(ce, 3),
        "weakest":   str(data.get("weakest", "entity_coverage")),
        "reasoning": str(data.get("reasoning", "")),
        "breakdown": breakdown,
    }


def ask_question(client, draft: OntologyDraft, history: list[InterviewRound],
                 weakest: str, domain: str) -> str:
    perspective = PERSPECTIVE.get(weakest, "MECE_REVIEWER: 구조적 문제를 찾아라")
    sys_prompt = (
        f"온톨로지 MECE 인터뷰어다. 현재 관점: {perspective}\n"
        "규칙:\n"
        "- 질문 하나만\n"
        "- 설계자가 미처 생각 못한 경계 케이스나 빈틈을 드러내는 질문\n"
        "- 도입·인사 없이 바로 질문"
    )
    user = (
        f"도메인: {domain}\n\n"
        f"온톨로지 초안:\n{draft.as_yaml_str()}\n\n"
        f"인터뷰 내역:\n{_history_text(history)}\n\n"
        "다음 질문:"
    )
    return _call(client, sys_prompt, user, max_tokens=200)


def check_contrarian(client, draft: OntologyDraft,
                     history: list[InterviewRound]) -> dict:
    user = f"온톨로지:\n{draft.as_yaml_str()}\n\n인터뷰:\n{_history_text(history)}"
    return _parse_json(_call(client, _CONTRARIAN_SYS, user, max_tokens=300))


def crystallize(client, draft: OntologyDraft,
                history: list[InterviewRound], domain: str) -> OntologyDraft:
    user = (
        f"도메인: {domain}\n"
        f"기존 초안:\n{draft.as_yaml_str()}\n\n"
        f"인터뷰 내역 (이 내용을 반영해야 함):\n{_history_text(history)}"
    )
    data = _parse_json(_call(client, _CRYSTALLIZE_SYS, user, max_tokens=2000))
    return OntologyDraft(
        classes=data.get("classes") or draft.classes,
        object_properties=data.get("object_properties") or draft.object_properties,
        datatype_properties=data.get("datatype_properties") or draft.datatype_properties,
        namespace=draft.namespace,
        extra=draft.extra,
    )


# ── YAML 출력 ──────────────────────────────────────────────────────────────────

_ONTOLOGY_HEADER = """\
# graph-ontology.yaml
# OWL 스타일 단일 진실 소스 (Single Source of Truth)
# mece_assessment 섹션은 mece_interview.py가 자동 생성한다.
#
# 사용:
#   python3 skills/md-frontmatter-rollup/scripts/rollup_engine.py --ontology graph-ontology.yaml
#   python3 skills/md-graph-multihop/scripts/graph_builder.py --config graph-config.yaml
"""


def _write_ontology(draft: OntologyDraft, assessment: MeceAssessment, output: Path) -> None:
    data = draft.to_dict()
    data["mece_assessment"] = assessment.to_dict()
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(_ONTOLOGY_HEADER + "\n")
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"\n  → 저장: {output}")


def _write_validation_pack(draft: OntologyDraft, assessment: MeceAssessment,
                           history: list[InterviewRound], output_dir: Path) -> None:
    pack = {
        "ontology_summary": {
            "classes":             list(draft.classes.keys()),
            "object_properties":   list(draft.object_properties.keys()),
            "datatype_properties": list(draft.datatype_properties.keys()),
        },
        "mece_assessment": assessment.to_dict(),
        "interview_log": [
            {"round": i + 1, "perspective": r.perspective,
             "Q": r.question, "A": r.answer}
            for i, r in enumerate(history)
        ],
    }
    pack_path = output_dir / "context" / "validation" / f"mece-pack-{TODAY}.yaml"
    pack_path.parent.mkdir(parents=True, exist_ok=True)
    with open(pack_path, "w", encoding="utf-8") as f:
        yaml.dump(pack, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"  → validation pack: {pack_path}")


# ── 깊이별 실행 루프 ───────────────────────────────────────────────────────────

def run_light(draft: OntologyDraft, output: Path | None) -> MeceAssessment:
    print("\n[ Light — LLM 호출 없음, 구조 체크리스트 ]")
    passed, issues = check_light(draft)

    if passed:
        print("  ✓ PASS")
        status = "seed_ready"
    else:
        for issue in issues:
            print(f"  ✗ {issue}")
        status = "draft"

    assessment = MeceAssessment(
        depth="light",
        gate=0.0,
        status=status,
        open_questions=[] if passed else issues,
        assessed_at=TODAY,
    )
    if output:
        _write_ontology(draft, assessment, output)
    return assessment


def run_medium(draft: OntologyDraft, domain: str, output: Path | None) -> MeceAssessment:
    cfg = DEPTH_CONFIG["medium"]
    client = _require_anthropic()
    history: list[InterviewRound] = []
    score_data: dict = {"score": 0.0, "me_score": 0.0, "ce_score": 0.0,
                        "weakest": "ce", "reasoning": "", "breakdown": {}}

    print(f"\n[ Medium — 최대 {cfg['max_rounds']}라운드, 게이트 ≥{cfg['gate']}, "
          f"예상 LLM 호출 {cfg['llm_calls_estimate']}회 ]")

    for rnd in range(1, cfg["max_rounds"] + 1):
        weakest = score_data["weakest"]
        question = ask_question(client, draft, history, weakest, domain)

        print(f"\n── Round {rnd}/{cfg['max_rounds']} [{weakest}] ──")
        print(f"Q: {question}")
        answer = input("A: ").strip()
        if not answer:
            print("  (빈 답변 — 건너뜀)")
            continue

        history.append(InterviewRound(
            perspective=PERSPECTIVE.get(weakest, "MECE_REVIEWER"),
            question=question,
            answer=answer,
        ))

        score_data = score_two_bucket(client, draft, history)
        print(f"  [MECE {score_data['score']:.2f}]  "
              f"ME:{score_data['me_score']:.2f}  CE:{score_data['ce_score']:.2f}  "
              f"— {score_data['reasoning']}")

        if score_data["score"] >= cfg["gate"]:
            print(f"  ✓ 게이트 통과 (≥{cfg['gate']})")
            break

    # 인터뷰가 진행됐으면 결정화
    if history:
        print("\n  [ 결정화 중... ]")
        draft = crystallize(client, draft, history, domain)

    passed = score_data["score"] >= cfg["gate"]
    assessment = MeceAssessment(
        depth="medium",
        score=score_data["score"],
        me_score=score_data["me_score"],
        ce_score=score_data["ce_score"],
        gate=cfg["gate"],
        rounds_used=len(history),
        status="seed_ready" if passed else "reviewing",
        weakest=score_data["weakest"],
        assessed_at=TODAY,
    )
    if output:
        _write_ontology(draft, assessment, output)
    return assessment


def run_deep(draft: OntologyDraft, domain: str, output: Path | None) -> MeceAssessment:
    cfg = DEPTH_CONFIG["deep"]
    client = _require_anthropic()
    history: list[InterviewRound] = []
    score_data: dict = {"score": 0.0, "me_score": 0.0, "ce_score": 0.0,
                        "weakest": "entity_coverage", "reasoning": "", "breakdown": {}}
    open_questions: list[str] = []

    print(f"\n[ Deep — 최대 {cfg['max_rounds']}라운드, 게이트 ≥{cfg['gate']}, "
          f"예상 LLM 호출 {cfg['llm_calls_estimate']}회 ]")

    for rnd in range(1, cfg["max_rounds"] + 1):
        weakest = score_data["weakest"]
        question = ask_question(client, draft, history, weakest, domain)

        print(f"\n── Round {rnd}/{cfg['max_rounds']} [{weakest}] ──")
        print(f"Q: {question}")
        answer = input("A: ").strip()
        if not answer:
            print("  (빈 답변 — 건너뜀)")
            continue

        history.append(InterviewRound(
            perspective=PERSPECTIVE.get(weakest, "MECE_REVIEWER"),
            question=question,
            answer=answer,
        ))

        # 6차원 채점
        score_data = score_six_dim(client, draft, history)
        print(f"  [MECE {score_data['score']:.2f}]  "
              f"ME:{score_data['me_score']:.2f}  CE:{score_data['ce_score']:.2f}  "
              f"취약: {score_data['weakest']}")

        # Contrarian 체크 (Deep 전용)
        contrarian = check_contrarian(client, draft, history)
        if contrarian.get("finding"):
            print(f"  [Contrarian] {contrarian['finding']}")
        oq = contrarian.get("open_question", "")
        if oq and oq not in open_questions:
            open_questions.append(oq)
            print(f"  [미결 질문] {oq}")

        # 게이트: 점수 + open_questions 소진
        if score_data["score"] >= cfg["gate"]:
            if not open_questions:
                print(f"  ✓ Deep 게이트 통과 (≥{cfg['gate']}, 미결 질문 없음)")
                break
            else:
                print(f"  (점수 충족, 미결 질문 {len(open_questions)}개 남음)")

    print("\n  [ 결정화 중... ]")
    draft = crystallize(client, draft, history, domain)

    passed = score_data["score"] >= cfg["gate"] and not open_questions
    assessment = MeceAssessment(
        depth="deep",
        score=score_data["score"],
        me_score=score_data["me_score"],
        ce_score=score_data["ce_score"],
        gate=cfg["gate"],
        rounds_used=len(history),
        status="seed_ready" if passed else "reviewing",
        weakest=score_data["weakest"],
        breakdown=score_data["breakdown"],
        open_questions=open_questions,
        assessed_at=TODAY,
    )
    if output:
        _write_ontology(draft, assessment, output)
        _write_validation_pack(draft, assessment, history, output.parent)
    return assessment


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="graph-ontology.yaml MECE 설계·검증 (Calibrated Validation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
깊이별 리소스 비용:
  light  : LLM 호출 0회  — 구조 존재 확인만  (게이트: heuristic)
  medium : LLM 4-6회    — ME/CE 채점 2-3 라운드 (게이트: ≥0.75)
  deep   : LLM 15-24회  — 6차원 채점 5-8 라운드 (게이트: ≥0.85 + open_questions 소진)

예시:
  python3 mece_interview.py --domain "시장 분석 KB" --depth medium --output graph-ontology.yaml
  python3 mece_interview.py --draft graph-ontology.yaml --depth light
  python3 mece_interview.py --draft graph-ontology.yaml --depth deep --output graph-ontology.yaml
        """,
    )
    parser.add_argument("--domain", "-d", default="",
                        help="KB 도메인 설명 (새 설계 시)")
    parser.add_argument("--draft", type=Path,
                        help="기존 graph-ontology.yaml 경로 (없으면 빈 초안으로 시작)")
    parser.add_argument("--depth", choices=["light", "medium", "deep"],
                        default="medium",
                        help="검증 깊이 — 리소스 투입량 조절 (기본: medium)")
    parser.add_argument("--output", "-o", type=Path,
                        help="출력 yaml 경로 (생략 시 파일 저장 안 함, 결과만 출력)")
    args = parser.parse_args()

    # 초안 로드
    if args.draft and args.draft.exists():
        draft = OntologyDraft.from_yaml(args.draft)
        domain = args.domain or args.draft.stem
        print(f"초안 로드: {args.draft}")
        print(draft.summary())
    else:
        draft = OntologyDraft()
        domain = args.domain or "미지정 도메인"
        if not args.domain:
            print("[주의] --domain 또는 --draft를 지정하면 더 정확한 질문이 생성됩니다.")

    cfg = DEPTH_CONFIG[args.depth]
    print(f"\n도메인   : {domain}")
    print(f"검증 깊이: {args.depth}  ({cfg['description']})")

    # 깊이별 실행
    if args.depth == "light":
        run_light(draft, args.output)
    elif args.depth == "medium":
        run_medium(draft, domain, args.output)
    else:
        run_deep(draft, domain, args.output)


if __name__ == "__main__":
    main()
