#!/usr/bin/env python3
"""ABox 추론 + OWL HITL axiom 저작 통합 테스트 (main PRD §5 / A 작업).

인수 시나리오 (advisor 지정):
  사람이 axiom 도구로 MultimodalModel classification_rule 저작(preview→approve)
  → LLM-populated ABox 가 gemma4_e4b 사실 보유
  → materialize → inferred.jsonl 이 gemma4_e4b 가 MultimodalModel 획득을 보여줌.

검증:
  T1 (ruamel만)    axiom --apply 가 classification_rule 병합 + 사람 주석 보존
  T2 (preview)     apply 전 preview 는 definition 파일을 변경하지 않음 (HITL gate)
  T3 (linkml+owlready2+Java)  materialize → gemma4_e4b.inferred_types 에 MultimodalModel

실행: python3 tests/test_abox_reasoning.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
SCRIPTS = SK / "scripts"
FIX = Path(__file__).resolve().parent / "fixtures" / "abox_demo"


def _have(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except ImportError:
        return False


def _have_java() -> bool:
    try:
        subprocess.run(["java", "-version"], capture_output=True)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _run(*args: str):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True)


def main() -> int:
    if not _have("ruamel.yaml"):
        print("SKIP: ruamel.yaml 미설치")
        return 0

    tmp = Path(tempfile.mkdtemp(prefix="msm_abox_test_"))
    try:
        shutil.copytree(FIX, tmp / "ontology")
        def_path = tmp / "ontology" / "definition" / "modeling.yaml"

        # T2: preview (no --apply) → 파일 미변경
        before = def_path.read_text(encoding="utf-8")
        _run(str(SCRIPTS / "axiom.py"), "classification-rule", "--target", str(tmp),
             "--domain", "modeling", "--class", "MultimodalModel",
             "--is-a", "TransformerMLMModel", "--some", "canBeUsedFor:ImageGeneration")
        assert def_path.read_text(encoding="utf-8") == before, "T2 FAIL: preview가 파일 변경"
        print("[T2] preview는 definition 미변경 (HITL gate) OK")

        # T1: --apply → rule 병합 + 주석 보존
        r = _run(str(SCRIPTS / "axiom.py"), "classification-rule", "--target", str(tmp),
                 "--domain", "modeling", "--class", "MultimodalModel",
                 "--is-a", "TransformerMLMModel", "--some", "canBeUsedFor:ImageGeneration",
                 "--apply")
        after = def_path.read_text(encoding="utf-8")
        assert "classification_rules" in after, "T1 FAIL: rule 미병합"
        assert "사람이 `axiom` 도구로 대화하며 추가" in after, "T1 FAIL: 주석 소실"
        print("[T1] axiom --apply 가 rule 병합 + 사람 주석 보존 OK")

        # T3: materialize → 재분류 (linkml+owlready2+Java 필요)
        if not (_have("linkml") and _have("owlready2") and _have("rdflib") and _have_java()):
            print("[T3] SKIP: linkml/owlready2/rdflib/Java 중 일부 미설치")
        else:
            mr = _run(str(SCRIPTS / "materialize.py"), "--target", str(tmp), "--apply")
            inferred = tmp / "ontology" / "Abox" / "_inferred" / "inferred.jsonl"
            assert inferred.exists(), f"T3 FAIL: inferred.jsonl 없음\n{mr.stderr[-500:]}"
            recs = [json.loads(l) for l in inferred.read_text().splitlines() if l.strip()]
            g4 = next((r for r in recs if r["id"] == "gemma4_e4b"), None)
            assert g4 is not None, "T3 FAIL: gemma4_e4b 레코드 없음"
            assert "MultimodalModel" in g4["inferred_types"], \
                f"T3 FAIL: MultimodalModel 미추론: {g4}"
            assert "TransformerMLMModel" in g4["asserted_types"], "T3 FAIL: asserted 누락"
            print(f"[T3] materialize → gemma4_e4b {g4['asserted_types']} +추론→ "
                  f"{g4['inferred_types']} OK")

        print("\nABOX REASONING + HITL AXIOM TESTS PASS")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
