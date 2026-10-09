"""Hybrid keyword + vector search over weekly reports and materials.

Search scope follows the account model: chunks are keyed by project and every
query is limited to `project_id IN (SELECT id FROM projects WHERE user_id=?)`,
the same isolation pattern as the rest of the app.

Indexing is lazy and incremental: each search request first re-chunks the
sources in scope (weekly_reports.content_md, materials.extracted_text), drops
chunks whose hash no longer matches, and embeds at most MAX_EMBED_PER_REQUEST
new or changed chunks synchronously before ranking. A failed embedding call
never fails the search — the request degrades to keyword-only results and
reports the error in `index.embedding_error`.

Vectors come from an OpenAI-compatible /embeddings endpoint (llm_embedding_model
setting on top of the shared llm_base_url/llm_api_key); without the setting the
search stays keyword-only. Keyword ranking is a LIKE scan with per-term
occurrence counts — the corpus is a single account's weekly reports and
materials, and FTS5's trigram tokenizer cannot match the two-character terms
that dominate Chinese queries. The two rankings are fused with reciprocal rank
fusion (RRF). 手填的 weekly_updates 暂不纳入索引。
"""

import hashlib
import json
import math
import os
import re
import struct
import threading
import urllib.error
import urllib.request

from .config import LLM_EMBEDDING_BASE_URL_SETTING, LLM_EMBEDDING_MODEL_SETTING
from .db import get_setting
from .internal_agent import resolve_llm_settings
from .timeutil import iso_now

EMBED_BATCH_SIZE = 32
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
RRF_K = 60
MAX_EMBED_PER_REQUEST = 64
EMBED_HTTP_TIMEOUT = 20
FAKE_EMBED_DIM = 32
RANKING_POOL = 50
SNIPPET_WIDTH = 160

