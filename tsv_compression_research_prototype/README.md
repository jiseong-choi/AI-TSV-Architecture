# TSV Compression Research Prototype

This prototype rewrites the earlier TSV research code around a stricter distinction:

- **Summary** = rewrites or paraphrases history. It is **lossy**.
- **Compression** = preserves original bytes or exact source spans. It should be treated separately.

## What this prototype does

It implements two different mechanisms on purpose:

1. **True lossless archive compression**
   - Entire session history is serialized and compressed with `zlib`.
   - The archive is verified by round-trip decompression.
   - This reduces storage size, not LLM input tokens directly.

2. **Extractive exact-span packing for reasoning**
   - The system does **not** summarize or paraphrase history.
   - It selects **verbatim spans** from the original messages and packs those into the prompt.
   - This reduces prompt size, but it is only lossless for the **selected spans**, not for the entire history.

This is the honest trade-off in black-box API systems:

- storage compression can be truly lossless,
- prompt reduction usually requires either lossy summarization or exact-span selection.

## Run

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.api
```

Docs:

```text
http://127.0.0.1:8000/docs
```

CLI:

```bash
python -m app.cli --session demo
```

Evaluation:

```bash
python scripts/evaluate.py --dataset data/sample_eval.yaml
```

## Endpoints

- `POST /sessions/{session_id}/query`
- `POST /sessions/{session_id}/pack`
- `GET /sessions/{session_id}/history`
- `GET /sessions/{session_id}/archive`

## Suggested experiment

1. Feed long repeated project context across many turns.
2. Compare full-history replay vs lossy summary vs extractive exact-pack.
3. Inspect `/archive` to verify round-trip lossless compression.
4. Inspect `/pack` to confirm the prompt contains original spans instead of paraphrased summaries.

## Replace the mock provider

Swap `app/providers/mock_provider.py` with a real provider adapter. The rest of the prototype is intentionally provider-agnostic.
