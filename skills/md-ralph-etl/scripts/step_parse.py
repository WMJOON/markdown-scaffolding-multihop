"""Step D — Entity Parsing: rule + dictionary + pattern based extraction.

LLM is only allowed for type judgment / normalization assist (not used here).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ralph.common import (
    EntityCandidate,
    ONTOLOGY_ENTITIES_DIR,
    RelationCandidate,
    RunConfig,
    RunState,
)
from ralph.yaml_io import read_jsonl, write_jsonl


# ---------------------------------------------------------------------------
# Ontology loading
# ---------------------------------------------------------------------------

def load_ontology_node_types(root: Path) -> Dict[str, str]:
    """Load node types from graph-ontology.yaml. Returns {type_key: dir_path}."""
    ontology_path = root / "graph-ontology.yaml"
    types: Dict[str, str] = {}
    if not ontology_path.exists():
        return types

    text = ontology_path.read_text(encoding="utf-8")
    in_nodes = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "nodes:":
            in_nodes = True
            continue
        if stripped == "relations:":
            in_nodes = False
            continue
        if in_nodes and ":" in stripped and not stripped.startswith("-"):
            if "path:" in stripped:
                # "path: data/ontology-entities/Work"
                path_val = stripped.split("path:", 1)[1].strip()
                if types:
                    last_key = list(types.keys())[-1]
                    types[last_key] = path_val
            else:
                key = stripped.rstrip(":").strip()
                types[key] = ""
    return types


def load_existing_entities(root: Path, include_summary: bool = False) -> Dict[str, Dict]:
    """Load all existing entity IDs, labels, and aliases.

    Returns {entity_id: {label_en, label_ko, aliases, entity_type, relpath}}.
    When include_summary=True, also includes a 'summary' key with the first
    non-empty non-heading body paragraph.
    """
    entities_dir = root / ONTOLOGY_ENTITIES_DIR
    if not entities_dir.exists():
        return {}

    entities: Dict[str, Dict] = {}
    for md_file in entities_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue

        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        fm = parts[1]
        body = parts[2]

        eid = ""
        etype = ""
        label_en = ""
        label_ko = ""
        aliases: List[str] = []
        in_aliases = False

        for line in fm.splitlines():
            line_s = line.strip()
            if line_s.startswith("entity_id:"):
                eid = line_s.split(":", 1)[1].strip().strip('"').strip("'")
                in_aliases = False
            elif line_s.startswith("entity_type:"):
                etype = line_s.split(":", 1)[1].strip().strip('"').strip("'")
                in_aliases = False
            elif line_s.startswith("label_en:"):
                label_en = line_s.split(":", 1)[1].strip().strip('"').strip("'")
                in_aliases = False
            elif line_s.startswith("label_ko:"):
                label_ko = line_s.split(":", 1)[1].strip().strip('"').strip("'")
                in_aliases = False
            elif line_s.startswith("aliases:"):
                in_aliases = True
            elif in_aliases and line_s.startswith("- "):
                aliases.append(line_s[2:].strip().strip('"').strip("'"))
            elif not line_s.startswith("- ") and ":" in line_s:
                in_aliases = False

        if eid:
            entry: Dict = {
                "label_en": label_en,
                "label_ko": label_ko,
                "aliases": aliases,
                "entity_type": etype,
                "relpath": str(md_file.relative_to(root)),
            }
            if include_summary:
                summary = ""
                for bline in body.strip().splitlines():
                    bline_s = bline.strip()
                    if bline_s and not bline_s.startswith("#"):
                        summary = bline_s
                        break
                entry["summary"] = summary
            entities[eid] = entry
    return entities


_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")


def extract_wikilink_mentions(text: str) -> List[str]:
    """Extract wikilink targets from text."""
    return _WIKILINK_RE.findall(text)


# ---------------------------------------------------------------------------
# Entity ID generation
# ---------------------------------------------------------------------------

def generate_entity_id(
    entity_type: str,
    label: str,
    existing_ids: Set[str],
) -> str:
    """Generate entity_id: {entity_type_lower}__{slug}.

    Follows existing codebase convention.
    """
    type_prefix = entity_type.lower()
    # convert CamelCase to snake_case
    type_prefix = re.sub(r"([a-z])([A-Z])", r"\1_\2", type_prefix).lower()

    slug = label.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = slug.strip("_")[:80]

    eid = f"{type_prefix}__{slug}"
    if eid not in existing_ids:
        return eid

    # collision: append counter
    for n in range(2, 100):
        candidate = f"{eid}__{n}"
        if candidate not in existing_ids:
            return candidate
    return eid


# ---------------------------------------------------------------------------
# Entity extraction patterns — per entity type
# ---------------------------------------------------------------------------

# Known model name dictionary (canonical names + common abbreviations)
# Used for high-precision dictionary matching in text
_KNOWN_MODEL_NAMES: List[str] = [
    # Transformers / LLMs (4+ chars, unambiguous names only)
    "Transformer", "BERT", "GPT-2", "GPT-3", "GPT-4", "GPT-4o", "GPT-4V",
    "LLaMA", "LLaMA 2", "LLaMA 3", "Llama 2", "Llama 3",
    "Mistral", "Mixtral", "Gemma 2", "Phi-3",
    "DeepSeek", "DeepSeek-R1", "Qwen2", "Qwen2.5",
    "BART", "RoBERTa", "DeBERTa", "XLNet", "ALBERT",
    "Falcon", "Vicuna", "Alpaca",
    # Vision
    "ResNet", "VGGNet", "AlexNet", "EfficientNet", "MobileNet",
    "Vision Transformer", "DeiT", "Swin Transformer",
    "CLIP", "DINOv2", "Segment Anything",
    "YOLO", "YOLOv8", "Faster R-CNN", "Mask R-CNN", "DETR",
    # Diffusion / Generative
    "Stable Diffusion", "DALL-E", "Midjourney", "Imagen",
    "DDPM", "DDIM", "Latent Diffusion", "ControlNet",
    "DreamBooth", "LoRA", "QLoRA",
    "StyleGAN", "CycleGAN", "VQGAN", "VQ-VAE",
    "Variational Autoencoder",
    # Graph Neural Networks
    "Graph Neural Network", "Graph Convolutional Network", "Graph Attention Network",
    "GraphSAGE", "STGCN", "DCRNN",
    "Spatio-Temporal Graph Convolutional Network",
    "Diffusion Convolutional Recurrent Neural Network",
    # Recurrent / Sequential
    "LSTM", "BiLSTM", "Seq2Seq",
    "Long Short-Term Memory", "Gated Recurrent Unit",
    "Temporal Convolutional Network",
    # Time Series / Forecasting
    "Prophet", "ARIMA", "SARIMA", "N-BEATS", "Informer",
    "Autoformer", "FEDformer", "PatchTST", "TimesNet",
    # Reinforcement Learning
    "DQN", "DDPG", "MADDPG",
    "Deep Q-Network", "Proximal Policy Optimization",
    "Soft Actor-Critic",
    # Tree-based / Classical ML
    "XGBoost", "LightGBM", "CatBoost", "Random Forest",
    "Gradient Boosting", "Support Vector Machine",
    "Linear Regression", "Logistic Regression",
    # Clustering
    "K-Means", "DBSCAN", "HDBSCAN",
    # Autoencoder / Representation
    "Autoencoder", "Sparse Autoencoder", "Denoising Autoencoder",
    # Mixture of Experts
    "Mixture of Experts", "Switch Transformer",
    # Multimodal
    "LLaVA", "Flamingo", "BLIP-2", "InstructBLIP",
    "Whisper", "Wav2Vec",
    # State Space Models
    "Mamba", "State Space Model",
    # Neural ODE / Physics
    "Neural ODE", "Neural SDE", "NeRF",
    # Flow-based
    "Normalizing Flow", "RealNVP", "GFlowNet",
    # Transport domain specific
    "STResNet", "ConvLSTM", "ST-ResNet",
    "DMVST-Net", "CSTN",
]

# Build regex pattern from known model names (longest first to avoid partial matches)
_KNOWN_MODEL_NAMES_SORTED = sorted(_KNOWN_MODEL_NAMES, key=len, reverse=True)
_KNOWN_MODEL_RE = re.compile(
    r"\b(" + "|".join(re.escape(n) for n in _KNOWN_MODEL_NAMES_SORTED) + r")\b",
    re.IGNORECASE,
)

# Fallback pattern for unknown model names (high-precision: requires explicit context)
_MODEL_PATTERN_FALLBACK = re.compile(
    r"(?:propose[sd]?|present[s]?|introduce[sd]?|develop[s]?|design[s]?)\s+"
    r"(?:a\s+)?(?:novel\s+)?(?:new\s+)?"
    r"([A-Z][A-Z0-9\-]{1,20}(?:\s+[A-Z][a-zA-Z0-9\-]+){0,2})"
    r"(?=\s*,|\s+model|\s+network|\s+architecture|\s+framework)",
    re.IGNORECASE,
)

# Task/capability patterns
_TASK_PATTERN = re.compile(
    r"(?:for|applied to|performs?|enables?|supports?)\s+"
    r"([\w\s]+?(?:detection|classification|forecasting|optimization|"
    r"recognition|generation|retrieval|segmentation|translation|"
    r"summarization|prediction|estimation|planning))",
    re.IGNORECASE,
)

# Dataset patterns
_DATASET_PATTERN = re.compile(
    r"(?:(?i:dataset|benchmark|corpus|trained on|evaluated on|tested on))\s+"
    r"([A-Z][a-zA-Z0-9\-]+(?:\s+[A-Z][a-zA-Z0-9\-]+){0,3})",
)

# Metric patterns
_METRIC_PATTERN = re.compile(
    r"(?:accuracy|precision|recall|F1|BLEU|ROUGE|perplexity|AUC|"
    r"mAP|IoU|FID|IS|SSIM|PSNR|WER|CER|latency|throughput)"
    r"\s*(?:of|=|:)?\s*([0-9]+\.?[0-9]*\s*%?)",
    re.IGNORECASE,
)

# ModelFamily patterns
_FAMILY_PATTERN = re.compile(
    r"(?:family of|class of|type of|category of|architecture:?)\s+"
    r"([\w\s\-]+?(?:model|network|architecture|framework)s?)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Concept extraction — dictionary + fallback pattern
# ---------------------------------------------------------------------------

_KNOWN_CONCEPT_NAMES: List[str] = [
    # Memory types (cognitive science taxonomy)
    "Short-Term Memory", "Long-Term Memory", "Working Memory",
    "Episodic Memory", "Semantic Memory", "Procedural Memory",
    "Sensory Memory", "Declarative Memory",
    # Agent memory taxonomy (functional)
    "Factual Memory", "Experiential Memory",
    "Token-Level Memory", "Parametric Memory", "Latent Memory",
    # Memory operations
    "Memory Consolidation", "Memory Retrieval", "Memory Formation",
    "Memory Evolution", "Memory Automation", "Memory Compaction",
    "Context Compression", "Memory Reflection",
    # Architecture concepts
    "Virtual Context Management", "Hierarchical Memory",
    "Memory Hierarchy", "Context Window Management",
    "In-Context Memory", "Out-of-Context Memory",
    "Memory Buffer", "Memory Tier",
    # Retrieval / search
    "Similarity Search", "Embedding-Based Retrieval",
    "Adaptive Retrieval Gating", "Retention Regularization",
    # Multi-agent
    "Multi-Agent Memory", "Shared Memory", "Collective Memory",
    # Learning / adaptation
    "Single-Shot Learning", "Continual Learning",
    "Self-Evolving Memory", "Memory Reinforcement Learning",
    # Multimodal
    "Multimodal Memory",
    # Trust / safety
    "Memory Trustworthiness", "Memory Privacy",
]

_KNOWN_CONCEPT_NAMES_SORTED = sorted(_KNOWN_CONCEPT_NAMES, key=len, reverse=True)
_KNOWN_CONCEPT_RE = re.compile(
    r"\b(" + "|".join(re.escape(n) for n in _KNOWN_CONCEPT_NAMES_SORTED) + r")\b",
    re.IGNORECASE,
)

# Fallback: "X memory" pattern for undiscovered concepts
_CONCEPT_PATTERN_FALLBACK = re.compile(
    r"\b((?:[A-Z][a-z]+[\-\s]){0,2}[A-Z][a-z]+)\s+"
    r"(?:memory|memories)\b",
)

# ---------------------------------------------------------------------------
# Framework extraction — dictionary + fallback pattern
# ---------------------------------------------------------------------------

_KNOWN_FRAMEWORK_NAMES: List[str] = [
    # Memory frameworks
    "MemGPT", "A-MEM", "Letta", "LangMem",
    "MAGMA", "EverMemOS", "MemRL", "MemEvolve",
    # Agent frameworks with memory
    "LangChain", "LangGraph", "AutoGen", "CrewAI",
    "BabyAGI", "AgentGPT", "MetaGPT",
    # Memory-specific systems
    "Mem0", "Zep", "Motorhead",
    "Zettelkasten",
    # Retrieval / RAG
    "RAG", "Retrieval-Augmented Generation",
    "GraphRAG", "HyDE",
]

_KNOWN_FRAMEWORK_NAMES_SORTED = sorted(_KNOWN_FRAMEWORK_NAMES, key=len, reverse=True)
_KNOWN_FRAMEWORK_RE = re.compile(
    r"\b(" + "|".join(re.escape(n) for n in _KNOWN_FRAMEWORK_NAMES_SORTED) + r")\b",
)

# Fallback: "propose/present X framework/system/architecture"
# Requires first captured word to start with uppercase and be ≥3 chars (filters "a", "an", "the")
_FRAMEWORK_PATTERN_FALLBACK = re.compile(
    r"(?:propose[sd]?|present[s]?|introduce[sd]?|develop[s]?)\s+"
    r"(?:a\s+)?(?:novel\s+)?(?:new\s+)?"
    r"([A-Z][A-Za-z0-9\-]{2,25}(?:\s+[A-Z][a-zA-Z0-9\-]+){0,2})"
    r"(?=\s*,|\s+(?:framework|system|architecture|platform|method|approach|mechanism))",
    re.IGNORECASE,
)

# Concept names that are too generic and should be filtered from fallback pattern
_CONCEPT_GENERIC_STOPWORDS = {
    # Determiners / pronouns
    "current", "this", "that", "their", "our", "its", "other",
    "the", "a", "an", "some", "all", "each", "every",
    # Adjectives too vague for concept names
    "new", "recent", "existing", "traditional", "various",
    "main", "key", "core", "basic", "simple", "complex",
    "effective", "efficient", "additional", "similar",
    "deep", "mixed", "multiple", "representative",
    # Conjunctions / prepositions / adverbs leaked by regex
    "although", "because", "does", "how", "when", "within",
    "without", "unlike", "toward", "on", "three",
    # Verbs / gerunds
    "exploring", "evaluating", "understanding", "rethinking",
    "synergizing", "bridging", "learning",
    # Noise from PDF parsing artifacts
    "fact", "preference",
}

# Patterns registry: maps entity type → (regex, predicate, new_entity_type)
# Note: Model is handled separately via dictionary matching in extract_entity_candidates_from_chunk
# Note: Concept and Framework also use dictionary matching (like Model) + fallback patterns
# Note: ModelFamily pattern is disabled — regex-based family extraction produces too much noise;
#       ModelFamily entities are managed manually based on confirmed taxonomy
_PATTERN_REGISTRY = {
    "Work": (_TASK_PATTERN, "targets_work", "Work"),
    "Dataset": (_DATASET_PATTERN, "uses_dataset", "Dataset"),
}

_DATASET_LEADING_STOPWORDS = {
    "a", "an", "the", "this", "that", "these", "those",
    "in", "on", "for", "of", "with", "as", "and", "or", "to", "from",
}

_DATASET_GENERIC_SINGLE = {
    "dataset", "datasets", "benchmark", "benchmarks", "corpus", "corpora",
    "model", "models", "problem", "problems", "data",
}


def _is_plausible_dataset_name(name: str) -> bool:
    """Heuristic filter to reduce noisy Dataset candidates."""
    tokens = [t for t in re.split(r"\s+", name.strip()) if t]
    if not tokens:
        return False
    if len(tokens) > 6:
        return False

    lowered = [
        re.sub(r"[^a-z0-9]+", "", t.lower())
        for t in tokens
    ]
    lowered = [t for t in lowered if t]
    if not lowered:
        return False
    if lowered[0] in _DATASET_LEADING_STOPWORDS:
        return False
    if len(lowered) == 1 and lowered[0] in _DATASET_GENERIC_SINGLE:
        return False

    has_digit = any(any(ch.isdigit() for ch in t) for t in tokens)
    has_acronym = any(t.isupper() and len(t) >= 2 for t in tokens)
    has_inner_upper = any(any(ch.isupper() for ch in t[1:]) for t in tokens)

    # Accept title-case multiword names like "Penn Treebank".
    has_multi_title = (
        len(tokens) >= 2
        and all(t[0].isupper() for t in tokens[:2] if t and t[0].isalpha())
    )

    return has_digit or has_acronym or has_inner_upper or has_multi_title


def extract_entity_candidates_from_chunk(
    chunk: Dict,
    existing_entities: Dict[str, Dict],
    existing_ids: Set[str],
    scope_targets: Optional[List[str]] = None,
    global_label_to_eid: Optional[Dict[str, str]] = None,
    existing_by_type: Optional[Dict[str, Dict[str, Dict]]] = None,
) -> Tuple[List[EntityCandidate], List[RelationCandidate]]:
    """Extract entity and relation candidates from a single chunk.

    scope_targets controls which entity types to extract. If None, all types.
    """
    text = chunk.get("text", "")
    doc_id = chunk.get("doc_id", "")
    chunk_id = chunk.get("chunk_id", "")
    section = chunk.get("section_path", "")

    entity_cands: List[EntityCandidate] = []
    relation_cands: List[RelationCandidate] = []

    span_ref = f"{chunk_id}:{section}"

    # 1. Wikilink-based detection (always active)
    wikilinks = extract_wikilink_mentions(text)
    for ref in wikilinks:
        basename = ref.split("/")[-1] if "/" in ref else ref
        if basename in existing_entities:
            relation_cands.append(RelationCandidate(
                candidate_id=hashlib.sha256(
                    f"rel:{doc_id}:{basename}:{chunk_id}".encode()
                ).hexdigest()[:16],
                source_entity_id=doc_id,
                predicate="references",
                target_entity_id=basename,
                evidence_spans=[span_ref],
                confidence=0.9,
            ))

    # 2. Pattern-based extraction — filtered by scope_targets
    active_types = set(scope_targets) if scope_targets else set(_PATTERN_REGISTRY.keys())

    # Model extraction: dictionary-first, then fallback pattern
    if "Model" in active_types:
        global_label_to_eid = global_label_to_eid or {}
        existing_models = (existing_by_type or {}).get("Model", existing_entities)
        seen_model_names_in_chunk: Set[str] = set()

        def _handle_model_candidate(name: str, confidence: float) -> None:
            """Create or reuse entity candidate for a model name."""
            name_key = name.lower()
            if name_key in seen_model_names_in_chunk:
                return
            seen_model_names_in_chunk.add(name_key)

            matched_eid = _match_existing(name, existing_models)
            if matched_eid:
                relation_cands.append(RelationCandidate(
                    candidate_id=hashlib.sha256(
                        f"rel:Model:{doc_id}:{matched_eid}:{chunk_id}".encode()
                    ).hexdigest()[:16],
                    source_entity_id=doc_id,
                    predicate="targets_model",
                    target_entity_id=matched_eid,
                    evidence_spans=[span_ref],
                    confidence=confidence,
                ))
            else:
                global_key = f"Model:{name_key}"
                if global_key in global_label_to_eid:
                    # Entity already created in a previous chunk — just add evidence
                    existing_ec_id = global_label_to_eid[global_key]
                    # Add a relation pointing to the already-created entity
                    # (dedup in run_parse will merge evidence spans)
                    entity_cands.append(EntityCandidate(
                        candidate_id=hashlib.sha256(
                            f"ent:Model:{name}:{chunk_id}".encode()
                        ).hexdigest()[:16],
                        entity_id=existing_ec_id,
                        entity_type="Model",
                        label_en=name,
                        label_ko="",
                        evidence_spans=[span_ref],
                        source_doc_id=doc_id,
                        confidence=confidence,
                    ))
                else:
                    eid = generate_entity_id("Model", name, existing_ids)
                    global_label_to_eid[global_key] = eid
                    existing_ids.add(eid)
                    entity_cands.append(EntityCandidate(
                        candidate_id=hashlib.sha256(
                            f"ent:Model:{name}:{chunk_id}".encode()
                        ).hexdigest()[:16],
                        entity_id=eid,
                        entity_type="Model",
                        label_en=name,
                        label_ko="",
                        evidence_spans=[span_ref],
                        source_doc_id=doc_id,
                        confidence=confidence,
                    ))

        # 2a. Known model dictionary matching (high precision)
        for m in _KNOWN_MODEL_RE.finditer(text):
            _handle_model_candidate(m.group(1).strip(), 0.85)

        # 2b. Fallback pattern disabled — too noisy across diverse paper domains
        # Only dictionary-based matching (2a) is used for Model entity creation

    # Concept extraction: dictionary-first + fallback "X memory" pattern
    if "Concept" in active_types:
        global_label_to_eid = global_label_to_eid or {}
        existing_concepts = (existing_by_type or {}).get("Concept", existing_entities)
        seen_concept_names_in_chunk: Set[str] = set()

        def _handle_concept_candidate(name: str, confidence: float) -> None:
            name_key = name.lower()
            if name_key in seen_concept_names_in_chunk:
                return
            seen_concept_names_in_chunk.add(name_key)

            matched_eid = _match_existing(name, existing_concepts)
            if matched_eid:
                relation_cands.append(RelationCandidate(
                    candidate_id=hashlib.sha256(
                        f"rel:Concept:{doc_id}:{matched_eid}:{chunk_id}".encode()
                    ).hexdigest()[:16],
                    source_entity_id=doc_id,
                    predicate="describes_concept",
                    target_entity_id=matched_eid,
                    evidence_spans=[span_ref],
                    confidence=confidence,
                ))
            else:
                global_key = f"Concept:{name_key}"
                if global_key in global_label_to_eid:
                    entity_cands.append(EntityCandidate(
                        candidate_id=hashlib.sha256(
                            f"ent:Concept:{name}:{chunk_id}".encode()
                        ).hexdigest()[:16],
                        entity_id=global_label_to_eid[global_key],
                        entity_type="Concept",
                        label_en=name,
                        label_ko="",
                        evidence_spans=[span_ref],
                        source_doc_id=doc_id,
                        confidence=confidence,
                    ))
                else:
                    eid = generate_entity_id("Concept", name, existing_ids)
                    global_label_to_eid[global_key] = eid
                    existing_ids.add(eid)
                    entity_cands.append(EntityCandidate(
                        candidate_id=hashlib.sha256(
                            f"ent:Concept:{name}:{chunk_id}".encode()
                        ).hexdigest()[:16],
                        entity_id=eid,
                        entity_type="Concept",
                        label_en=name,
                        label_ko="",
                        evidence_spans=[span_ref],
                        source_doc_id=doc_id,
                        confidence=confidence,
                    ))

        # 2c. Known concept dictionary matching
        for m in _KNOWN_CONCEPT_RE.finditer(text):
            _handle_concept_candidate(m.group(1).strip(), 0.85)

        # 2d. Fallback "X Memory" pattern (moderate precision, filtered)
        for m in _CONCEPT_PATTERN_FALLBACK.finditer(text):
            adj = m.group(1).strip()
            if adj.lower() in _CONCEPT_GENERIC_STOPWORDS:
                continue
            name = f"{adj} Memory"
            if name.lower() not in seen_concept_names_in_chunk:
                _handle_concept_candidate(name, 0.6)

    # Framework extraction: dictionary-first + fallback pattern
    if "Framework" in active_types:
        global_label_to_eid = global_label_to_eid or {}
        existing_frameworks = (existing_by_type or {}).get("Framework", existing_entities)
        seen_framework_names_in_chunk: Set[str] = set()

        def _handle_framework_candidate(name: str, confidence: float) -> None:
            name_key = name.lower()
            if name_key in seen_framework_names_in_chunk:
                return
            seen_framework_names_in_chunk.add(name_key)

            matched_eid = _match_existing(name, existing_frameworks)
            if matched_eid:
                relation_cands.append(RelationCandidate(
                    candidate_id=hashlib.sha256(
                        f"rel:Framework:{doc_id}:{matched_eid}:{chunk_id}".encode()
                    ).hexdigest()[:16],
                    source_entity_id=doc_id,
                    predicate="implements_framework",
                    target_entity_id=matched_eid,
                    evidence_spans=[span_ref],
                    confidence=confidence,
                ))
            else:
                global_key = f"Framework:{name_key}"
                if global_key in global_label_to_eid:
                    entity_cands.append(EntityCandidate(
                        candidate_id=hashlib.sha256(
                            f"ent:Framework:{name}:{chunk_id}".encode()
                        ).hexdigest()[:16],
                        entity_id=global_label_to_eid[global_key],
                        entity_type="Framework",
                        label_en=name,
                        label_ko="",
                        evidence_spans=[span_ref],
                        source_doc_id=doc_id,
                        confidence=confidence,
                    ))
                else:
                    eid = generate_entity_id("Framework", name, existing_ids)
                    global_label_to_eid[global_key] = eid
                    existing_ids.add(eid)
                    entity_cands.append(EntityCandidate(
                        candidate_id=hashlib.sha256(
                            f"ent:Framework:{name}:{chunk_id}".encode()
                        ).hexdigest()[:16],
                        entity_id=eid,
                        entity_type="Framework",
                        label_en=name,
                        label_ko="",
                        evidence_spans=[span_ref],
                        source_doc_id=doc_id,
                        confidence=confidence,
                    ))

        # 2e. Known framework dictionary matching
        for m in _KNOWN_FRAMEWORK_RE.finditer(text):
            _handle_framework_candidate(m.group(1).strip(), 0.85)

        # 2f. Fallback "propose/present X framework/system" pattern
        #     Skip if name is already a known Concept (avoid type confusion)
        _concept_names_lower = {n.lower() for n in _KNOWN_CONCEPT_NAMES}
        for m in _FRAMEWORK_PATTERN_FALLBACK.finditer(text):
            name = m.group(1).strip()
            if name.lower() in _concept_names_lower:
                continue
            _handle_framework_candidate(name, 0.6)

    # Other types (Work, Dataset, ModelFamily)
    for target_type, (pattern, predicate, new_type) in _PATTERN_REGISTRY.items():
        if target_type == "Model":
            continue  # handled above
        if target_type not in active_types:
            continue
        existing_of_type = (existing_by_type or {}).get(target_type, existing_entities)
        for m in pattern.finditer(text):
            name = m.group(1).strip()
            if len(name) < 2:
                continue
            if target_type == "Dataset" and not _is_plausible_dataset_name(name):
                continue
            matched_eid = _match_existing(name, existing_of_type)
            if matched_eid:
                relation_cands.append(RelationCandidate(
                    candidate_id=hashlib.sha256(
                        f"rel:{target_type}:{doc_id}:{matched_eid}:{chunk_id}".encode()
                    ).hexdigest()[:16],
                    source_entity_id=doc_id,
                    predicate=predicate,
                    target_entity_id=matched_eid,
                    evidence_spans=[span_ref],
                    confidence=0.8,
                ))
            elif target_type in (scope_targets or list(_PATTERN_REGISTRY.keys())):
                # only create new entities for explicitly targeted types
                eid = generate_entity_id(new_type, name, existing_ids)
                entity_cands.append(EntityCandidate(
                    candidate_id=hashlib.sha256(
                        f"ent:{new_type}:{name}:{chunk_id}".encode()
                    ).hexdigest()[:16],
                    entity_id=eid,
                    entity_type=new_type,
                    label_en=name,
                    label_ko="",
                    evidence_spans=[span_ref],
                    source_doc_id=doc_id,
                    confidence=0.6,
                ))
                existing_ids.add(eid)

    # 3. Metric extraction (if Metric in scope or always as metadata)
    for m in _METRIC_PATTERN.finditer(text):
        metric_name = m.group(0).split("=")[0].split(":")[0].strip()
        value = m.group(1).strip()
        # store as relation metadata, not as entity candidate
        relation_cands.append(RelationCandidate(
            candidate_id=hashlib.sha256(
                f"rel:metric:{doc_id}:{metric_name}:{chunk_id}".encode()
            ).hexdigest()[:16],
            source_entity_id=doc_id,
            predicate="reports_metric",
            target_entity_id=f"metric__{metric_name.lower().replace(' ', '_')}",
            evidence_spans=[f"{span_ref}:value={value}"],
            confidence=0.7,
        ))

    return entity_cands, relation_cands


def _match_existing(
    name: str,
    existing_of_type: Dict[str, Dict],
) -> Optional[str]:
    """Try to match a name against pre-filtered existing entities (single type).

    existing_of_type must already be filtered to the target entity_type.
    """
    name_lower = name.lower().replace("-", "_").replace(" ", "_")

    for eid, info in existing_of_type.items():
        # exact match on entity_id suffix
        eid_suffix = eid.split("__", 1)[-1] if "__" in eid else eid
        if name_lower == eid_suffix:
            return eid
        # label match
        label = (info.get("label_en") or "").lower()
        if label and name_lower == label.lower().replace(" ", "_"):
            return eid
    return None


# ---------------------------------------------------------------------------
# Step handler
# ---------------------------------------------------------------------------

def run_parse(
    root: Path,
    state: RunState,
    config: RunConfig,
    run_dir: Path,
    apply: bool,
) -> RunState:
    """Step D: Entity Parsing — extract candidates from chunks."""
    chunks_path = run_dir / "evidence_corpus" / "chunks" / "all_chunks.jsonl"
    if not chunks_path.exists():
        print("[Ralph] Parse: no chunks found")
        return state

    chunks = read_jsonl(chunks_path)
    existing = load_existing_entities(root)
    existing_ids = set(existing.keys())

    # Pre-index by entity_type for O(N/k) lookup in _match_existing
    existing_by_type: Dict[str, Dict[str, Dict]] = {}
    for eid, info in existing.items():
        existing_by_type.setdefault(info.get("entity_type", ""), {})[eid] = info

    # load scope targets
    scope_targets: Optional[List[str]] = None
    meta_path = run_dir / ".run_meta.json"
    if meta_path.exists():
        import json
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        scope_targets = meta.get("scope_targets")
    if config.scope_targets:
        scope_targets = list(config.scope_targets)

    all_entity_cands: List[Dict] = []
    all_relation_cands: List[Dict] = []

    # Global label→eid map to prevent duplicate entity creation across chunks
    # Key: (entity_type, label_lower), Value: entity_id
    global_label_to_eid: Dict[str, str] = {}

    for chunk in chunks:
        ent_cands, rel_cands = extract_entity_candidates_from_chunk(
            chunk, existing, existing_ids, scope_targets, global_label_to_eid,
            existing_by_type,
        )
        all_entity_cands.extend([asdict(c) for c in ent_cands])
        all_relation_cands.extend([asdict(c) for c in rel_cands])

    # deduplicate entity candidates by entity_id (safety net), merge evidence spans
    deduped_map: Dict[str, Dict] = {}
    for ec in all_entity_cands:
        eid = ec["entity_id"]
        if eid in deduped_map:
            deduped_map[eid]["evidence_spans"].extend(ec["evidence_spans"])
        else:
            deduped_map[eid] = ec
    deduped_entities: List[Dict] = list(deduped_map.values())

    write_jsonl(run_dir / "entity_candidates.jsonl", deduped_entities)
    write_jsonl(run_dir / "relation_candidates.jsonl", all_relation_cands)

    state.metrics.entities_processed = len(deduped_entities)
    state.metrics.relations_processed = len(all_relation_cands)

    print(
        f"[Ralph] Parse: {len(deduped_entities)} entity candidates, "
        f"{len(all_relation_cands)} relation candidates"
    )
    return state
