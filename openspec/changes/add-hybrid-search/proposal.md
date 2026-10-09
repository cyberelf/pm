## Why

The workspace has no way to find content across weekly reports and materials: the CLI explicitly cannot read material bodies, and the server exposes no search endpoint. As report and material history grows, locating a past decision or note requires opening projects one by one.

## What Changes

- Add a `search` capability: hybrid keyword + vector search over each account's weekly reports (`weekly_reports.content_md`) and materials (`materials.extracted_text`), scoped by the existing per-user project isolation.
- Index lazily at query time: texts are chunked (1000 chars, 150 overlap), stored in `search_chunks`, and re-embedded incrementally per request based on a content hash that includes the embedding model; deleted sources leave no orphan chunks.
- Embeddings come from an OpenAI-compatible `{llm_base_url}/embeddings` endpoint using a new admin-only global setting `llm_embedding_model` on top of the shared `llm_base_url`/`llm_api_key`; when unset, or when a call fails, search degrades to keyword-only and reports `embedding_error` instead of failing.
- Fuse keyword and vector rankings with reciprocal rank fusion (RRF); keyword ranking is a LIKE scan with per-term occurrence counts (FTS5 trigram cannot match the two-character terms that dominate Chinese queries).
- Expose `GET /api/search?q=&limit=&type=&project_id=` (limit capped at 50; a foreign project id yields an empty result, not an error).
- Add `zreport search QUERY [-p PROJECT] [-n N] [--type report|material] [--json]` to the CLI (top 10 by default) and document it in the agent skill and README.
- Surface the optional embedding model in 全局设置 → 内部 Agent LLM (autosaved like the other LLM fields).

## Capabilities

### New Capabilities

- `search`: hybrid keyword + vector search across weekly reports and materials with per-account isolation and topN control.

## Impact

- Code: `reports_app/search_index.py` (new), `reports_app/db.py` (`search_chunks` table), `reports_app/server.py` (route + setting plumbing), `reports_app/config.py`, `zreport.py` (`search` command, SKILL_MD, version 1.4.0), `static/index.html`, `static/app.js`.
- No new process or queue: indexing runs in-request with a per-request embed budget (64 chunks, batches of 32); a failed embedding call never fails the search.
- 手填的 `weekly_updates` are intentionally out of scope for now.
