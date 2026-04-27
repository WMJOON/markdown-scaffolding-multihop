"""
mece_interview.py
graph-ontology.yaml 설계·검증 시 MECE(상호배제·전체포괄) 구조를 보장하는 Calibrated Validation 루프.

설계 철학: Bounded Rationality — 검증 깊이를 고정하지 않고 리소스 투입량을 명시적으로 조절한다.

  Depth   LLM 호출     라운드   게이트      중단 기준
  light   0            0       heuristic   구조 존재 확인 1회 pass
  medium  2/라운드     2-3     ≥0.75       2회 이내 pass
  deep    3/라운드     5-8     ≥0.85       score + open_questions 소진

클라이언트 우선순위 (medium/deep):
  1. Ollama 로컬 서버 — 가용 시 사용자에게 먼저 확인
  2. Anthropic API   — ANTHROPIC_API_KEY가 설정된 경우
  3. 사용자 인터뷰    — LLM 없이 템플릿 질문으로 진행 (항상 폴백)

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
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

# ── 상수 ──────────────────────────────────────────────────────────────────────

TODAY = date.today().isoformat()

OLLAMA_BASE  = "http://localhost:11434"
OLLAMA_MODEL = "qwen3.5:4b"

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

# LLM 없을 때 사용하는 템플릿 질문
TEMPLATE_QUESTIONS: dict[str, list[str]] = {
    "me": [
        "두 개 이상의 클래스에 동시에 속할 수 있는 실체가 있나요? 예를 들면?",
        "어떤 관계가 다른 관계와 의미상 겹치거나 대체 가능한가요?",
        "domain/range 제약이 실제 데이터와 충돌하는 케이스를 떠올릴 수 있나요?",
    ],
    "ce": [
        "이 도메인에서 중요한데 어떤 클래스에도 속하지 않는 개념이 있나요?",
        "두 노드 사이에 표현하고 싶은 관계인데 정의되지 않은 것이 있나요?",
        "자주 사용될 속성인데 datatype_property로 정의하지 않은 것이 있나요?",
    ],
    "class_boundary_clarity": [
        "가장 경계가 모호한 두 클래스는 무엇이고, 어떤 기준으로 구분하나요?",
        "한 인스턴스가 두 클래스에 동시에 들어갈 수 있는 케이스가 있나요?",
    ],
    "property_uniqueness": [
        "비슷한 의미를 가진 관계가 여러 개 있나요? 각각의 차이는 무엇인가요?",
        "제거해도 표현력이 줄지 않는 관계가 있다면 어떤 것인가요?",
    ],
    "constraint_consistency": [
        "정의된 domain/range 제약이 실제 데이터 패턴과 맞지 않는 경우가 있나요?",
        "방향성(단방향/양방향)이 실제 의미와 어긋나는 관계가 있나요?",
    ],
    "entity_coverage": [
        "이 도메인의 핵심 개념인데 클래스로 정의하지 않은 것이 있나요?",
        "KB를 처음 보는 사람이 '이게 왜 없지?'라고 할 만한 개념은?",
    ],
    "relation_coverage": [
        "중요한 노드 간 관계인데 아직 정의되지 않은 것이 있나요?",
        "현재 관계만으로 표현할 수 없는 중요한 사실이 있나요?",
    ],
    "attribute_coverage": [
        "인스턴스 frontmatter에서 자주 쓰이는 필드인데 datatype_property에 없는 것이 있나요?",
        "검색·필터링에 자주 쓰일 속성인데 정의하지 않은 것은?",
    ],
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

    has_instance_dirs = bool(draft.extra.get("instance_dirs"))
    for name, cls in draft.classes.items():
        cls_cfg = cls or {}
        # entity_dir(레거시) 또는 instance_dirs(도메인 기반) 중 하나면 OK
        if not cls_cfg.get("entity_dir") and not has_instance_dirs:
            issues.append(f"클래스 '{name}': entity_dir 미정의 (또는 최상위 instance_dirs 선언 필요)")

    for name, prop in draft.object_properties.items():
        prop = prop or {}
        if not prop.get("domain"):
            issues.append(f"관계 '{name}': domain 미선언")
        if not prop.get("range"):
            issues.append(f"관계 '{name}': range 미선언")
        domain = prop.get("domain", "")
        rng    = prop.get("range", "")
        # domain/range는 단일 문자열 또는 리스트 모두 허용
        domain_list = domain if isinstance(domain, list) else ([domain] if domain else [])
        range_list  = rng   if isinstance(rng,    list) else ([rng]    if rng    else [])
        for d in domain_list:
            if d and d not in draft.classes:
                issues.append(f"관계 '{name}': domain '{d}'이 classes에 없음")
        for r in range_list:
            if r and r not in draft.classes:
                issues.append(f"관계 '{name}': range '{r}'이 classes에 없음")

    return len(issues) == 0, issues


# ── Ollama 클라이언트 ───────────────────────────────────────────────────────────

def _check_ollama() -> tuple[bool, list[str]]:
    """Ollama 로컬 서버 가용성 확인. (가용 여부, 모델명 목록) 반환."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE}/api/tags", timeout=2) as resp:
            data = json.loads(resp.read())
            return True, [m["name"] for m in data.get("models", [])]
    except Exception:
        return False, []


