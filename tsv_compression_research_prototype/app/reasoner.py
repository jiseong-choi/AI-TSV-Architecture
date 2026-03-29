from __future__ import annotations

from textwrap import dedent

from .models import PackedContext
from .providers.base import BaseLLMProvider


def answer_with_reasoner(
    *,
    provider: BaseLLMProvider,
    model_name: str,
    query: str,
    packed: PackedContext,
) -> str:
    system_prompt = dedent(
        """
        You are the Strategic Reasoner in a compression-first TSV experiment.
        The packed context contains exact source spans only.
        Do not rely on hidden summaries. If evidence is insufficient, say so.
        Prefer concise technical answers with explicit assumptions.
        """
    ).strip()

    user_prompt = dedent(
        f"""
        Query:
        {query}

        Packed context:
        {packed.packed_text}
        """
    ).strip()

    return provider.complete(system_prompt=system_prompt, user_prompt=user_prompt, model_name=model_name)


def answer_with_direct_mode(query: str, packed: PackedContext) -> str:
    head = packed.selected_spans[:3]
    lines = ["[direct] Exact-span answer scaffold"]
    lines.append(f"Query: {query}")
    if head:
        lines.append("Relevant verbatim spans:")
        for span in head:
            lines.append(f"- [{span.span_id}] {span.text}")
    else:
        lines.append("No exact spans matched the query.")
    return "\n".join(lines)
