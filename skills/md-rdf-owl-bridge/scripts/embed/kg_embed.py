"""
kg_embed: KG Embedding 레이어

네 가지 백엔드를 지원:
  1. TF-IDF (기본) — numpy 만으로 동작, 즉시 사용 가능
  2. PyKEEN (선택) — TransE/RotatE/ComplEx, torch 환경 필요
  3. Semantic (선택) — SentenceTransformer, 의미 유사도
  4. Hybrid (선택) — Semantic + PyKEEN 결합, 3-tier scoring

사용처:
  - Mode B (Export): 전체 그래프 분석 + 리포트
  - Mode C (Placement): merge_candidate embed_sim 재계산
"""
from __future__ import annotations

import logging
from typing import Literal as TLiteral, Protocol, runtime_checkable

import numpy as np

from core.triple_graph import TripleGraph
from core.md_to_triple import entity_feature_dict

logger = logging.getLogger(__name__)

EmbedModel = TLiteral["TransE", "RotatE", "ComplEx", "tfidf", "semantic", "hybrid"]


# ─── Embedder Protocol ───────────────────────────────────────────────────────

@runtime_checkable
class Embedder(Protocol):
    """모든 Embedder가 공유하는 인터페이스."""

    def fit(self, graph: TripleGraph) -> None: ...

    @property
    def fitted(self) -> bool: ...


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

    def has_entity(self, entity_id: str) -> bool:
        return entity_id in self._id_to_idx

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

    def inductive_embed(
        self,
        candidate_relations: list[tuple[str, str]],
    ) -> np.ndarray | None:
        """
        그래프 밖 candidate의 이웃 관계 패턴으로 임베딩 근사.
        candidate_relations: [(relation_type, target_entity_id), ...]
        """
        if self._model is None:
            return None

        import torch

        vecs: list[np.ndarray] = []
        for rel_type, target_id in candidate_relations:
            t_vec = self.embed(target_id)
            if t_vec is not None:
                # relation 임베딩은 가용하지 않으므로 엔티티 임베딩만 사용
                vecs.append(t_vec)

        if not vecs:
            return None

        # 이웃 엔티티 임베딩의 평균 → candidate 근사 벡터
        return np.mean(vecs, axis=0)

    @property
    def fitted(self) -> bool:
        return self._model is not None


# ─── Semantic 백엔드 ──────────────────────────────────────────────────────────

