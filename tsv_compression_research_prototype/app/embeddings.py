from __future__ import annotations

import hashlib
import math
import re
from collections import Counter


TOKEN_RE = re.compile(r"[A-Za-z0-9_가-힣]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def hashed_embedding(text: str, dim: int = 128) -> list[float]:
    counts = Counter(tokenize(text))
    vec = [0.0] * dim
    for token, weight in counts.items():
        digest = hashlib.md5(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign * float(weight)

    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vector dimension mismatch")
    return sum(x * y for x, y in zip(a, b))
