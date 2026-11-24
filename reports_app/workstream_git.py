"""PR / issue activity for 工作线.

Each connected repository with its PR or issue switch on contributes the
pull/merge requests and issues updated in the current project week. They are
stored per item and week in `workstream_git_items` and linked to one
workstream: the repository's default workstream first, otherwise the
internal agent's choice from the title; a person's choice is manual and
wins over both from then on, also in later weeks. Linked activity is
evidence for the weekly snapshots and tracking items and counts as activity
for the deterministic staleness rule.

Remote reads happen before any write, so a slow API never holds the SQLite
write lock; the report path reuses the extras its context already fetched.
"""

import json

from .timeutil import current_week_key, iso_now, week_bounds
from .validation import ValidationError

GIT_KINDS = ("pr", "issue")
CLASSIFY_BATCH = 60
PER_WORKSTREAM = 15


def _section(extras, key):
    section = extras.get(key)
    if isinstance(section, dict):
        return section.get(key) or []
    return section if isinstance(section, list) else []


def syncable_repos(conn, project_id):
    return conn.execute(
        """
        SELECT * FROM github_repos WHERE project_id = ? AND enabled = 1 AND status = 'connected'
          AND (fetch_pull_requests = 1 OR fetch_issues = 1) ORDER BY id
        """,
        (project_id,),
    ).fetchall()


def fetch_week_activity(conn, project_id):
    """Remote reads only: this week's PRs/MRs and issues per syncable repo,
    as the extras shape report context uses."""
    from .git_sources import fetch_repo_extras, git_auth_for_user

    project = conn.execute("SELECT user_id, timezone FROM projects WHERE id = ?", (project_id,)).fetchone()
    repos = syncable_repos(conn, project_id)
    if not project or not repos:
        return []
    auth_info = git_auth_for_user(conn, project["user_id"])
    week_start, week_end = week_bounds(project["timezone"])
    result = []
    for repo in repos:
        flags = {"fetch_pull_requests": repo["fetch_pull_requests"], "fetch_issues": repo["fetch_issues"]}
        result.append(fetch_repo_extras(repo["repo"], week_start, week_end, flags, git_mode=repo["git_mode"], auth_info=auth_info))
    return result


def store_week_activity(conn, project_id, week_key, extras_list):
    """Upsert the week's items from extras entries ({repo, git_mode,
    pull_requests, issues}); new rows inherit the item's earlier manual or
    agent link, else the repository default. Returns how many rows exist
    for the week after the sync."""
    repos = {
        (r["repo"].lower(), r["git_mode"]): r
        for r in conn.execute("SELECT * FROM github_repos WHERE project_id = ?", (project_id,))
    }
    now = iso_now()
    for extras in extras_list or []:
        repo = repos.get((str(extras.get("repo") or "").lower(), extras.get("git_mode") or "github"))
        if not repo:
            continue
        for kind, key in (("pr", "pull_requests"), ("issue", "issues")):
            for entry in _section(extras, key):
                number = entry.get("number")
                if not isinstance(number, int):
                    continue
                conn.execute(
                    """
                    INSERT INTO workstream_git_items
                    (project_id, repo_id, kind, number, week_key, title, state, merged, draft, author, url, updated_at, synced_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(repo_id, kind, number, week_key) DO UPDATE SET title = excluded.title, state = excluded.state,
                        merged = excluded.merged, draft = excluded.draft, author = excluded.author, url = excluded.url,
                        updated_at = excluded.updated_at, synced_at = excluded.synced_at
                    """,
                    (
                        project_id, repo["id"], kind, number, week_key, str(entry.get("title") or "")[:300],
                        str(entry.get("state") or ""), int(bool(entry.get("merged"))), int(bool(entry.get("draft"))),
                        str(entry.get("author") or "")[:80], str(entry.get("url") or "")[:500], str(entry.get("updated_at") or ""), now,
                    ),
                )
    _apply_links(conn, project_id, week_key)
    return conn.execute(
        "SELECT COUNT(*) FROM workstream_git_items WHERE project_id = ? AND week_key = ?", (project_id, week_key)
    ).fetchone()[0]


def _apply_links(conn, project_id, week_key):
    for row in conn.execute(
        """
        SELECT g.id, g.repo_id, g.kind, g.number, r.workstream_id AS repo_default
        FROM workstream_git_items g JOIN github_repos r ON r.id = g.repo_id
        WHERE g.project_id = ? AND g.week_key = ? AND g.workstream_id IS NULL
        """,
        (project_id, week_key),
    ).fetchall():
        earlier = conn.execute(
            """
            SELECT workstream_id, link_source FROM workstream_git_items
            WHERE repo_id = ? AND kind = ? AND number = ? AND workstream_id IS NOT NULL AND link_source IN ('manual', 'auto')
            ORDER BY link_source = 'manual' DESC, week_key DESC LIMIT 1
            """,
            (row["repo_id"], row["kind"], row["number"]),
        ).fetchone()
        if earlier:
            link = (earlier["workstream_id"], earlier["link_source"])
        elif row["repo_default"]:
            link = (row["repo_default"], "repo")
        else:
            continue
        conn.execute("UPDATE workstream_git_items SET workstream_id = ?, link_source = ? WHERE id = ?", (*link, row["id"]))


