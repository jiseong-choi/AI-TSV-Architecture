from __future__ import annotations

from typing import Protocol


class BaseLLMProvider(Protocol):
    def complete(self, *, system_prompt: str, user_prompt: str, model_name: str) -> str:
        ...
