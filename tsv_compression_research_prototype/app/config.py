from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("TSV_DB_PATH", "./tsv_compression.db")
    embedding_dim: int = int(os.getenv("TSV_EMBEDDING_DIM", "128"))
    semantic_cache_threshold: float = float(os.getenv("TSV_SEMANTIC_CACHE_THRESHOLD", "0.94"))
    max_exact_spans: int = int(os.getenv("TSV_MAX_EXACT_SPANS", "4"))
    max_packed_tokens: int = int(os.getenv("TSV_MAX_PACKED_TOKENS", "180"))
    include_recent_messages: int = int(os.getenv("TSV_INCLUDE_RECENT_MESSAGES", "2"))
    default_host: str = os.getenv("TSV_HOST", "127.0.0.1")
    default_port: int = int(os.getenv("TSV_PORT", "8000"))
    reasoner_model_name: str = os.getenv("TSV_REASONER_MODEL", "mock-pro")


SETTINGS = Settings()
