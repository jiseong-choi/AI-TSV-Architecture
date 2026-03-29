from __future__ import annotations

import re


COMPLEXITY_MARKERS = [
    "why",
    "how",
    "design",
    "architecture",
    "tradeoff",
    "implement",
    "code",
    "benchmark",
    "evaluate",
    "experiment",
    "compare",
    "failure",
    "root cause",
    "refactor",
    "optimize",
]


def route_query(query: str) -> str:
    q = query.lower()
    score = 0

    if len(q.split()) > 25:
        score += 1
    if "?" in q:
        score += 1
    if any(marker in q for marker in COMPLEXITY_MARKERS):
        score += 2
    if re.search(r"(step by step|plan|strategy|system)", q):
        score += 1

    return "reasoner" if score >= 3 else "direct"
