"""Similarity engines: Levenshtein + TF-IDF + BERT (3-tier).

Tier 1 — Lexical: Levenshtein (stdlib, 항상 사용)
Tier 2 — Sparse Semantic: TF-IDF cosine (stdlib, 항상 사용)
Tier 3 — Dense Semantic: BERT 계열 모델 (torch 필요, opt-in)

BERT 엔진은 subprocess로 bert_embed_worker.py를 호출하여 scipy/sklearn
code-signing 충돌을 우회한다. torch가 없으면 자동으로 TF-IDF fallback.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SparseVector = Dict[str, float]
DenseVector = List[float]

_WORKER_PATH = Path(__file__).resolve().parent / "bert_embed_worker.py"


# ---------------------------------------------------------------------------
# Tier 1 — Lexical Similarity (Levenshtein)
# ---------------------------------------------------------------------------

def levenshtein_distance(s1: str, s2: str) -> int:
    """Standard DP Levenshtein distance."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if not s2:
        return len(s1)

    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            cost = 0 if c1 == c2 else 1
            curr.append(min(
                curr[j] + 1,          # insert
                prev[j + 1] + 1,      # delete
                prev[j] + cost,       # replace
            ))
        prev = curr
    return prev[-1]


def normalize_for_comparison(text: str) -> str:
    """Lowercase, collapse whitespace/underscores/hyphens, strip punctuation."""
    t = text.lower()
    t = re.sub(r"[_\-\s]+", " ", t)
    t = re.sub(r"[^\w\s]", "", t)
    return t.strip()


def normalized_levenshtein(s1: str, s2: str) -> float:
    """1.0 - (distance / max(len(s1), len(s2))). 1.0 = identical."""
    a = normalize_for_comparison(s1)
    b = normalize_for_comparison(s2)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    dist = levenshtein_distance(a, b)
    max_len = max(len(a), len(b))
    return 1.0 - dist / max_len


def alias_similarity(
    candidate_labels: List[str],
    existing_labels: List[str],
) -> float:
    """Max normalized Levenshtein across all label pairs."""
    if not candidate_labels or not existing_labels:
        return 0.0
    best = 0.0
    for cl in candidate_labels:
        for el in existing_labels:
            sim = normalized_levenshtein(cl, el)
            if sim > best:
                best = sim
                if best >= 1.0:
                    return 1.0
    return best


# ---------------------------------------------------------------------------
# Tier 2 — TF-IDF Sparse Semantic Similarity (stdlib)
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-zA-Z가-힣0-9]+")


def _word_unigrams(text: str) -> List[str]:
    return [m.group().lower() for m in _TOKEN_RE.finditer(text)]


def _char_ngrams(text: str, n: int = 3) -> List[str]:
    t = f" {text.lower()} "
    return [t[i : i + n] for i in range(len(t) - n + 1)]


def _extract_features(text: str) -> Counter:
    features: Counter = Counter()
    features.update(_word_unigrams(text))
    features.update(_char_ngrams(text, 3))
    return features


class TFIDFEngine:
    """Corpus-level TF-IDF vectorizer, pure stdlib."""

    def __init__(self, max_features: int = 50000):
        self.idf: Dict[str, float] = {}
        self.doc_count: int = 0
        self.max_features = max_features

    def fit(self, documents: List[str]) -> None:
        df: Counter = Counter()
        self.doc_count = len(documents)
        for doc in documents:
            features = _extract_features(doc)
            df.update(features.keys())

        if len(df) > self.max_features:
            top = df.most_common(self.max_features)
            df = Counter(dict(top))

        self.idf = {}
        for term, count in df.items():
            self.idf[term] = math.log((self.doc_count + 1) / (count + 1)) + 1

    def transform(self, text: str) -> SparseVector:
        features = _extract_features(text)
        total = sum(features.values()) or 1
        vec: SparseVector = {}
        for term, count in features.items():
            if term in self.idf:
                vec[term] = (count / total) * self.idf[term]
        return vec

    def cosine_similarity(self, v1: SparseVector, v2: SparseVector) -> float:
        if not v1 or not v2:
            return 0.0
        common = set(v1.keys()) & set(v2.keys())
        dot = sum(v1[k] * v2[k] for k in common)
        norm1 = math.sqrt(sum(val * val for val in v1.values()))
        norm2 = math.sqrt(sum(val * val for val in v2.values()))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return dot / (norm1 * norm2)

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        v1 = self.transform(text_a)
        v2 = self.transform(text_b)
        return self.cosine_similarity(v1, v2)


# ---------------------------------------------------------------------------
# Tier 3 — BERT Dense Semantic Similarity (subprocess)
# ---------------------------------------------------------------------------

