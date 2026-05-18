#!/usr/bin/env python3
"""Standalone BERT embedding worker — subprocess로 호출되어 임베딩 벡터를 반환.

Ralph의 similarity.py에서 subprocess로 호출한다.
in-process import 시 scipy/sklearn 충돌을 회피하기 위해 별도 프로세스로 분리.

Usage:
    # 단일 텍스트 → 벡터 (JSON stdout)
    echo "transformer architecture" | python3 bert_embed_worker.py

    # 배치 (JSONL stdin → JSONL stdout)
    python3 bert_embed_worker.py --batch < texts.jsonl > vectors.jsonl

    # 두 텍스트 간 cosine similarity
    python3 bert_embed_worker.py --similarity "text A" "text B"

    # 모델 지정
    python3 bert_embed_worker.py --model sentence-transformers/all-MiniLM-L6-v2

Supported models (auto-download on first use):
    - sentence-transformers/all-MiniLM-L6-v2  (default, 384d, 22M params)
    - BAAI/bge-base-en-v1.5                   (768d, 109M params)
    - BAAI/bge-small-en-v1.5                  (384d, 33M params)
    - intfloat/multilingual-e5-small           (384d, multilingual)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_DIR = Path.home() / ".cache" / "ralph-embeddings"


def _load_model(model_name: str):
    """Load tokenizer and model using raw torch + transformers."""
    import torch

    # transformers AutoModel import를 지연시켜 sklearn 충돌을 우회
    # torch만으로 모델 로딩
    try:
        from transformers import AutoTokenizer, AutoModel
        tokenizer = AutoTokenizer.from_pretrained(
            model_name, cache_dir=str(CACHE_DIR)
        )
        model = AutoModel.from_pretrained(
            model_name, cache_dir=str(CACHE_DIR)
        )
    except ImportError:
        print(
            json.dumps({"error": "transformers not installed"}),
            file=sys.stderr,
        )
        sys.exit(1)

    model.eval()
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = model.to(device)
    return tokenizer, model, device


def embed_texts(
    texts: list[str], tokenizer, model, device: str
) -> list[list[float]]:
    """Encode texts into embedding vectors via mean pooling."""
    import torch

    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )
    encoded = {k: v.to(device) for k, v in encoded.items()}

    with torch.no_grad():
        outputs = model(**encoded)

    # mean pooling over token embeddings (masked)
    token_embeds = outputs.last_hidden_state
    attention_mask = encoded["attention_mask"].unsqueeze(-1)
    masked = token_embeds * attention_mask
    summed = masked.sum(dim=1)
    counts = attention_mask.sum(dim=1).clamp(min=1e-9)
    embeddings = summed / counts

    # L2 normalize
    norms = torch.nn.functional.normalize(embeddings, p=2, dim=1)
    return norms.cpu().tolist()


def cosine_sim(v1: list[float], v2: list[float]) -> float:
    """Pure-Python cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = sum(a * a for a in v1) ** 0.5
    n2 = sum(b * b for b in v2) ** 0.5
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="BERT embedding worker")
    parser.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"HuggingFace model (default: {DEFAULT_MODEL})"
    )
    parser.add_argument("--batch", action="store_true", help="Batch mode: JSONL stdin → JSONL stdout")
    parser.add_argument(
        "--similarity", nargs=2, metavar=("TEXT_A", "TEXT_B"),
        help="Compute cosine similarity between two texts",
    )
    parser.add_argument("--dim", action="store_true", help="Print model embedding dimension and exit")
    args = parser.parse_args()

    tokenizer, model, device = _load_model(args.model)

    if args.dim:
        dim = model.config.hidden_size
        print(json.dumps({"model": args.model, "dimension": dim, "device": device}))
        return

    if args.similarity:
        vecs = embed_texts(args.similarity, tokenizer, model, device)
        sim = cosine_sim(vecs[0], vecs[1])
        print(json.dumps({
            "text_a": args.similarity[0],
            "text_b": args.similarity[1],
            "similarity": round(sim, 6),
            "model": args.model,
        }))
        return

    if args.batch:
        # JSONL: each line {"id": "...", "text": "..."} → {"id": "...", "vector": [...]}
        lines = []
        for line in sys.stdin:
            line = line.strip()
            if line:
                lines.append(json.loads(line))

        texts = [item.get("text", "") for item in lines]
        if texts:
            vecs = embed_texts(texts, tokenizer, model, device)
            for item, vec in zip(lines, vecs):
                print(json.dumps({
                    "id": item.get("id", ""),
                    "vector": vec,
                }, ensure_ascii=False))
        return

    # Single text from stdin
    text = sys.stdin.read().strip()
    if text:
        vecs = embed_texts([text], tokenizer, model, device)
        print(json.dumps({"text": text, "vector": vecs[0]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
