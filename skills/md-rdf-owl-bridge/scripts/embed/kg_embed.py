"""
kg_embed: KG Embedding 레이어

두 가지 백엔드를 지원:
  1. TF-IDF (기본) — numpy/scipy 만으로 동작, 즉시 사용 가능
  2. PyKEEN (선택) — TransE/RotatE/ComplEx, torch 환경 필요

사용처:
  - Mode B (Export): 전체 그래프 분석 + 리포트
  - Mode C (Placement): merge_candidate embed_sim 재계산
"""
from __future__ import annotations

import logging
from typing import Literal as TLiteral

import numpy as np

from core.triple_graph import TripleGraph
from core.md_to_triple import entity_feature_dict

logger = logging.getLogger(__name__)

EmbedModel = TLiteral["TransE", "RotatE", "ComplEx", "tfidf"]


# ─── TF-IDF 백엔드 ────────────────────────────────────────────────────────────

class TFIDFEmbedder:
    """
    엔티티 feature_text를 TF-IDF 벡터로 변환 후 코사인 유사도를 계산.
    추가 의존성 없이 동작하는 baseline 백엔드.
    """

    def __init__(self):
        self._matrix:    np.ndarray | None = None
        self._entity_ids: list[str]        = []
        self._vocab:     dict[str, int]    = {}
        self._idf:       np.ndarray | None = None

    def fit(self, graph: TripleGraph):
        """TripleGraph의 모든 엔티티로 TF-IDF 행렬 구축."""
        corpus: list[str] = []
        ids:    list[str] = []

        for _, eid, _ in graph.iter_entities():
            feat = entity_feature_dict(eid, graph)
            corpus.append(feat["feature_text"])
            ids.append(eid)

        if not corpus:
            logger.warning("[TFIDFEmbedder] 엔티티가 없습니다.")
            return

        self._entity_ids = ids
        self._matrix, self._idf, self._vocab = _tfidf_fit_transform(corpus)
        logger.info(
            "[TFIDFEmbedder] fit 완료: %d 엔티티, vocab %d",
            len(ids), len(self._vocab),
        )

    def encode(self, text: str) -> np.ndarray:
        """단일 텍스트 → TF-IDF 벡터 (정규화)."""
        if self._vocab is None or self._idf is None:
            raise RuntimeError("fit()을 먼저 호출하세요.")
        vec = _tfidf_transform_single(text, self._vocab, self._idf)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def cosine_similarity(self, vec: np.ndarray) -> list[tuple[str, float]]:
        """
        쿼리 벡터와 전체 엔티티의 코사인 유사도 계산.
        반환: [(entity_id, sim), ...] 내림차순 정렬
        """
        if self._matrix is None:
            return []
        sims    = self._matrix @ vec                  # (n,) 벡터
        indices = np.argsort(sims)[::-1]              # 전체 정렬 대신 numpy argsort
        return [(self._entity_ids[i], float(sims[i])) for i in indices]

    def top_k(self, text: str, k: int = 5) -> list[tuple[str, float]]:
        """text와 가장 유사한 엔티티 k개 반환."""
        if self._matrix is None:
            return []
        vec     = self.encode(text)
        sims    = self._matrix @ vec
        indices = np.argsort(sims)[::-1][:k]          # 상위 k만 슬라이스
        return [(self._entity_ids[i], float(sims[i])) for i in indices]

    @property
    def fitted(self) -> bool:
        return self._matrix is not None


# ─── TF-IDF 내부 구현 ─────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def _tfidf_fit_transform(
    corpus: list[str],
) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    """corpus → (L2-정규화된 TF-IDF 행렬, IDF 벡터, vocab dict)"""
    import math

    # vocab 구축
    vocab: dict[str, int] = {}
    for doc in corpus:
        for tok in _tokenize(doc):
            if tok not in vocab:
                vocab[tok] = len(vocab)

    V = len(vocab)
    N = len(corpus)

    # TF 행렬
    tf = np.zeros((N, V), dtype=np.float32)
    for i, doc in enumerate(corpus):
        tokens = _tokenize(doc)
        if not tokens:
            continue
        for tok in tokens:
            if tok in vocab:
                tf[i, vocab[tok]] += 1
        tf[i] /= len(tokens)

    # IDF 벡터
    df = (tf > 0).sum(axis=0).astype(np.float32)
    idf = np.log((N + 1) / (df + 1)) + 1.0

    # TF-IDF
    tfidf = tf * idf

    # L2 정규화
    norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    tfidf /= norms

    return tfidf, idf, vocab


def _tfidf_transform_single(
    text: str,
    vocab: dict[str, int],
    idf:   np.ndarray,
) -> np.ndarray:
    tokens = _tokenize(text)
    vec = np.zeros(len(vocab), dtype=np.float32)
    if not tokens:
        return vec
    for tok in tokens:
        if tok in vocab:
            vec[vocab[tok]] += 1
    vec /= len(tokens)
    return vec * idf


