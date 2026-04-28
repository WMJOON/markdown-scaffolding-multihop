"""Shared data structures, enums, and constants for Ralph ETL."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class StepName(Enum):
    RUN_CREATED = "RUN_CREATED"
    A_INTAKE = "A_INTAKE"
    B_CRAWL = "B_CRAWL"
    C_PREPROCESS = "C_PREPROCESS"
    D_PARSE = "D_PARSE"
    # v0.1 — 3 steps inserted between D_PARSE and H_PLACE
    E_CONCEPT_MAP = "E_CONCEPT_MAP"
    F_DEDUPLICATE = "F_DEDUPLICATE"
    G_VALIDATE = "G_VALIDATE"
    H_PLACE = "H_PLACE"
    I_SEAL = "I_SEAL"
    # legacy aliases kept for backward-compat (not in STEP_ORDER)
    E_PLACE = "E_PLACE"
    F_SEAL = "F_SEAL"
    DONE = "DONE"
    RUN_FAILED = "RUN_FAILED"


class RunMode(str, Enum):
    """Pipeline operation mode."""
    FULL = "full"              # URL → crawl → parse → place → seal (기본)
    LOCAL = "local"            # 로컬 파일 → preprocess → parse → place → seal
    ENRICH = "enrich"          # 기존 엔티티 관계 보강만 (parse → place만)


class InputFormat(str, Enum):
    """Supported manifest/input formats."""
    TSV = "tsv"
    JSONL = "jsonl"
    DIRECTORY = "directory"    # 로컬 디렉토리 스캔


class EmbedMode(str, Enum):
    """Similarity engine selection."""
    AUTO = "auto"     # BERT if available, else TF-IDF
    BERT = "bert"     # BERT only (RuntimeError if unavailable)
    TFIDF = "tfidf"   # TF-IDF only


class FetcherMode(str, Enum):
    """HTTP fetcher tier selection."""
    AUTO = "auto"         # source_type 기반 자동 선택
    BASIC = "basic"       # TLS 스푸핑 HTTP
    STEALTHY = "stealthy" # 반봇 우회
    DYNAMIC = "dynamic"   # JS 렌더링 (Playwright)


class PlacementLabel(Enum):
    NEW = "new"
    EXTEND = "extend"
    MERGE_CANDIDATE = "merge_candidate"
    MERGE = "merge"
    RELATION_ONLY = "relation_only"
    REJECT = "reject"
    HOLD = "hold"


STEP_ORDER: List[StepName] = [
    StepName.A_INTAKE,
    StepName.B_CRAWL,
    StepName.C_PREPROCESS,
    StepName.D_PARSE,
    StepName.E_CONCEPT_MAP,
    StepName.F_DEDUPLICATE,
    StepName.G_VALIDATE,
    StepName.H_PLACE,
    StepName.I_SEAL,
]

RUNS_ARCHIVE_DIR = Path("archive") / "history" / "ralph-runs"
ONTOLOGY_ENTITIES_DIR = Path("data") / "ontology-entities"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class RunConfig:
    batch_size: int = 20
    max_retry: int = 3
    ambiguity_threshold: float = 0.35
    chunk_max_words: int = 400
    chunk_overlap_words: int = 50
    chunk_min_words: int = 40
    llm_call_ratio_limit: float = 0.05
    hold_ratio_limit: float = 0.20
    merge_alias_sim_threshold: float = 0.92
    extend_alias_sim_threshold: float = 0.80
    relation_embed_sim_threshold: float = 0.75
    http_timeout: int = 40
    # v0.0.3 확장: 다양한 사용 모드
    run_mode: str = RunMode.FULL
    input_format: str = InputFormat.TSV
    scope_targets: List[str] = field(default_factory=list)  # 대상 entity type 직접 지정
    file_extensions: List[str] = field(      # local 모드에서 스캔할 확장자
        default_factory=lambda: [".md", ".txt", ".html", ".pdf"]
    )
    embed_mode: str = EmbedMode.AUTO
    bert_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    fetcher_mode: str = FetcherMode.AUTO


# ---------------------------------------------------------------------------
# Run State
# ---------------------------------------------------------------------------

@dataclass
class Checkpoint:
    step: str
    artifact: str
    idempotency_key: str
    completed_at: str = ""


@dataclass
class RunMetrics:
    llm_call_count: int = 0
    llm_call_ratio: float = 0.0
    cache_hit_ratio: float = 0.0
    hold_count: int = 0
    hold_ratio: float = 0.0
    entities_processed: int = 0
    relations_processed: int = 0


@dataclass
class BatchInfo:
    batch_id: str
    urls: List[str] = field(default_factory=list)
    scope_targets: List[str] = field(default_factory=list)
    url_fingerprints: List[str] = field(default_factory=list)


@dataclass
class GovernanceEvent:
    event_type: str  # "hitl_request" | "approval" | "rejection"
    gate: str  # "H1" | "H2"
    reason: str
    requires_manual_confirmation: bool = True
    resolved: bool = False
    resolved_by: str = ""
    timestamp: str = ""


@dataclass
class RunState:
    ralph_run_id: str
    parent_run_id: Optional[str] = None
    started_at: str = ""
    status: str = "RUN_CREATED"
    attempt: int = 1
    max_retry: int = 3
    input_snapshot_hash: str = ""
    config_hash: str = ""
    code_ref: str = ""
    batch: Optional[BatchInfo] = None
    config: Optional[RunConfig] = None
    checkpoints: List[Checkpoint] = field(default_factory=list)
    metrics: RunMetrics = field(default_factory=RunMetrics)
    governance_events: List[GovernanceEvent] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pipeline Data Types
# ---------------------------------------------------------------------------

@dataclass
class URLEntry:
    url: str
    normalized_url: str
    url_fingerprint: str
    source_type: str
    case_id: str
    title: str
    industry_mapping: str
    start_marker: str = ""
    tags: List[str] = field(default_factory=list)
    license_hint: str = ""
    priority: int = 0
    collected_at: str = ""
    skip_reason: Optional[str] = None


@dataclass
class DocIndex:
    doc_id: str
    title: str
    organization: str
    date: str
    headings: List[str] = field(default_factory=list)
    doc_type: str = ""
    length: int = 0
    outbound_links: List[str] = field(default_factory=list)


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    section_path: str
    text: str
    word_count: int
    start_line: int
    end_line: int
    metadata_prefix: str = ""


@dataclass
class EntityCandidate:
    candidate_id: str
    entity_id: str
    entity_type: str
    label_en: str
    label_ko: str
    aliases: List[str] = field(default_factory=list)
    evidence_spans: List[str] = field(default_factory=list)
    source_doc_id: str = ""
    confidence: float = 0.0
    source_refs: List[str] = field(default_factory=list)
    relations: List[Dict[str, str]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationCandidate:
    candidate_id: str
    source_entity_id: str
    predicate: str
    target_entity_id: str
    evidence_spans: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class PlacementResult:
    candidate_id: str
    label: str
    target_existing_id: Optional[str] = None
    alias_sim: float = 0.0
    embed_sim: float = 0.0
    evidence_count: int = 0
    conflict_layer: Optional[str] = None
    reason: str = ""


@dataclass
class HoldEntry:
    hold_id: str
    entity_candidate_id: str
    reason: str
    ambiguity_ratio: float
    created_at: str
    source_batch: str
    ttl_batches: int = 5
    resolution: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None


@dataclass
class ValidationResult:
    check_id: str
    name: str
    passed: bool
    blocking: bool
    details: str = ""
