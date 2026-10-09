## 1. Index and retrieval core

- [x] 1.1 Add `search_chunks` table (chunk hash incl. embedding model, title, week_key, embedding BLOB) to `reports_app/db.py`
- [x] 1.2 Create `reports_app/search_index.py`: `chunk_text`, `resolve_embedding_settings`, `embed_texts` (OpenAI-compatible `/embeddings`, batch 32), `sync_index` (lazy incremental, orphan prune, 64-chunk embed budget), `search` (keyword + cosine + RRF fusion)
- [x] 1.3 Keyword ranking via LIKE occurrence counts with plain-text snippets; degradation to keyword-only on missing/failing embeddings

## 2. Server API and settings

- [x] 2.1 Add `GET /api/search` route with `q`/`limit`/`type`/`project_id` validation and per-user project scoping
- [x] 2.2 Add admin-only `llm_embedding_model` setting (config key, ADMIN_ONLY_SETTING_KEYS, llm_state, PUT /api/settings)
- [x] 2.3 Surface the embedding model input in 全局设置 → 内部 Agent LLM (index.html + app.js autosave) and bump the static asset cache version

## 3. CLI

- [x] 3.1 Add `zreport search QUERY [-p] [-n] [--type] [--json]` with 120s timeout and table/JSON output
- [x] 3.2 Update SKILL.md (repo copy + embedded SKILL_MD), README-cli.md commands, bump `__version__` to 1.4.0

## 4. Tests and verification

- [x] 4.1 Unit tests: chunk boundaries, index invalidation, orphan cleanup, per-user isolation, embeddings HTTP call against a mock endpoint, embed-failure degradation, settings admin gate, /api/search endpoint behaviors
- [x] 4.2 CLI end-to-end test in tests/test_cli.py (table, --json, --type, unknown project, keyword-only note)
- [x] 4.3 `python3 -m unittest` green; verify /api/search against the running service with curl