class _OllamaClient:
    def __init__(self, model: str):
        self.model = model

    def generate(self, system: str, user: str, max_tokens: int = 512) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        body: dict = {
            "model":   self.model,
            "messages": messages,
            "stream":  False,
            "options": {"num_predict": max_tokens},
        }
        # qwen3 계열은 think:false를 최상위에 설정해야 thinking 모드가 꺼짐
        if "qwen3" in self.model:
            body["think"] = False

        payload = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_BASE}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        timeout = 300 if max_tokens >= 2000 else 120
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read()).get("message", {}).get("content", "").strip()

    def smoke_test(self) -> bool:
        """빈 응답을 내는 모델인지 확인."""
        try:
            return bool(self.generate("", '다음 JSON만 반환해라: {"ok":true}', max_tokens=100))
        except Exception:
            return False


# ── 클라이언트 선택 ────────────────────────────────────────────────────────────

_AUTO_OLLAMA: bool = False  # --ollama 플래그로 설정됨
_AUTO_MODE:   bool = False  # --auto 플래그로 설정됨


def auto_answer(client, draft: "OntologyDraft", question: str, domain: str) -> str:
    """--auto 모드: LLM이 온톨로지 전문 검토자 역할로 질문에 답변한다."""
    system = (
        "You are a senior ontology reviewer conducting a MECE validation interview. "
        "Your job is to critically evaluate the ontology draft and give substantive answers "
        "that identify real gaps, overlaps, or coverage issues. "
        "Be specific — name actual classes or clusters. Keep your answer to 2-4 sentences."
    )
    user = (
        f"Domain: {domain}\n\n"
        f"Ontology draft (classes/clusters):\n{draft.as_yaml_str()[:3000]}\n\n"
        f"Interview question: {question}\n\n"
        "Answer as a critical ontology reviewer:"
    )
    try:
        return client.generate(system, user, max_tokens=300)
    except Exception as e:
        return f"(auto-answer 실패: {e})"


def _resolve_client() -> tuple[object | None, str]:
    """
    LLM 클라이언트 우선순위:
      1. Ollama 로컬 — 가용 시 사용자 확인, smoke test 통과 모델 선택
      2. None (사용자 인터뷰 모드) — 항상 폴백
    Returns (client | None, mode)
    """
    available, models = _check_ollama()
    if available:
        model_hint = ", ".join(models[:5]) if models else "없음"
        print(f"\n[Ollama] 로컬 서버 감지 — 모델: {model_hint}")
        if _AUTO_OLLAMA:
            ans = "y"
            print("로컬 모델을 사용하시겠습니까? [y/N]: y  (--ollama 자동 수락)")
        else:
            ans = input("로컬 모델을 사용하시겠습니까? [y/N]: ").strip().lower()
        if ans == "y":
            # JSON 지시 준수 우선: qwen → phi → llama → gemma → mistral
            priority = [
                [m for m in models if "qwen" in m],
                [m for m in models if "phi" in m],
                [m for m in models if "llama" in m],
                [m for m in models if "gemma" in m],
                [m for m in models if "mistral" in m],
            ]
            seen: set[str] = set()
            candidates: list[str] = []
            for group in priority:
                for m in group:
                    if m not in seen:
                        candidates.append(m)
                        seen.add(m)
            candidates += [m for m in models if m not in seen]
            chosen = None
            for m in candidates:
                c = _OllamaClient(m)
                print(f"  → 모델 확인 중: {m} ...", end=" ", flush=True)
                if c.smoke_test():
                    print("OK")
                    chosen = m
                    break
                print("응답 없음, 다음 시도")
            if chosen:
                return _OllamaClient(chosen), "ollama"
            print("  [경고] 응답 가능한 모델이 없습니다. 인터뷰 모드로 전환합니다.")

    print("\n[인터뷰 모드] LLM을 사용할 수 없습니다. 템플릿 질문으로 진행합니다.")
    return None, "interview"


