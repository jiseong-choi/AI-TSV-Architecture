from __future__ import annotations

import base64
import json
import re
import zlib
from collections import OrderedDict

from .embeddings import estimate_tokens
from .models import ArchiveMetrics, ExactSpan, Message, PackedContext


SENTENCE_PATTERN = re.compile(r"[^.!?\n]+[.!?]?", re.UNICODE)
WORD_RE = re.compile(r"[A-Za-z0-9_가-힣]+")


def _query_terms(query: str) -> set[str]:
    return {x.lower() for x in WORD_RE.findall(query)}


def build_exact_spans(messages: list[Message]) -> list[ExactSpan]:
    spans: list[ExactSpan] = []
    for midx, message in enumerate(messages):
        parts = [m.group(0) for m in SENTENCE_PATTERN.finditer(message.content)]
        if not parts:
            parts = [message.content]
        span_idx = 0
        for raw in parts:
            if not raw.strip():
                continue
            text = raw.rstrip("\n")
            spans.append(
                ExactSpan(
                    span_id=f"m{midx}.s{span_idx}",
                    role=message.role,
                    message_index=midx,
                    span_index=span_idx,
                    text=text,
                    token_estimate=estimate_tokens(text),
                )
            )
            span_idx += 1
    return spans


def compress_messages_lossless(messages: list[Message]) -> tuple[str, ArchiveMetrics]:
    payload = json.dumps(
        [message.__dict__ for message in messages],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    compressed = zlib.compress(payload, level=9)
    restored_bytes = zlib.decompress(compressed)
    restored = json.loads(restored_bytes.decode("utf-8"))
    archive_b64 = base64.b64encode(compressed).decode("ascii")
    ratio = round((len(compressed) / max(1, len(payload))), 4)
    metrics = ArchiveMetrics(
        raw_bytes=len(payload),
        compressed_bytes=len(compressed),
        compression_ratio=ratio,
        roundtrip_verified=restored == [message.__dict__ for message in messages],
    )
    return archive_b64, metrics


def pack_exact_context(
    messages: list[Message],
    query: str,
    *,
    max_spans: int,
    max_tokens: int,
    include_recent_messages: int,
) -> PackedContext:
    spans = build_exact_spans(messages)
    raw_history_tokens = sum(estimate_tokens(m.content) for m in messages)
    q_terms = _query_terms(query)
    recent_start = max(0, len(messages) - include_recent_messages)

    candidate_spans = [span for span in spans if span.role == "user"]
    if not candidate_spans:
        candidate_spans = spans

    scored: list[ExactSpan] = []
    for span in candidate_spans:
        terms = {x.lower() for x in WORD_RE.findall(span.text)}
        overlap = len(q_terms & terms)
        recency_bonus = 2.0 if span.message_index >= recent_start else 0.0
        role_bonus = 1.0 if span.role == "user" else 0.0
        numeric_bonus = 0.5 if any(ch.isdigit() for ch in span.text) else 0.0
        exact_phrase_bonus = 1.0 if query.strip() and query.lower() in span.text.lower() else 0.0
        span.score = overlap + recency_bonus + role_bonus + numeric_bonus + exact_phrase_bonus
        if span.score > 0:
            scored.append(span)

    if not scored:
        scored = candidate_spans[-max_spans:]

    scored.sort(key=lambda s: (-s.score, -s.message_index, s.span_index))

    unique: OrderedDict[str, ExactSpan] = OrderedDict()
    for span in scored:
        key = span.text
        if key not in unique:
            unique[key] = span
        if len(unique) >= max_spans * 2:
            break

    selected: list[ExactSpan] = []
    token_total = 0
    for span in unique.values():
        projected = token_total + span.token_estimate
        if selected and projected > max_tokens:
            break
        selected.append(span)
        token_total = projected
        if len(selected) >= max_spans:
            break

    selected.sort(key=lambda s: (s.message_index, s.span_index))
    selected_ids = [span.span_id for span in selected]

    lines = ["CTX_EXACT_SPANS:"]
    for span in selected:
        lines.append(f"[{span.span_id}|{span.role}] {span.text}")

    packed_text = "\n".join(lines)
    packed_tokens = estimate_tokens(packed_text)
    truncated = len(unique) > len(selected)
    return PackedContext(
        query=query,
        packed_text=packed_text,
        selected_span_ids=selected_ids,
        selected_spans=selected,
        raw_history_tokens=raw_history_tokens,
        packed_tokens=packed_tokens,
        exact_span_count=len(selected),
        truncated=truncated,
    )