# One process, one ThreadingHTTPServer: two concurrent searches must not
# interleave the index writes.
_index_lock = threading.Lock()


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks on paragraph boundaries.

    Long paragraphs are cut into windows of `size` with `overlap` carry;
    short paragraphs are packed up to `size` characters per chunk.
    """
    text = (text or "").strip()
    if not text:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(para) > size:
            if current:
                chunks.append(current)
                current = ""
            step = max(1, size - overlap)
            pos = 0
            while pos < len(para):
                chunks.append(para[pos:pos + size])
                if pos + size >= len(para):
                    break
                pos += step
            continue
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) > size and current:
            chunks.append(current)
            current = para
        else:
            current = candidate
    if current.strip():
        chunks.append(current)
    return [chunk for chunk in chunks if chunk.strip()]


def resolve_embedding_settings(conn):
    """Embedding endpoint settings, or None when the vector half is disabled.

    Reuses the internal agent's LLM credentials; the endpoint address defaults
    to llm_base_url and can be overridden with llm_embedding_base_url (e.g. a
    local LM Studio while chat goes through a remote gateway). The endpoint is
    called OpenAI-style regardless of llm_provider — Anthropic's own API has no
    embeddings, so an Anthropic-shaped base URL fails at call time and search
    stays keyword-only.
    """
    model = (get_setting(conn, LLM_EMBEDDING_MODEL_SETTING, "") or "").strip()
    if not model:
        return None
    settings = resolve_llm_settings(conn)
    base_url = (get_setting(conn, LLM_EMBEDDING_BASE_URL_SETTING, "") or "").strip()
    settings["embedding_model"] = model
    settings["embedding_base_url"] = base_url or settings["base_url"]
    return settings


def chunk_hash(embedding_model, text):
    """Content hash including the model name, so switching models invalidates
    every chunk and the next search re-embeds them lazily."""
    return hashlib.sha256(f"{embedding_model}\0{text}".encode("utf-8")).hexdigest()


def embed_texts(texts, settings, timeout=EMBED_HTTP_TIMEOUT):
    """Batch-embed texts against the OpenAI-compatible /embeddings endpoint.

    Returns little-endian float32 blobs, one per input, in input order.
    """
    url = (settings.get("embedding_base_url") or settings["base_url"]).rstrip("/") + "/embeddings"
    vectors = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[start:start + EMBED_BATCH_SIZE]
        payload = json.dumps({"model": settings["embedding_model"], "input": batch}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings['api_key']}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", "replace")[:200]
            except Exception:
                detail = ""
            raise RuntimeError(f"embedding request failed with HTTP {exc.code}: {detail or exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"embedding request failed: {exc}") from exc
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list) or len(data) != len(batch):
            raise RuntimeError("embedding response is missing data entries")
        for item in sorted(data, key=lambda entry: entry.get("index", 0)):
            vector = item.get("embedding")
            if not isinstance(vector, list) or not vector:
                raise RuntimeError("embedding response contains an empty vector")
            vectors.append(struct.pack(f"<{len(vector)}f", *vector))
    return vectors


def fake_embed_texts(texts):
    """Deterministic vectors from the text digest, used when
    REPORTS_FAKE_EMBEDDINGS=1 (tests) so the vector path runs with no network."""
    vectors = []
    for text in texts:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vectors.append(struct.pack(f"<{FAKE_EMBED_DIM}f", *(byte / 255.0 - 0.5 for byte in digest[:FAKE_EMBED_DIM])))
    return vectors


def _embed(texts, settings):
    if os.environ.get("REPORTS_FAKE_EMBEDDINGS") == "1":
        return fake_embed_texts(texts)
    return embed_texts(texts, settings)


def _scope_clause(user_id, project_id):
    clause = "project_id IN (SELECT id FROM projects WHERE user_id = ?)"
    params = [user_id]
    if project_id is not None:
        clause += " AND project_id = ?"
        params.append(project_id)
    return clause, params


def _source_rows(conn, user_id, source_type, project_id):
    """Source rows in scope as (source_id, project_id, title, week_key, text, updated_at, project_name)."""
    if source_type == "report":
        where = "p.user_id = ?"
        params = [user_id]
        if project_id is not None:
            where += " AND wr.project_id = ?"
            params.append(project_id)
        rows = conn.execute(
            f"""
            SELECT wr.id, wr.project_id, wr.week_key, wr.content_md AS text, wr.updated_at, p.name AS project_name
            FROM weekly_reports wr JOIN projects p ON p.id = wr.project_id
            WHERE {where}
            """,
            params,
        ).fetchall()
        return [
            (row["id"], row["project_id"], f"周报 {row['project_name']} {row['week_key']}", row["week_key"] or "", row["text"] or "", row["updated_at"], row["project_name"])
            for row in rows
        ]
    where = "p.user_id = ? AND m.extracted_text != ''"
    params = [user_id]
    if project_id is not None:
        where += " AND m.project_id = ?"
        params.append(project_id)
    rows = conn.execute(
        f"""
        SELECT m.id, m.project_id, m.filename, m.extracted_text AS text, m.updated_at, p.name AS project_name
        FROM materials m JOIN projects p ON p.id = m.project_id
        WHERE {where}
        """,
        params,
    ).fetchall()
    return [
        (row["id"], row["project_id"], row["filename"] or "未命名资料", "", row["text"] or "", row["updated_at"], row["project_name"])
        for row in rows
    ]


def sync_index(conn, user_id, project_id=None, source_type=None, settings=None, budget=MAX_EMBED_PER_REQUEST):
    """Bring search_chunks in scope in line with the sources; embed pending
    chunks (budget-capped). Returns {"indexed_chunks", "embedded_chunks",
    "embedding_error"} for the API response."""
    meta = {"indexed_chunks": 0, "embedded_chunks": 0, "embedding_error": ""}
    model = settings["embedding_model"] if settings else ""
    wanted_types = ("report", "material") if source_type is None else (source_type,)
    for kind in wanted_types:
        for source_id, proj_id, title, week_key, text, updated_at, _name in _source_rows(conn, user_id, kind, project_id):
            chunks = chunk_text(text)
            desired = {index: chunk_hash(model, chunk) for index, chunk in enumerate(chunks)}
            existing = {
                row["chunk_index"]: (row["id"], row["chunk_hash"])
                for row in conn.execute(
                    "SELECT id, chunk_index, chunk_hash FROM search_chunks WHERE source_type = ? AND source_id = ?",
                    (kind, source_id),
                ).fetchall()
            }
            now = iso_now()
            for index, (row_id, stored_hash) in existing.items():
                if desired.get(index) != stored_hash:
                    conn.execute("DELETE FROM search_chunks WHERE id = ?", (row_id,))
            for index, chunk in enumerate(chunks):
                if desired[index] == existing.get(index, (None, None))[1]:
                    continue
                conn.execute(
                    """
                    INSERT INTO search_chunks
                        (project_id, source_type, source_id, chunk_index, chunk_hash, title, week_key, content,
                         embedding, embedding_model, embedding_dim, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, '', 0, ?, ?)
                    """,
                    (proj_id, kind, source_id, index, desired[index], title, week_key, chunk, now, now),
                )
                meta["indexed_chunks"] += 1
    # orphaned chunks whose source row was deleted (materials/reports have no
    # ON DELETE hook into search_chunks)
    scope, scope_params = _scope_clause(user_id, None)
    conn.execute(
        f"""
        DELETE FROM search_chunks
        WHERE source_type = 'report' AND {scope}
          AND source_id NOT IN (SELECT id FROM weekly_reports)
        """,
        scope_params,
    )
    conn.execute(
        f"""
        DELETE FROM search_chunks
        WHERE source_type = 'material' AND {scope}
          AND source_id NOT IN (SELECT id FROM materials)
        """,
        scope_params,
    )
    if not settings:
        return meta
    # embed pending chunks, newest first, within this request's budget
    pending = conn.execute(
        f"""
        SELECT id, content FROM search_chunks
        WHERE (embedding IS NULL OR embedding_model != ?) AND {scope}
        ORDER BY updated_at DESC, id DESC LIMIT ?
        """,
        [model, *scope_params, budget],
    ).fetchall()
    if not pending:
        return meta
    try:
        vectors = _embed([row["content"] for row in pending], settings)
    except RuntimeError as exc:
        meta["embedding_error"] = str(exc)
        return meta
    dim = len(vectors[0]) // 4
    for row, vector in zip(pending, vectors):
        conn.execute(
            "UPDATE search_chunks SET embedding = ?, embedding_model = ?, embedding_dim = ?, updated_at = ? WHERE id = ?",
            (vector, model, dim, iso_now(), row["id"]),
        )
    meta["embedded_chunks"] = len(pending)
    return meta


def _keyword_hits(conn, user_id, query, source_type, project_id, limit=RANKING_POOL):
    """LIKE scan over the user's chunks, ranked by summed per-term occurrence
    counts. Two-character Chinese terms (部署, 联调) are the common case, so
    this deliberately avoids FTS5's three-character trigram floor."""
    terms = [term for term in re.split(r"\s+", query.strip()) if term]
    if not terms:
        return []
    scope, scope_params = _scope_clause(user_id, project_id)
    type_clause = ""
    if source_type:
        type_clause = " AND sc.source_type = ?"
        scope_params = [*scope_params, source_type]
    rows = conn.execute(
        f"""
        SELECT sc.id, sc.project_id, sc.source_type, sc.source_id, sc.chunk_index, sc.title, sc.week_key,
               sc.content, sc.updated_at, p.name AS project_name
        FROM search_chunks sc JOIN projects p ON p.id = sc.project_id
        WHERE {scope}{type_clause}
        """,
        scope_params,
    ).fetchall()
    upper_terms = [term.upper() for term in terms]
    hits = []
    for row in rows:
        content_upper = (row["content"] or "").upper()
        title_upper = (row["title"] or "").upper()
        score = 0
        for term in upper_terms:
            score += content_upper.count(term) * 2 + title_upper.count(term) * 4
        if not score:
            continue
        hits.append(
            {
                "type": row["source_type"],
                "source_id": row["source_id"],
                "chunk_index": row["chunk_index"],
                "project_id": row["project_id"],
                "project_name": row["project_name"],
                "title": row["title"],
                "week_key": row["week_key"],
                "snippet": _snippet(row["content"] or "", terms),
                "updated_at": row["updated_at"],
                "score": score,
            }
        )
    hits.sort(key=lambda hit: (-hit["score"], hit["updated_at"] or "", hit["source_id"], hit["chunk_index"]))
    return hits[:limit]