class SemanticEmbedder:
    """
    SentenceTransformer 기반 의미 임베딩.
    feature_text의 의미적 유사도를 계산. 그래프 밖 candidate도 처리 가능.

    의존성: sentence-transformers (`pip install sentence-transformers`)
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or self.DEFAULT_MODEL
        self._model      = None
        self._matrix:     np.ndarray | None = None
        self._entity_ids: list[str]         = []
        self._features:   dict[str, str]    = {}   # entity_id → feature_text

    def fit(self, graph: TripleGraph):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RuntimeError(
                "sentence-transformers 미설치. "
                "`pip install sentence-transformers` 후 사용하거나 "
                "--embed-model tfidf 를 사용하세요."
            )

        self._model = SentenceTransformer(self._model_name)

        texts: list[str] = []
        ids:   list[str] = []

        for _, eid, _ in graph.iter_entities():
            feat = entity_feature_dict(eid, graph)
            texts.append(feat["feature_text"])
            ids.append(eid)
            self._features[eid] = feat["feature_text"]

        if not texts:
            logger.warning("[SemanticEmbedder] 엔티티가 없습니다.")
            return

        self._entity_ids = ids
        # 일괄 인코딩 (L2 정규화)
        self._matrix = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        logger.info(
            "[SemanticEmbedder] fit 완료: %d 엔티티, dim=%d, model=%s",
            len(ids), self._matrix.shape[1], self._model_name,
        )

    def encode(self, text: str) -> np.ndarray:
        """단일 텍스트 → 정규화된 임베딩 벡터."""
        if self._model is None:
            raise RuntimeError("fit()을 먼저 호출하세요.")
        vec = self._model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vec

    def cosine_similarity(self, vec: np.ndarray) -> list[tuple[str, float]]:
        """쿼리 벡터와 전체 엔티티의 코사인 유사도 (내림차순)."""
        if self._matrix is None:
            return []
        sims    = self._matrix @ vec
        indices = np.argsort(sims)[::-1]
        return [(self._entity_ids[i], float(sims[i])) for i in indices]

    def top_k(self, text: str, k: int = 5) -> list[tuple[str, float]]:
        """text와 가장 유사한 엔티티 k개 반환."""
        if self._matrix is None:
            return []
        vec     = self.encode(text)
        sims    = self._matrix @ vec
        indices = np.argsort(sims)[::-1][:k]
        return [(self._entity_ids[i], float(sims[i])) for i in indices]

    def similarity_between(self, text_a: str, text_b: str) -> float:
        """두 텍스트 간 코사인 유사도."""
        if self._model is None:
            raise RuntimeError("fit()을 먼저 호출하세요.")
        vecs = self._model.encode(
            [text_a, text_b],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return float(vecs[0] @ vecs[1])

    def get_feature_text(self, entity_id: str) -> str | None:
        return self._features.get(entity_id)

    @property
    def fitted(self) -> bool:
        return self._matrix is not None


# ─── Hybrid 백엔드 ────────────────────────────────────────────────────────────

class HybridEmbedder:
    """
    3-tier hybrid scoring:
      Tier 1: Semantic (SentenceTransformer) — 항상 작동, candidate 포함
      Tier 2: Structural (PyKEEN) — 그래프 내 엔티티 간 구조 유사도
      Tier 3: Alias (외부 제공) — Ralph ETL의 alias_sim

    최종 점수: w_sem * sem_sim + w_struct * struct_sim
    (struct 불가 시 w_struct=0, sem만 사용)
    """

    def __init__(
        self,
        pykeen_model: str = "TransE",
        sem_model:    str | None = None,
        pykeen_epochs: int = 100,
        w_sem:    float = 0.6,
        w_struct: float = 0.4,
    ):
        self._pykeen_model = pykeen_model
        self._sem_model    = sem_model
        self._pykeen_epochs = pykeen_epochs
        self.w_sem    = w_sem
        self.w_struct = w_struct

        self._semantic: SemanticEmbedder | None = None
        self._pykeen:   PyKEENEmbedder | None   = None
        self._tfidf:    TFIDFEmbedder | None    = None   # ultimate fallback

    def fit(self, graph: TripleGraph):
        # Tier 1: Semantic — 필수
        try:
            self._semantic = SemanticEmbedder(self._sem_model)
            self._semantic.fit(graph)
            logger.info("[HybridEmbedder] Tier 1 (Semantic) 준비 완료")
        except (ImportError, RuntimeError) as e:
            logger.warning(
                "[HybridEmbedder] Semantic 실패 (%s). TF-IDF로 폴백.", e
            )
            self._semantic = None
            self._tfidf = TFIDFEmbedder()
            self._tfidf.fit(graph)
            logger.info("[HybridEmbedder] Tier 1 폴백 (TF-IDF) 준비 완료")

        # Tier 2: Structural — 선택
        try:
            self._pykeen = PyKEENEmbedder(
                model_name=self._pykeen_model,
                epochs=self._pykeen_epochs,
            )
            self._pykeen.fit(graph)
            logger.info("[HybridEmbedder] Tier 2 (PyKEEN %s) 준비 완료", self._pykeen_model)
        except (ImportError, RuntimeError, ValueError) as e:
            logger.warning(
                "[HybridEmbedder] PyKEEN 실패 (%s). Semantic 단독 모드.", e
            )
            self._pykeen = None

    def compute_hybrid_similarity(
        self,
        candidate_text: str,
        target_id:      str,
        graph:          TripleGraph,
        candidate_relations: list[tuple[str, str]] | None = None,
    ) -> dict:
        """
        3-tier hybrid 유사도 계산.

        반환:
          {
            "final_sim": float,
            "sem_sim": float,
            "struct_sim": float | None,
            "tier_used": str,            # "semantic+structural" | "semantic" | "tfidf"
            "weights": {"sem": float, "struct": float},
          }
        """
        result = {
            "final_sim":  0.0,
            "sem_sim":    0.0,
            "struct_sim": None,
            "tier_used":  "none",
            "weights":    {"sem": self.w_sem, "struct": self.w_struct},
        }

        # ── Tier 1: Semantic ────────────────────────────────────────────────────
        sem_sim = 0.0
        if self._semantic is not None and self._semantic.fitted:
            target_feat = self._semantic.get_feature_text(target_id)
            if target_feat:
                sem_sim = self._semantic.similarity_between(candidate_text, target_feat)
            else:
                # target이 그래프에 없으면 entity_feature_dict으로 구성 시도
                feat = entity_feature_dict(target_id, graph) if graph.entity_exists(target_id) else None
                if feat:
                    sem_sim = self._semantic.similarity_between(
                        candidate_text, feat["feature_text"]
                    )
            result["sem_sim"] = float(sem_sim)
            result["tier_used"] = "semantic"
        elif self._tfidf is not None and self._tfidf.fitted:
            # Semantic 실패 → TF-IDF 폴백
            q_vec = self._tfidf.encode(candidate_text)
            for eid, sim in self._tfidf.cosine_similarity(q_vec):
                if eid == target_id:
                    sem_sim = sim
                    break
            result["sem_sim"] = float(sem_sim)
            result["tier_used"] = "tfidf"

        # ── Tier 2: Structural (PyKEEN) ─────────────────────────────────────────
        struct_sim = None
        if self._pykeen is not None and self._pykeen.fitted:
            if self._pykeen.has_entity(target_id):
                # candidate 관계 정보로 inductive embedding 시도
                if candidate_relations:
                    cand_vec = self._pykeen.inductive_embed(candidate_relations)
                    if cand_vec is not None:
                        t_vec = self._pykeen.embed(target_id)
                        if t_vec is not None:
                            cn = np.linalg.norm(cand_vec)
                            tn = np.linalg.norm(t_vec)
                            if cn > 0 and tn > 0:
                                struct_sim = float(
                                    (cand_vec / cn) @ (t_vec / tn)
                                )
                                result["struct_sim"] = struct_sim
                                result["tier_used"] = (
                                    result["tier_used"] + "+structural"
                                    if result["tier_used"] != "none"
                                    else "structural"
                                )

        # ── Final score ─────────────────────────────────────────────────────────
        if struct_sim is not None:
            w_s = self.w_sem
            w_t = self.w_struct
            result["final_sim"] = w_s * sem_sim + w_t * struct_sim
        else:
            # structural 불가 → semantic만 사용 (가중치 재정규화)
            result["final_sim"] = sem_sim
            result["weights"] = {"sem": 1.0, "struct": 0.0}

        return result

    def top_k(self, text: str, k: int = 5) -> list[tuple[str, float]]:
        """text와 가장 유사한 엔티티 k개 반환 (Semantic 기반)."""
        if self._semantic is not None and self._semantic.fitted:
            return self._semantic.top_k(text, k)
        if self._tfidf is not None and self._tfidf.fitted:
            return self._tfidf.top_k(text, k)
        return []

    @property
    def fitted(self) -> bool:
        sem_ok = (self._semantic is not None and self._semantic.fitted)
        tfidf_ok = (self._tfidf is not None and self._tfidf.fitted)
        return sem_ok or tfidf_ok


# ─── 팩토리 함수 ──────────────────────────────────────────────────────────────

AnyEmbedder = TFIDFEmbedder | PyKEENEmbedder | SemanticEmbedder | HybridEmbedder


def build_embedder(
    model_name: EmbedModel,
    graph:      TripleGraph,
) -> AnyEmbedder:
    """
    model_name에 따라 적절한 Embedder를 생성 후 fit하여 반환.
    PyKEEN/Semantic 환경 없으면 TF-IDF로 자동 폴백.
    """
    if model_name == "tfidf":
        emb = TFIDFEmbedder()
        emb.fit(graph)
        return emb

    if model_name == "semantic":
        try:
            emb = SemanticEmbedder()
            emb.fit(graph)
            return emb
        except (ImportError, RuntimeError) as e:
            logger.warning(
                "[build_embedder] Semantic 실패 (%s). TF-IDF 폴백.", e
            )
            emb_fb = TFIDFEmbedder()
            emb_fb.fit(graph)
            return emb_fb

    if model_name == "hybrid":
        emb = HybridEmbedder()
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
    embedder:       AnyEmbedder,
    graph:          TripleGraph,
    candidate_relations: list[tuple[str, str]] | None = None,
) -> float:
    """
    candidate_text(자유 텍스트)와 target_id 엔티티 간 코사인 유사도 계산.
    모든 백엔드를 통일된 인터페이스로 처리.
    """
    # ── HybridEmbedder ──────────────────────────────────────────────────────
    if isinstance(embedder, HybridEmbedder):
        result = embedder.compute_hybrid_similarity(
            candidate_text, target_id, graph, candidate_relations,
        )
        logger.debug(
            "[compute_similarity] Hybrid: final=%.4f sem=%.4f struct=%s tier=%s",
            result["final_sim"], result["sem_sim"],
            result["struct_sim"], result["tier_used"],
        )
        return result["final_sim"]

    # ── SemanticEmbedder ────────────────────────────────────────────────────
    if isinstance(embedder, SemanticEmbedder):
        target_feat = embedder.get_feature_text(target_id)
        if target_feat:
            return embedder.similarity_between(candidate_text, target_feat)
        # target이 그래프에 있지만 캐시되지 않은 경우
        feat = entity_feature_dict(target_id, graph) if graph.entity_exists(target_id) else None
        if feat:
            return embedder.similarity_between(candidate_text, feat["feature_text"])
        return 0.0

    # ── TFIDFEmbedder ───────────────────────────────────────────────────────
    if isinstance(embedder, TFIDFEmbedder):
        q_vec = embedder.encode(candidate_text)
        ranked = embedder.cosine_similarity(q_vec)
        for eid, sim in ranked:
            if eid == target_id:
                return float(sim)
        return 0.0

    # ── PyKEENEmbedder (단독) ───────────────────────────────────────────────
    if isinstance(embedder, PyKEENEmbedder):
        # candidate의 관계 정보로 inductive embedding 시도
        if candidate_relations:
            cand_vec = embedder.inductive_embed(candidate_relations)
            if cand_vec is not None:
                t_vec = embedder.embed(target_id)
                if t_vec is not None:
                    cn = np.linalg.norm(cand_vec)
                    tn = np.linalg.norm(t_vec)
                    if cn > 0 and tn > 0:
                        return float((cand_vec / cn) @ (t_vec / tn))

        logger.debug(
            "[compute_similarity] PyKEEN: candidate 관계 없음 또는 "
            "inductive embed 실패 → 0.0"
        )
        return 0.0

    return 0.0
