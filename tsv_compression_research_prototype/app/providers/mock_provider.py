from __future__ import annotations

import re
from textwrap import shorten

from .base import BaseLLMProvider


SPAN_RE = re.compile(r"^\[(m\d+\.s\d+)\|([^\]]+)\]\s+(.*)$", re.MULTILINE)


class MockLLMProvider(BaseLLMProvider):
    """Deterministic provider for architecture testing."""

    def complete(self, *, system_prompt: str, user_prompt: str, model_name: str) -> str:
        spans = SPAN_RE.findall(user_prompt)
        if not spans:
            body = shorten(user_prompt.replace("\n", " "), width=480, placeholder=" ...")
            return f"[{model_name}] No exact spans found. Prompt body: {body}"

        bullets: list[str] = []
        for span_id, role, text in spans[:4]:
            bullets.append(f"- {span_id} ({role}): {text[:140]}")

        return (
            f"[{model_name}] Compression-first answer based on verbatim packed spans.\n"
            f"Used exact spans:\n" + "\n".join(bullets) +
            "\n\nInterpretation: respond from these spans first; request more spans if needed."
        )