# ─── PyKEEN 백엔드 ────────────────────────────────────────────────────────────

class PyKEENEmbedder:
    """
    PyKEEN TransE/RotatE/ComplEx 래퍼.
    torch + pykeen 환경에서만 동작. 없으면 TFIDFEmbedder로 자동 폴백.
    """

    def __init__(self, model_name: str = "TransE", epochs: int = 100):
        self.model_name  = model_name
        self.epochs      = epochs
        self._model      = None
        self._entity_ids: list[str]  = []
        self._id_to_idx:  dict[str, int] = {}

    def fit(self, graph: TripleGraph):
        try:
            import torch  # noqa: F401
            from pykeen.pipeline import pipeline
            from pykeen.triples import TriplesFactory
        except ImportError:
            raise RuntimeError(
                "PyKEEN/torch 미설치. `pip install pykeen torch` 후 사용하거나 "
                "--embed-model tfidf 를 사용하세요."
            )

        # Triple 목록 수집
        triples_list: list[tuple[str, str, str]] = []
        for s_id, p_local, o_id in graph.iter_relations():
            triples_list.append((s_id, p_local, o_id))

        if not triples_list:
            raise ValueError("관계 Triple이 없어 PyKEEN 학습 불가.")

        triples_array = np.array(triples_list)
        tf = TriplesFactory.from_labeled_triples(triples_array)

        result = pipeline(
            training=tf,
            model=self.model_name,
            epochs=self.epochs,
            random_seed=42,
        )
        self._model = result.model
        self._entity_ids = list(tf.entity_to_id.keys())
        self._id_to_idx  = {eid: idx for eid, idx in tf.entity_to_id.items()}
        logger.info("[PyKEENEmbedder] 학습 완료: %d 엔티티", len(self._entity_ids))

    def embed(self, entity_id: str) -> np.ndarray | None:
        if self._model is None or entity_id not in self._id_to_idx:
            return None
        import torch
        idx    = self._id_to_idx[entity_id]
        tensor = self._model.entity_representations[0](
            torch.tensor([idx])
        ).detach().cpu().numpy()[0]
        return tensor

    def cosine_similarity_to(self, entity_id: str) -> list[tuple[str, float]]:
        vec = self.embed(entity_id)
        if vec is None:
            return []
        norm = np.linalg.norm(vec)
        if norm == 0:
            return []
        vec = vec / norm

        results: list[tuple[str, float]] = []
        for eid in self._entity_ids:
            if eid == entity_id:
                continue
            v2 = self.embed(eid)
            if v2 is None:
                continue
            n2 = np.linalg.norm(v2)
            if n2 == 0:
                continue
            sim = float(vec @ (v2 / n2))
            results.append((eid, sim))

        return sorted(results, key=lambda x: x[1], reverse=True)

    @property
    def fitted(self) -> bool:
        return self._model is not None


# ─── 팩토리 함수 ──────────────────────────────────────────────────────────────

def build_embedder(
    model_name: EmbedModel,
    graph:      TripleGraph,
) -> TFIDFEmbedder | PyKEENEmbedder:
    """
    model_name에 따라 적절한 Embedder를 생성 후 fit하여 반환.
    PyKEEN 환경 없으면 TF-IDF로 자동 폴백.
    """
    if model_name == "tfidf":
        emb = TFIDFEmbedder()
        emb.fit(graph)
        return emb

    # TransE / RotatE / ComplEx → PyKEEN 시도
    try:
        emb_kgem = PyKEENEmbedder(model_name=model_name)
        emb_kgem.fit(graph)
        return emb_kgem
    except (ImportError, RuntimeError, ValueError) as e:
        logger.warning(
            "[build_embedder] PyKEEN 실패 (%s). TF-IDF 폴백.", e
        )
        emb_tfidf = TFIDFEmbedder()
        emb_tfidf.fit(graph)
        return emb_tfidf


def compute_similarity(
    candidate_text: str,
    target_id:      str,
    embedder:       TFIDFEmbedder | PyKEENEmbedder,
    graph:          TripleGraph,
) -> float:
    """
    candidate_text(자유 텍스트)와 target_id 엔티티 간 코사인 유사도 계산.
    두 백엔드를 통일된 인터페이스로 처리.
    """
    if isinstance(embedder, TFIDFEmbedder):
        q_vec = embedder.encode(candidate_text)
        ranked = embedder.cosine_similarity(q_vec)
        for eid, sim in ranked:
            if eid == target_id:
                return float(sim)
        return 0.0

    if isinstance(embedder, PyKEENEmbedder):
        feat   = entity_feature_dict(target_id, graph) if graph.entity_exists(target_id) else None
        t_vec  = embedder.embed(target_id)
        if t_vec is None:
            return 0.0
        # candidate는 그래프에 없으므로 feature_text → TF-IDF fallback
        logger.debug(
            "[compute_similarity] PyKEEN: candidate는 그래프 외부 → 유사도 0.0"
        )
        return 0.0

    return 0.0
