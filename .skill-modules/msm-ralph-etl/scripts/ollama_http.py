"""Python → ollama HTTP 클라이언트 (로컬 LLM 위임 계층).

올바른 작업만 위임한다 (ollama-delegate SKILL 기준):
  - 2,000자 초과 섹션 요약
  - 개념/키워드 추출

(a) http://localhost:11434 직접 호출 우선.
(b) 연결 실패 시 호출부에서 .sidecar_pending.json 기록 → Claude MCP fallback.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Dict, List, Optional

OLLAMA_BASE = "http://localhost:11434"
DEFAULT_MODEL = "gemma4:e4b"
_CONNECT_TIMEOUT = 3    # is_available 전용
_GENERATE_TIMEOUT = 120


class OllamaUnavailableError(RuntimeError):
    """ollama 서버에 연결할 수 없을 때."""


# ---------------------------------------------------------------------------
# 연결 확인
# ---------------------------------------------------------------------------

def is_available() -> bool:
    try:
        urllib.request.urlopen(f"{OLLAMA_BASE}/api/tags", timeout=_CONNECT_TIMEOUT)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 기본 generate
# ---------------------------------------------------------------------------

def generate(
    prompt: str,
    model: str = DEFAULT_MODEL,
    timeout: int = _GENERATE_TIMEOUT,
) -> str:
    """ollama /api/generate 호출. 실패 시 OllamaUnavailableError."""
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read()).get("response", "").strip()
    except urllib.error.URLError as exc:
        raise OllamaUnavailableError(f"ollama 연결 실패: {exc}") from exc
    except Exception as exc:
        raise OllamaUnavailableError(f"ollama 호출 오류: {exc}") from exc


# ---------------------------------------------------------------------------
# 섹션 요약
# ---------------------------------------------------------------------------

def summarize_text(
    text: str,
    context_label: str = "",
    model: str = DEFAULT_MODEL,
    max_input_chars: int = 20_000,
) -> str:
    """텍스트를 요약. 원문 전문 용어·모델명은 그대로 유지."""
    label_hint = f"섹션: {context_label}\n\n" if context_label else ""
    prompt = (
        f"{label_hint}"
        f"다음 논문 내용을 핵심만 3-5문장으로 요약하세요. "
        f"전문 용어, 모델명, 수치는 원문 그대로 유지하세요.\n\n"
        f"---\n{text[:max_input_chars]}\n---\n\n요약:"
    )
    return generate(prompt, model)


# ---------------------------------------------------------------------------
# 개념 추출
# ---------------------------------------------------------------------------

def extract_concepts(
    text: str,
    model: str = DEFAULT_MODEL,
    max_input_chars: int = 8_000,
) -> List[Dict]:
    """텍스트에서 개념·모델명·기술 용어를 추출.

    Returns:
        [{"concept": str, "type": "model|dataset|task|metric|other"}]
    """
    prompt = (
        "다음 텍스트에서 주요 개념을 추출하세요. "
        "모델명, 데이터셋명, 태스크, 메트릭, 기술 용어를 포함합니다.\n"
        "JSON 배열로만 응답하세요 (다른 텍스트 없이):\n"
        '[{"concept": "...", "type": "model|dataset|task|metric|other"}]\n\n'
        f"텍스트:\n{text[:max_input_chars]}\n\nJSON:"
    )
    raw = generate(prompt, model)

    # JSON 배열 추출 — LLM이 앞뒤에 텍스트를 붙이는 경우 대비
    match = re.search(r"\[.*?\]", raw, re.DOTALL)
    if not match:
        return []
    try:
        items = json.loads(match.group())
        if not isinstance(items, list):
            return []
        return [
            {"concept": str(it.get("concept", "")), "type": str(it.get("type", "other"))}
            for it in items
            if it.get("concept")
        ]
    except (json.JSONDecodeError, AttributeError):
        return []