def _snippet(content, terms, width=SNIPPET_WIDTH):
    """One-line window around the earliest match, in plain text."""
    flat = re.sub(r"\s+", " ", content).strip()
    lowered = flat.lower()
    first = len(flat)
    for term in terms:
        pos = lowered.find(term.lower())
        if pos != -1:
            first = min(first, pos)
    if first == len(flat):
        return flat[:width]
    start = max(0, first - width // 3)
    end = min(len(flat), start + width)
    prefix = "…" if start else ""
    suffix = "…" if end < len(flat) else ""
    return f"{prefix}{flat[start:end]}{suffix}"


def _cosine(blob_a, blob_b):
    count = len(blob_a) // 4
    a = struct.unpack(f"<{count}f", blob_a)
    b = struct.unpack(f"<{len(blob_b) // 4}f", blob_b)
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def _vector_hits(conn, user_id, query, settings, source_type, project_id, limit=RANKING_POOL):
    """Embed the query and rank embedded chunks in scope by cosine similarity."""
    query_vector = _embed([query], settings)[0]
    scope, scope_params = _scope_clause(user_id, project_id)
    type_clause = ""
    if source_type:
        type_clause = " AND sc.source_type = ?"
        scope_params = [*scope_params, source_type]
    rows = conn.execute(
        f"""
        SELECT sc.source_type, sc.source_id, sc.chunk_index, sc.title, sc.week_key, sc.embedding,
               sc.updated_at, sc.project_id, p.name AS project_name
        FROM search_chunks sc JOIN projects p ON p.id = sc.project_id
        WHERE sc.embedding IS NOT NULL AND {scope}{type_clause}
        """,
        scope_params,
    ).fetchall()
    hits = []
    for row in rows:
        similarity = _cosine(query_vector, row["embedding"])
        hits.append(
            {
                "type": row["source_type"],
                "source_id": row["source_id"],
                "chunk_index": row["chunk_index"],
                "project_id": row["project_id"],
                "project_name": row["project_name"],
                "title": row["title"],
                "week_key": row["week_key"],
                "updated_at": row["updated_at"],
                "score": similarity,
            }
        )
    hits.sort(key=lambda hit: -hit["score"])
    return hits[:limit]


def _rrf_fuse(hit_lists, limit):
    """Reciprocal rank fusion: score = Σ 1/(RRF_K + rank) over every list the
    chunk appears in; keyword-only searches fuse a single list, which simply
    keeps the keyword order."""
    fused = {}
    for hits in hit_lists:
        for rank, hit in enumerate(hits, start=1):
            key = (hit["type"], hit["source_id"], hit["chunk_index"])
            entry = fused.setdefault(key, {**hit, "score": 0.0})
            entry["score"] += 1.0 / (RRF_K + rank)
    ranked = sorted(fused.values(), key=lambda hit: -hit["score"])
    return ranked[:limit]


def search(conn, user_id, query, limit=10, source_type=None, project_id=None):
    """Hybrid search entry point: lazy incremental index, then keyword and
    (when configured) vector rankings fused with RRF."""
    with _index_lock:
        settings = resolve_embedding_settings(conn)
        meta = sync_index(conn, user_id, project_id=project_id, source_type=source_type, settings=settings)
    keyword_hits = _keyword_hits(conn, user_id, query, source_type, project_id)
    vector_hits = []
    if settings and not meta["embedding_error"]:
        try:
            vector_hits = _vector_hits(conn, user_id, query, settings, source_type, project_id)
        except RuntimeError as exc:
            meta["embedding_error"] = str(exc)
    hits = _rrf_fuse([keyword_hits, vector_hits], limit)
    for hit in hits:
        hit.pop("updated_at", None)
        hit.pop("chunk_index", None)
    return {
        "mode": "hybrid" if vector_hits else "keyword",
        "embedding_configured": bool(settings),
        "index": meta,
        "hits": hits,
    }
