from __future__ import annotations

import time

from .compressor import compress_messages_lossless, pack_exact_context
from .config import SETTINGS
from .embeddings import cosine_similarity, estimate_tokens, hashed_embedding
from .memory import SQLiteMemoryStore
from .models import QueryMetrics, QueryResponse
from .providers.mock_provider import MockLLMProvider
from .reasoner import answer_with_direct_mode, answer_with_reasoner
from .router import route_query


class TSVCompressionEngine:
    def __init__(self, db_path: str | None = None) -> None:
        self.settings = SETTINGS
        self.store = SQLiteMemoryStore(db_path or self.settings.db_path)
        self.provider = MockLLMProvider()

    def _lookup_cache(self, session_id: str, query: str) -> tuple[str, str] | None:
        query_vec = hashed_embedding(query, dim=self.settings.embedding_dim)
        best: tuple[float, dict] | None = None
        for row in self.store.list_cache_entries(session_id):
            sim = cosine_similarity(query_vec, row["embedding"])
            if best is None or sim > best[0]:
                best = (sim, row)
        if best and best[0] >= self.settings.semantic_cache_threshold:
            return best[1]["answer"], best[1]["route"]
        return None

    def inspect_pack(self, session_id: str, query: str) -> dict:
        messages = self.store.get_messages(session_id)
        _, archive_metrics = compress_messages_lossless(messages)
        packed = pack_exact_context(
            messages,
            query,
            max_spans=self.settings.max_exact_spans,
            max_tokens=self.settings.max_packed_tokens,
            include_recent_messages=self.settings.include_recent_messages,
        )
        return {
            "packed_context": packed.to_dict(),
            "archive_metrics": archive_metrics.to_dict(),
        }

    def process_query(self, session_id: str, query: str) -> QueryResponse:
        start = time.perf_counter()
        self.store.add_message(session_id, "user", query)
        cache_hit = False

        cached = self._lookup_cache(session_id, query)
        messages = self.store.get_messages(session_id)
        _, archive_metrics = compress_messages_lossless(messages)
        packed = pack_exact_context(
            messages,
            query,
            max_spans=self.settings.max_exact_spans,
            max_tokens=self.settings.max_packed_tokens,
            include_recent_messages=self.settings.include_recent_messages,
        )

        if cached is not None:
            answer, route = cached
            cache_hit = True
        else:
            route = route_query(query)
            if route == "reasoner":
                answer = answer_with_reasoner(
                    provider=self.provider,
                    model_name=self.settings.reasoner_model_name,
                    query=query,
                    packed=packed,
                )
            else:
                answer = answer_with_direct_mode(query, packed)

            query_vec = hashed_embedding(query, dim=self.settings.embedding_dim)
            self.store.add_cache_entry(
                session_id=session_id,
                query_text=query,
                embedding=query_vec,
                answer=answer,
                route=route,
            )

        self.store.add_message(session_id, "assistant", answer)

        latency_ms = (time.perf_counter() - start) * 1000.0
        metrics = QueryMetrics(
            estimated_input_tokens=packed.packed_tokens + estimate_tokens(query),
            estimated_output_tokens=estimate_tokens(answer),
            exact_span_count=packed.exact_span_count,
            cache_hit=cache_hit,
            route=route,
            latency_ms=round(latency_ms, 2),
            raw_history_tokens=packed.raw_history_tokens,
            packed_context_tokens=packed.packed_tokens,
            storage_compression_ratio=archive_metrics.compression_ratio,
        )
        return QueryResponse(
            answer=answer,
            route=route,
            cache_hit=cache_hit,
            packed_context=packed,
            archive_metrics=archive_metrics,
            metrics=metrics,
        )

    def get_history(self, session_id: str) -> list[dict]:
        return [m.__dict__ for m in self.store.get_messages(session_id)]

    def get_archive(self, session_id: str) -> dict:
        messages = self.store.get_messages(session_id)
        archive_b64, metrics = compress_messages_lossless(messages)
        return {
            "archive_base64_preview": archive_b64[:120] + ("..." if len(archive_b64) > 120 else ""),
            "archive_metrics": metrics.to_dict(),
        }