def _dense_cosine(v1: DenseVector, v2: DenseVector) -> float:
    """Pure-Python cosine similarity for dense vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = math.sqrt(sum(a * a for a in v1))
    n2 = math.sqrt(sum(b * b for b in v2))
    if n1 == 0.0 or n2 == 0.0:
        return 0.0
    return dot / (n1 * n2)


class BERTEngine:
    """BERT 계열 모델 임베딩 — subprocess로 bert_embed_worker.py 호출.

    모델은 최초 호출 시 HuggingFace에서 자동 다운로드되며,
    ~/.cache/ralph-embeddings/ 에 캐시된다.

    Supported models:
        - sentence-transformers/all-MiniLM-L6-v2  (384d, 가장 빠름)
        - BAAI/bge-base-en-v1.5                   (768d, 고품질)
        - BAAI/bge-small-en-v1.5                  (384d, 균형)
        - intfloat/multilingual-e5-small           (384d, 다국어)
    """

    def __init__(
        self,
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        timeout: int = 120,
    ):
        self.model = model
        self.timeout = timeout
        self._available: Optional[bool] = None
        self._cache: Dict[str, DenseVector] = {}

    def is_available(self) -> bool:
        """torch가 설치되어 있고 worker가 실행 가능한지 확인."""
        if self._available is not None:
            return self._available
        try:
            result = subprocess.run(
                ["python3", str(_WORKER_PATH), "--model", self.model, "--dim"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            self._available = result.returncode == 0
            if self._available:
                info = json.loads(result.stdout.strip())
                print(
                    f"[BERT] {info.get('model')} ready "
                    f"(dim={info.get('dimension')}, device={info.get('device')})"
                )
        except Exception:
            self._available = False
        return self._available

    def embed(self, text: str) -> Optional[DenseVector]:
        """단일 텍스트 임베딩. 캐시 사용."""
        if text in self._cache:
            return self._cache[text]
        try:
            result = subprocess.run(
                ["python3", str(_WORKER_PATH), "--model", self.model],
                input=text,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if result.returncode != 0:
                return None
            data = json.loads(result.stdout.strip())
            vec = data.get("vector")
            if vec:
                self._cache[text] = vec
            return vec
        except Exception:
            return None

    def embed_batch(self, texts: List[str]) -> List[Optional[DenseVector]]:
        """배치 임베딩. 캐시 미스만 worker에 보냄."""
        results: List[Optional[DenseVector]] = [None] * len(texts)
        to_compute: List[Tuple[int, str]] = []

        for i, text in enumerate(texts):
            if text in self._cache:
                results[i] = self._cache[text]
            else:
                to_compute.append((i, text))

        if not to_compute:
            return results

        # prepare JSONL input
        jsonl_input = "\n".join(
            json.dumps({"id": str(idx), "text": text}, ensure_ascii=False)
            for idx, text in to_compute
        )

        try:
            result = subprocess.run(
                ["python3", str(_WORKER_PATH), "--model", self.model, "--batch"],
                input=jsonl_input,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if result.returncode != 0:
                return results

            for line in result.stdout.strip().splitlines():
                data = json.loads(line)
                idx = int(data.get("id", -1))
                vec = data.get("vector")
                if vec and 0 <= idx < len(texts):
                    results[idx] = vec
                    self._cache[texts[idx]] = vec
        except Exception:
            pass

        return results

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """두 텍스트의 BERT cosine similarity."""
        vecs = self.embed_batch([text_a, text_b])
        if vecs[0] is None or vecs[1] is None:
            return 0.0
        return _dense_cosine(vecs[0], vecs[1])

    def similarity_from_worker(self, text_a: str, text_b: str) -> float:
        """Worker의 --similarity 모드 직접 호출 (단건 최적화)."""
        try:
            result = subprocess.run(
                [
                    "python3", str(_WORKER_PATH),
                    "--model", self.model,
                    "--similarity", text_a, text_b,
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if result.returncode != 0:
                return 0.0
            data = json.loads(result.stdout.strip())
            return float(data.get("similarity", 0.0))
        except Exception:
            return 0.0


# ---------------------------------------------------------------------------
# Unified Engine — 3-tier 자동 선택
# ---------------------------------------------------------------------------

class SimilarityEngine:
    """3-tier similarity engine with automatic fallback.

    embed_mode:
        "auto"  — BERT 사용 가능하면 BERT, 아니면 TF-IDF (기본)
        "bert"  — BERT 강제 (실패 시 에러)
        "tfidf" — TF-IDF만 사용 (기존 동작)
    """

    def __init__(
        self,
        embed_mode: str = "auto",
        bert_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.embed_mode = embed_mode
        self.tfidf = TFIDFEngine()
        self.bert: Optional[BERTEngine] = None
        self._use_bert = False

        if embed_mode in ("auto", "bert"):
            self.bert = BERTEngine(model=bert_model)
            if embed_mode == "auto":
                self._use_bert = self.bert.is_available()
            else:
                if not self.bert.is_available():
                    raise RuntimeError(
                        f"BERT mode requested but torch/transformers not available"
                    )
                self._use_bert = True

        if not self._use_bert:
            print("[Similarity] Using TF-IDF engine (Tier 2)")
        else:
            print(f"[Similarity] Using BERT engine (Tier 3): {bert_model}")

    def fit(self, documents: List[str]) -> None:
        """TF-IDF corpus fit (BERT는 pre-trained이므로 fit 불필요)."""
        self.tfidf.fit(documents)

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """embed_sim: BERT 또는 TF-IDF cosine."""
        if self._use_bert and self.bert:
            sim = self.bert.compute_similarity(text_a, text_b)
            if sim > 0.0:
                return sim
            # BERT 실패 시 TF-IDF fallback
        return self.tfidf.compute_similarity(text_a, text_b)

    def embed_batch(self, texts: List[str]) -> List[Optional[DenseVector]]:
        """배치 임베딩 (BERT only). TF-IDF 모드에서는 None 리스트 반환."""
        if self._use_bert and self.bert:
            return self.bert.embed_batch(texts)
        return [None] * len(texts)

    @property
    def engine_name(self) -> str:
        return "bert" if self._use_bert else "tfidf"