# ---------------------------------------------------------------- classification


def build_git_classify_prompt(workstreams, items):
    return (
        "把每条代码仓库的 PR / Issue 归到最相关的一条工作线。只依据仓库名、标题和仓库说明判断；"
        "带 parent 的是子工作线，明确属于某条子工作线时归到子工作线；"
        "无法判断或与所有工作线都无关时 workstream_id 填 null，不要勉强归类。"
        "只输出 JSON 数组，每项严格使用 {\"id\": 条目ID, \"workstream_id\": 工作线ID或null}，不要 Markdown。\n\n"
        f"工作线：\n{json.dumps(workstreams, ensure_ascii=False, indent=2)}\n\n"
        f"PR / Issue：\n{json.dumps(items, ensure_ascii=False, indent=2)}"
    )


def classify_week_items(conn, project_id, week_key, timeout=120):
    """Agent links for this week's unlinked items to active workstreams.
    Returns how many were linked."""
    from .workstream_agent import _chat, _fake, fake_classify, parse_json_array
    from .workstreams import workstreams_for_prompt

    workstreams = workstreams_for_prompt(conn, project_id)
    if not workstreams:
        return 0
    active = {w["id"] for w in workstreams}
    rows = conn.execute(
        """
        SELECT g.id, g.kind, g.number, g.title, r.repo, r.notes FROM workstream_git_items g
        JOIN github_repos r ON r.id = g.repo_id
        WHERE g.project_id = ? AND g.week_key = ? AND g.workstream_id IS NULL ORDER BY g.id
        """,
        (project_id, week_key),
    ).fetchall()
    conn.commit()  # nothing pending while the model call runs
    linked = 0
    for start in range(0, len(rows), CLASSIFY_BATCH):
        batch = rows[start:start + CLASSIFY_BATCH]
        items = [
            {"id": r["id"], "repo": r["repo"], "kind": r["kind"], "title": r["title"], "repo_notes": (r["notes"] or "")[:200]}
            for r in batch
        ]
        if _fake():
            choices = {item["id"]: fake_classify(f"{item['repo']} {item['title']}", workstreams) for item in items}
        else:
            choices = {
                entry.get("id"): entry.get("workstream_id")
                for entry in parse_json_array(_chat(conn, build_git_classify_prompt(workstreams, items), timeout))
            }
        for item in items:
            choice = choices.get(item["id"])
            try:
                choice = int(choice) if choice is not None else None
            except (TypeError, ValueError):
                choice = None
            if choice in active:
                cur = conn.execute(
                    "UPDATE workstream_git_items SET workstream_id = ?, link_source = 'auto' WHERE id = ? AND workstream_id IS NULL",
                    (choice, item["id"]),
                )
                linked += cur.rowcount
        conn.commit()
    return linked


def sync_week(conn, project_id, timeout=120, extras_list=None):
    """Fetch (unless the extras are given), store and classify the current
    week's PR / issue activity. Returns {"items", "linked"}."""
    project = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        return {"items": 0, "linked": 0}
    week_key = current_week_key(project["timezone"])
    conn.commit()
    if extras_list is None:
        extras_list = fetch_week_activity(conn, project_id)
    items = store_week_activity(conn, project_id, week_key, extras_list)
    conn.commit()
    linked = classify_week_items(conn, project_id, week_key, timeout) if items else 0
    return {"items": items, "linked": linked}


# ---------------------------------------------------------------- reads and manual links


def _label(row):
    return f"{row['repo']}#{row['number']}"


def state_label(row):
    if row["kind"] == "pr":
        if row["merged"]:
            return "merged"
        if row["draft"] and row["state"] in ("open", "opened"):
            return "draft"
    return "open" if row["state"] in ("open", "opened") else ("closed" if row["state"] else "")


def week_items_by_workstream(conn, project_id, week_key, per_workstream=PER_WORKSTREAM):
    """{workstream_id: [{"repo", "kind", "number", "title", "state"}]} for
    the week, newest first."""
    result = {}
    for row in conn.execute(
        """
        SELECT g.*, r.repo FROM workstream_git_items g JOIN github_repos r ON r.id = g.repo_id
        WHERE g.project_id = ? AND g.week_key = ? AND g.workstream_id IS NOT NULL
        ORDER BY g.updated_at DESC, g.id DESC
        """,
        (project_id, week_key),
    ):
        items = result.setdefault(row["workstream_id"], [])
        if len(items) < per_workstream:
            items.append({"ref": _label(row), "kind": row["kind"], "title": row["title"], "state": state_label(row)})
    return result