# ── LLM 공통 호출 ─────────────────────────────────────────────────────────────

def _call(client: _OllamaClient, system: str, user: str, max_tokens: int = 512) -> str:
    return client.generate(system, user, max_tokens)


def _extract_first_json(text: str) -> str:
    """텍스트에서 첫 번째 완전한 JSON 객체를 추출한다."""
    depth, start, in_str, esc = 0, None, False, False
    for i, c in enumerate(text):
        if esc:
            esc = False; continue
        if c == "\\" and in_str:
            esc = True; continue
        if c == '"':
            in_str = not in_str; continue
        if in_str:
            continue
        if c == "{":
            if depth == 0:
                start = i
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and start is not None:
                return text[start:i + 1]
    return ""


def _parse_json(text: str) -> dict:
    """LLM 응답에서 첫 번째 JSON 객체 추출. 끝이 잘린 경우 자동 복구 시도."""
    # 코드블록 안에 있으면 먼저 꺼내기
    cb = re.search(r'```(?:json)?\s*(\{.*?})\s*```', text, re.DOTALL)
    if cb:
        try:
            return json.loads(cb.group(1))
        except json.JSONDecodeError:
            pass

    # 첫 번째 완전한 JSON 객체
    raw = _extract_first_json(text)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # 닫는 중괄호가 잘린 경우 복구 시도
            for suffix in ("}", '"}}', '"}', "}}"):
                try:
                    return json.loads(raw + suffix)
                except json.JSONDecodeError:
                    continue
    raise ValueError(f"JSON 파싱 실패:\n{text[:400]}")


# ── Scoring ────────────────────────────────────────────────────────────────────

_TWO_BUCKET_SYS = """\
You are an ontology MECE evaluator. Return ONLY valid JSON. No prose, no explanations, no markdown.
Example output:
{"me_score": 0.7, "ce_score": 0.8, "weakest": "me", "reasoning": "class boundaries overlap"}
me_score: class boundary uniqueness + property uniqueness + constraint consistency (higher is better)
ce_score: entity coverage + relation coverage + attribute coverage (higher is better)
Output JSON only:"""

_SIX_DIM_SYS = """\
You are an ontology MECE evaluator. Return ONLY valid JSON. No prose, no explanations, no markdown.
Example output:
{"class_boundary_clarity": 0.8, "property_uniqueness": 0.9, "constraint_consistency": 0.7, "entity_coverage": 0.6, "relation_coverage": 0.7, "attribute_coverage": 0.5, "weakest": "attribute_coverage", "reasoning": "missing key attributes"}
Higher is better (1.0 = perfect MECE).
Output JSON only:"""

_CONTRARIAN_SYS = """\
You are an ontology MECE critic. Return ONLY valid JSON. No prose, no explanations, no markdown.
Example output:
{"finding": "TrainingParadigm and PerceptionComponent overlap on self-supervised tasks", "open_question": "Should SSL be in both domains?"}
Output JSON only:"""

_CRYSTALLIZE_SYS = """\
You are an ontology designer. Return ONLY valid JSON reflecting interview findings. No prose, no markdown.
Example output:
{"classes": {"Industry": {"label": "Industry", "entity_dir": "data/industry", "description": "..."}}, "object_properties": {"targets": {"label": "targets", "domain": "Competitor", "range": "Industry", "relation_name": "targets", "rollup": []}}, "datatype_properties": {"name": {"label": "name", "domain": ["Industry"], "range": "xsd:string"}}}
Output JSON only:"""


def _history_text(history: list[InterviewRound]) -> str:
    if not history:
        return "(아직 없음)"
    return "\n".join(f"Q{i+1}: {r.question}\nA{i+1}: {r.answer}" for i, r in enumerate(history))


