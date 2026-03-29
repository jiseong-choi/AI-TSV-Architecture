from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any


@dataclass
class Message:
    role: str
    content: str
    created_at: str


@dataclass
class ExactSpan:
    span_id: str
    role: str
    message_index: int
    span_index: int
    text: str
    token_estimate: int
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PackedContext:
    query: str
    packed_text: str
    selected_span_ids: list[str] = field(default_factory=list)
    selected_spans: list[ExactSpan] = field(default_factory=list)
    raw_history_tokens: int = 0
    packed_tokens: int = 0
    exact_span_count: int = 0
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "packed_text": self.packed_text,
            "selected_span_ids": self.selected_span_ids,
            "selected_spans": [s.to_dict() for s in self.selected_spans],
            "raw_history_tokens": self.raw_history_tokens,
            "packed_tokens": self.packed_tokens,
            "exact_span_count": self.exact_span_count,
            "truncated": self.truncated,
        }


@dataclass
class ArchiveMetrics:
    raw_bytes: int
    compressed_bytes: int
    compression_ratio: float
    roundtrip_verified: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QueryMetrics:
    estimated_input_tokens: int
    estimated_output_tokens: int
    exact_span_count: int
    cache_hit: bool
    route: str
    latency_ms: float
    raw_history_tokens: int
    packed_context_tokens: int
    storage_compression_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QueryResponse:
    answer: str
    route: str
    cache_hit: bool
    packed_context: PackedContext
    archive_metrics: ArchiveMetrics
    metrics: QueryMetrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "route": self.route,
            "cache_hit": self.cache_hit,
            "packed_context": self.packed_context.to_dict(),
            "archive_metrics": self.archive_metrics.to_dict(),
            "metrics": self.metrics.to_dict(),
        }
