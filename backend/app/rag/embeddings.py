from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

_TOKEN = re.compile(r"[a-z0-9]+")


def _stable_bucket(value: str, modulus: int) -> int:
    digest = hashlib.md5(value.encode("utf-8"), usedforsecurity=False).digest()
    return int.from_bytes(digest[:4], "big") % modulus


class EmbeddingProvider(ABC):
    name: str
    version: str
    dimensions: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class LocalHashingEmbeddingProvider(EmbeddingProvider):
    """Deterministic hashed n-gram embeddings. No API key required.

    Similar passages produce similar vectors; this is cosine similarity, not keyword lookup.
    """

    name = "local-hashing"
    version = "1.0"
    dimensions = 256

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        values = [0.0] * self.dimensions
        tokens = _TOKEN.findall(text.lower())
        grams = tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:], strict=False)]
        if not grams:
            values[0] = 1.0
            return values
        for gram in grams:
            index = _stable_bucket(gram, self.dimensions)
            sign = -1.0 if _stable_bucket(f"s:{gram}", 2) else 1.0
            values[index] += sign
        norm = math.sqrt(sum(item * item for item in values)) or 1.0
        return [item / norm for item in values]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return float(sum(a * b for a, b in zip(left, right, strict=True)))


def get_embedding_provider() -> EmbeddingProvider:
    return LocalHashingEmbeddingProvider()