def activity_counts(conn, project_id):
    """{workstream_id: {week_key: n}} of linked items."""
    counts = {}
    for row in conn.execute(
        """
        SELECT workstream_id, week_key, COUNT(*) AS n FROM workstream_git_items
        WHERE project_id = ? AND workstream_id IS NOT NULL GROUP BY workstream_id, week_key
        """,
        (project_id,),
    ):
        counts.setdefault(row["workstream_id"], {})[row["week_key"]] = row["n"]
    return counts


def _item_payload(row):
    return {
        "id": row["id"], "repo": row["repo"], "kind": row["kind"], "number": row["number"], "title": row["title"],
        "state": state_label(row), "url": row["url"], "author": row["author"], "week_key": row["week_key"],
        "updated_at": row["updated_at"], "workstream_id": row["workstream_id"], "link_source": row["link_source"],
    }


def workstream_git_items(conn, workstream_id, limit=40):
    """The latest week's row of every item linked to the workstream."""
    rows = conn.execute(
        """
        SELECT g.*, r.repo FROM workstream_git_items g JOIN github_repos r ON r.id = g.repo_id
        WHERE g.workstream_id = ? AND g.week_key = (
            SELECT MAX(week_key) FROM workstream_git_items x WHERE x.repo_id = g.repo_id AND x.kind = g.kind AND x.number = g.number
        )
        ORDER BY g.week_key DESC, g.updated_at DESC LIMIT ?
        """,
        (workstream_id, limit),
    ).fetchall()
    return [_item_payload(r) for r in rows]


def unassigned_week_items(conn, project_id, week_key, limit=100):
    rows = conn.execute(
        """
        SELECT g.*, r.repo FROM workstream_git_items g JOIN github_repos r ON r.id = g.repo_id
        WHERE g.project_id = ? AND g.week_key = ? AND g.workstream_id IS NULL ORDER BY g.updated_at DESC LIMIT ?
        """,
        (project_id, week_key, limit),
    ).fetchall()
    return [_item_payload(r) for r in rows]


def set_item_link(conn, project_id, item_id, workstream_id):
    """A person's choice, applied to every week's row of the item."""
    row = conn.execute(
        "SELECT repo_id, kind, number FROM workstream_git_items WHERE id = ? AND project_id = ?", (item_id, project_id)
    ).fetchone()
    if not row:
        raise LookupError("PR / issue not found")
    target = _workstream(conn, project_id, workstream_id)
    conn.execute(
        "UPDATE workstream_git_items SET workstream_id = ?, link_source = ? WHERE repo_id = ? AND kind = ? AND number = ?",
        (target, "manual" if target else "", row["repo_id"], row["kind"], row["number"]),
    )


def set_repo_workstream(conn, project_id, repo_id, workstream_id):
    """The repository's default workstream; applied to its unlinked items
    and to items it linked before, never to agent or manual links."""
    if not conn.execute("SELECT 1 FROM github_repos WHERE id = ? AND project_id = ?", (repo_id, project_id)).fetchone():
        raise ValidationError("repository not found")
    target = _workstream(conn, project_id, workstream_id)
    conn.execute("UPDATE github_repos SET workstream_id = ? WHERE id = ?", (target, repo_id))
    conn.execute(
        """
        UPDATE workstream_git_items SET workstream_id = ?, link_source = ?
        WHERE repo_id = ? AND (workstream_id IS NULL OR link_source = 'repo')
        """,
        (target, "repo" if target else "", repo_id),
    )


def _workstream(conn, project_id, value):
    if value in (None, "", 0, "0"):
        return None
    try:
        workstream_id = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("invalid workstream id") from exc
    if not conn.execute("SELECT 1 FROM workstreams WHERE id = ? AND project_id = ?", (workstream_id, project_id)).fetchone():
        raise ValidationError("workstream does not belong to this project")
    return workstream_id


def annotate_extras(conn, project_id, extras_list):
    """Tag report-context PR / issue entries with their workstream path."""
    from .workstreams import list_workstreams, workstream_paths

    paths = workstream_paths(list_workstreams(conn, project_id))
    links = {}
    for row in conn.execute(
        """
        SELECT r.repo, r.git_mode, g.kind, g.number, g.workstream_id FROM workstream_git_items g
        JOIN github_repos r ON r.id = g.repo_id WHERE g.project_id = ? AND g.workstream_id IS NOT NULL
        ORDER BY g.week_key
        """,
        (project_id,),
    ):
        links[(row["repo"].lower(), row["git_mode"], row["kind"], row["number"])] = paths.get(row["workstream_id"], "")
    for extras in extras_list or []:
        for kind, key in (("pr", "pull_requests"), ("issue", "issues")):
            for entry in _section(extras, key):
                path = links.get((str(extras.get("repo") or "").lower(), extras.get("git_mode") or "github", kind, entry.get("number")))
                if path:
                    entry["workstream"] = path
    return extras_list
