# Qwen LLM Integration (Advisory Synthesis Only)

## Architecture
```text
DB + Analytics + RAG -> AnalyticalContext -> AdvisoryService -> QwenClient -> Final advisory text
```

Qwen is used only to synthesize natural-language output from `AnalyticalContext`.

## Environment Variables
- `QWEN_API_KEY`
- `QWEN_BASE_URL` (default `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`)
- `QWEN_MODEL` (default `qwen-plus`)

Fallback base URL when needed:
- `https://dashscope.aliyuncs.com/compatible-mode/v1`

## Why Qwen Only Synthesizes
- Prevents model-side data fetching and hidden source drift.
- Keeps indicators deterministic in Python analytics.
- Preserves evidence provenance from DB/RAG pipelines.
- Guardrails remain authoritative.

## Sample Prompt
System rules include:
- only synthesize from provided AnalyticalContext
- do not invent values/sources
- do not calculate indicators
- include risk and confidence
- no personalized advice
- include disclaimer

User prompt contains only serialized context snapshots and evidence summaries (`source`, `date`, `content` with fetched timestamps when available).

## Fallback Behavior
- If `QWEN_API_KEY` is missing, or provider call fails, `QwenClient` returns a safe mock synthesizer response.
- Runtime still uses existing guardrails and disclaimer flow.