def _heuristic_score(history: list[InterviewRound]) -> dict:
    """인터뷰 내용 기반 휴리스틱 채점 (LLM 없을 때 사용)."""
    all_answers = " ".join(r.answer for r in history).lower()
    issue_kw = ["없", "겹", "중복", "모호", "빠진", "누락", "안됨", "문제", "충돌", "애매"]
    issue_count = sum(1 for kw in issue_kw if kw in all_answers)
    me = max(0.3, 0.85 - issue_count * 0.08)
    ce = max(0.3, 0.85 - issue_count * 0.08)
    return {
        "score":     round((me + ce) / 2, 3),
        "me_score":  round(me, 3),
        "ce_score":  round(ce, 3),
        "weakest":   "ce",
        "reasoning": f"인터뷰 기반 휴리스틱 (이슈 키워드 {issue_count}개 감지)",
        "breakdown": {},
    }


def score_two_bucket(client, draft: OntologyDraft,
                     history: list[InterviewRound]) -> dict:
    if client is None:
        return _heuristic_score(history)
    user = f"Ontology draft:\n{draft.as_yaml_str()}\n\nInterview history:\n{_history_text(history)}"
    try:
        data = _parse_json(_call(client, _TWO_BUCKET_SYS, user, max_tokens=300))
    except ValueError:
        return _heuristic_score(history)

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
    if client is None:
        base = _heuristic_score(history)
        base["weakest"] = "entity_coverage"
        return base
    user = f"Ontology draft:\n{draft.as_yaml_str()}\n\nInterview history:\n{_history_text(history)}"
    try:
        data = _parse_json(_call(client, _SIX_DIM_SYS, user, max_tokens=600))
    except ValueError:
        base = _heuristic_score(history)
        base["weakest"] = "entity_coverage"
        return base

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
    if client is None:
        questions = TEMPLATE_QUESTIONS.get(weakest, TEMPLATE_QUESTIONS["ce"])
        return questions[len(history) % len(questions)]

    perspective = PERSPECTIVE.get(weakest, "MECE_REVIEWER: 구조적 문제를 찾아라")
    sys_prompt = (
        f"You are an ontology MECE interviewer. Current perspective: {perspective}\n"
        "Rules: ask exactly ONE question. No greeting, no intro, no prefix like 'Here is my question:'. "
        "Output only the question text itself."
    )
    user = (
        f"Domain: {domain}\n\n"
        f"Ontology draft:\n{draft.as_yaml_str()}\n\n"
        f"Interview history:\n{_history_text(history)}\n\n"
        "Question:"
    )
    return _call(client, sys_prompt, user, max_tokens=200)


def check_contrarian(client, draft: OntologyDraft,
                     history: list[InterviewRound]) -> dict:
    if client is None:
        return {"finding": "", "open_question": ""}
    user = f"Ontology:\n{draft.as_yaml_str()}\n\nInterview:\n{_history_text(history)}"
    try:
        return _parse_json(_call(client, _CONTRARIAN_SYS, user, max_tokens=300))
    except ValueError:
        return {"finding": "", "open_question": ""}


