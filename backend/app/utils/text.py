"""Text utilities: token counting, chunk splitting, noise-comment filtering.

Token counting prefers tiktoken when available and falls back to a simple
word-count heuristic (~0.75 words per token, i.e. 1 token ~= 1.33 words is
the usual rule of thumb; we use a conservative words * 1.3 approximation)
so the pipeline works even without tiktoken installed.
"""
from __future__ import annotations

import re
from typing import Iterable

try:
    import tiktoken

    _ENCODING = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - optional dependency
    _ENCODING = None

# Simple deny-list + length heuristic for filtering noise comments out of
# historical-ticket retrieval documents. This is a data-cleaning rule, not
# an AI classifier (explicitly allowed per DESIGN.md 6.1).
_NOISE_PHRASES = {
    "thanks",
    "thank you",
    "ok",
    "okay",
    "done",
    "resolved",
    "closing",
    "closed",
    "got it",
    "ack",
    "acknowledged",
    "noted",
    "cool",
    "great",
    "perfect",
    "sounds good",
    "will do",
    "no problem",
    "np",
    "yep",
    "yes",
    "no",
    "+1",
}
_NOISE_MIN_LENGTH = 12


def count_tokens(text: str) -> int:
    if not text:
        return 0
    if _ENCODING is not None:
        return len(_ENCODING.encode(text))
    words = len(text.split())
    return int(words * 1.3)


def is_noise_comment(text: str) -> bool:
    if not text:
        return True
    stripped = text.strip().lower().strip(".! ")
    if len(stripped) < _NOISE_MIN_LENGTH and stripped in _NOISE_PHRASES:
        return True
    if len(stripped) < _NOISE_MIN_LENGTH:
        # very short comments with no real content
        return True
    return False


def filter_noise_comments(comments: Iterable[str]) -> list[str]:
    return [c for c in comments if c and not is_noise_comment(c)]


def split_into_sentences(text: str) -> list[str]:
    if not text:
        return []
    # Basic sentence splitter, sufficient for chunking purposes.
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def chunk_text_by_tokens(
    text: str,
    *,
    target_tokens: int = 400,
    overlap_tokens: int = 60,
    min_tokens: int = 50,
) -> list[str]:
    """Splits text on sentence boundaries into ~target_tokens chunks with
    overlap. Never splits mid-sentence when possible."""
    sentences = split_into_sentences(text)
    if not sentences:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)
        if current and current_tokens + sentence_tokens > target_tokens:
            chunks.append(" ".join(current))
            # build overlap from the tail of the current chunk
            overlap: list[str] = []
            overlap_count = 0
            for s in reversed(current):
                t = count_tokens(s)
                if overlap_count + t > overlap_tokens:
                    break
                overlap.insert(0, s)
                overlap_count += t
            current = overlap
            current_tokens = overlap_count
        current.append(sentence)
        current_tokens += sentence_tokens

    if current:
        chunk_text = " ".join(current)
        if chunks and count_tokens(chunk_text) < min_tokens:
            chunks[-1] = chunks[-1] + " " + chunk_text
        else:
            chunks.append(chunk_text)

    return chunks


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def lexical_overlap_score(a: str, b: str) -> float:
    """Simple Jaccard-style overlap between two texts' lowercase token sets.
    Used only for deterministic rerank scoring — never for classification.
    """
    if not a or not b:
        return 0.0
    set_a = set(re.findall(r"[a-z0-9]+", a.lower()))
    set_b = set(re.findall(r"[a-z0-9]+", b.lower()))
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0