def crystallize(client, draft: OntologyDraft,
                history: list[InterviewRound], domain: str) -> OntologyDraft:
    if client is None:
        print("\n  [ 인터뷰 결과 요약 — 아래 내용을 반영해 graph-ontology.yaml을 직접 수정하세요 ]")
        for i, r in enumerate(history):
            print(f"  Q{i+1}: {r.question}")
            print(f"  A{i+1}: {r.answer}")
        print()
        return draft

    user = (
        f"Domain: {domain}\n"
        f"Existing draft:\n{draft.as_yaml_str()}\n\n"
        f"Interview findings to reflect:\n{_history_text(history)}"
    )
    try:
        data = _parse_json(_call(client, _CRYSTALLIZE_SYS, user, max_tokens=4096))
        return OntologyDraft(
            classes=data.get("classes") or draft.classes,
            object_properties=data.get("object_properties") or draft.object_properties,
            datatype_properties=data.get("datatype_properties") or draft.datatype_properties,
            namespace=draft.namespace,
            extra=draft.extra,
        )
    except ValueError as e:
        print(f"  [경고] 결정화 JSON 파싱 실패 — 원본 초안 유지. ({e})")
        return draft


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
    client, mode = _resolve_client()
    history: list[InterviewRound] = []
    score_data: dict = {"score": 0.0, "me_score": 0.0, "ce_score": 0.0,
                        "weakest": "ce", "reasoning": "", "breakdown": {}}

    mode_label = {"ollama": "Ollama", "anthropic": "Anthropic", "interview": "인터뷰"}.get(mode, mode)
    print(f"\n[ Medium — 최대 {cfg['max_rounds']}라운드, 게이트 ≥{cfg['gate']}, "
          f"클라이언트: {mode_label} ]")

    for rnd in range(1, cfg["max_rounds"] + 1):
        weakest = score_data["weakest"]
        question = ask_question(client, draft, history, weakest, domain)

        print(f"\n── Round {rnd}/{cfg['max_rounds']} [{weakest}] ──")
        print(f"Q: {question}")
        if _AUTO_MODE:
            answer = auto_answer(client, draft, question, domain)
            print(f"A: {answer}")
        else:
            answer = input("A: ").strip()
            if not answer:
                print("  (빈 답변 — 건너뜀)")
                continue
            print(f"   {answer}")

        history.append(InterviewRound(
            perspective=PERSPECTIVE.get(weakest, "MECE_REVIEWER"),
            question=question,
            answer=answer,
        ))

        score_data = score_two_bucket(client, draft, history)
        print(f"\n  [MECE {score_data['score']:.2f}]  "
              f"ME:{score_data['me_score']:.2f}  CE:{score_data['ce_score']:.2f}  "
              f"— {score_data['reasoning']}")

        if score_data["score"] >= cfg["gate"]:
            print(f"  ✓ 게이트 통과 (≥{cfg['gate']})")
            break

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
    client, mode = _resolve_client()
    history: list[InterviewRound] = []
    score_data: dict = {"score": 0.0, "me_score": 0.0, "ce_score": 0.0,
                        "weakest": "entity_coverage", "reasoning": "", "breakdown": {}}
    open_questions: list[str] = []

    mode_label = {"ollama": "Ollama", "anthropic": "Anthropic", "interview": "인터뷰"}.get(mode, mode)
    print(f"\n[ Deep — 최대 {cfg['max_rounds']}라운드, 게이트 ≥{cfg['gate']}, "
          f"클라이언트: {mode_label} ]")

    for rnd in range(1, cfg["max_rounds"] + 1):
        weakest = score_data["weakest"]
        question = ask_question(client, draft, history, weakest, domain)

        print(f"\n── Round {rnd}/{cfg['max_rounds']} [{weakest}] ──")
        print(f"Q: {question}")
        if _AUTO_MODE:
            answer = auto_answer(client, draft, question, domain)
            print(f"A: {answer}")
        else:
            answer = input("A: ").strip()
            if not answer:
                print("  (빈 답변 — 건너뜀)")
                continue
            print(f"   {answer}")

        history.append(InterviewRound(
            perspective=PERSPECTIVE.get(weakest, "MECE_REVIEWER"),
            question=question,
            answer=answer,
        ))

        score_data = score_six_dim(client, draft, history)
        print(f"\n  [MECE {score_data['score']:.2f}]  "
              f"ME:{score_data['me_score']:.2f}  CE:{score_data['ce_score']:.2f}  "
              f"취약: {score_data['weakest']}")

        contrarian = check_contrarian(client, draft, history)
        if contrarian.get("finding"):
            print(f"  [Contrarian] {contrarian['finding']}")
        oq = contrarian.get("open_question", "")
        if oq and oq not in open_questions:
            open_questions.append(oq)
            print(f"  [미결 질문] {oq}")

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

클라이언트 우선순위 (medium/deep):
  1. Ollama 로컬 서버 — 가용 시 사용자에게 먼저 확인
  2. Anthropic API   — ANTHROPIC_API_KEY가 설정된 경우
  3. 사용자 인터뷰    — LLM 없이 템플릿 질문으로 진행 (폴백)

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
    parser.add_argument("--ollama", action="store_true",
                        help="Ollama 로컬 서버 사용 자동 수락 (확인 프롬프트 건너뜀)")
    parser.add_argument("--auto", action="store_true",
                        help="LLM이 인터뷰 질문에 자동 답변 (비대화형 전체 자동화)")
    args = parser.parse_args()

    global _AUTO_OLLAMA, _AUTO_MODE
    if args.ollama:
        _AUTO_OLLAMA = True
    if args.auto:
        _AUTO_MODE  = True
        _AUTO_OLLAMA = True  # --auto는 항상 Ollama도 자동 수락

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
