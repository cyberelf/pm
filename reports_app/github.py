import json
import shutil
import subprocess
from urllib.parse import urlencode

from .config import TRACK_ALL_BRANCHES
from .timeutil import iso_now


def check_repo(repo, timeout=20):
    if not shutil.which("gh"):
        return {
            "status": "disconnected",
            "status_message": "local GitHub CLI (`gh`) is missing",
            "activity_summary": "",
            "last_activity_at": None,
        }
    auth = subprocess.run(["gh", "auth", "status"], text=True, capture_output=True, timeout=timeout)
    if auth.returncode != 0:
        return {
            "status": "unauthenticated",
            "status_message": (auth.stderr or auth.stdout or "local gh is unauthenticated").strip(),
            "activity_summary": "",
            "last_activity_at": None,
        }
    view = subprocess.run(
        ["gh", "repo", "view", repo, "--json", "nameWithOwner,pushedAt,description,defaultBranchRef"],
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if view.returncode != 0:
        return {
            "status": "inaccessible",
            "status_message": (view.stderr or view.stdout or "repository inaccessible").strip(),
            "activity_summary": "",
            "last_activity_at": None,
        }
    data = json.loads(view.stdout or "{}")
    default_branch = ((data.get("defaultBranchRef") or {}).get("name") or "main").strip() or "main"
    prs = subprocess.run(
        ["gh", "pr", "list", "-R", repo, "--state", "all", "--limit", "10", "--json", "number,title,state,updatedAt"],
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    issues = subprocess.run(
        ["gh", "issue", "list", "-R", repo, "--state", "all", "--limit", "10", "--json", "number,title,state,updatedAt"],
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    parts = [f"Repository {data.get('nameWithOwner', repo)}"]
    if data.get("description"):
        parts.append(data["description"])
    if data.get("pushedAt"):
        parts.append(f"Last push: {data['pushedAt']}")
    parts.append(f"Default branch: {default_branch}")
    if prs.returncode == 0:
        pr_data = json.loads(prs.stdout or "[]")
        parts.append(f"Recent PRs: {len(pr_data)}")
    if issues.returncode == 0:
        issue_data = json.loads(issues.stdout or "[]")
        parts.append(f"Recent issues: {len(issue_data)}")
    return {
        "status": "connected",
        "status_message": "connected through local gh",
        "activity_summary": "\n".join(parts),
        "last_activity_at": data.get("pushedAt"),
        "default_branch": default_branch,
    }


def refresh_repo(conn, repo_id):
    repo_row = conn.execute("SELECT * FROM github_repos WHERE id = ?", (repo_id,)).fetchone()
    result = check_repo(repo_row["repo"])
    now = iso_now()
    conn.execute(
        """
        UPDATE github_repos
        SET status = ?, status_message = ?, activity_summary = ?, last_activity_at = ?,
            last_checked_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            result["status"],
            result["status_message"],
            result["activity_summary"],
            result["last_activity_at"],
            now,
            now,
            repo_id,
        ),
    )
    return result


def list_branches(repo, timeout=30):
    if not shutil.which("gh"):
        return {
            "repo": repo,
            "status": "disconnected",
            "status_message": "local GitHub CLI (`gh`) is missing",
            "branches": [],
        }
    endpoint = f"repos/{repo}/branches?per_page=100"
    result = subprocess.run(
        ["gh", "api", "--paginate", "--slurp", endpoint],
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        return {
            "repo": repo,
            "status": "failed",
            "status_message": (result.stderr or result.stdout or "failed to read branches").strip(),
            "branches": [],
        }
    try:
        data = flatten_api_pages(json.loads(result.stdout or "[]"))
    except (json.JSONDecodeError, ValueError) as exc:
        return {
            "repo": repo,
            "status": "failed",
            "status_message": f"failed to parse branches: {exc}",
            "branches": [],
        }
    return {
        "repo": repo,
        "status": "ok",
        "status_message": f"{len(data)} branches",
        "branches": [item.get("name") for item in data if item.get("name")],
    }


def weekly_commits(repo, since, until, branches=None, timeout=30):
    tracked_branches = normalize_branches(branches)
    if not shutil.which("gh"):
        return {
            "repo": repo,
            "branches": tracked_branches,
            "resolved_branches": [],
            "status": "disconnected",
            "status_message": "local GitHub CLI (`gh`) is missing",
            "commits": [],
        }
    branch_names = tracked_branches
    tracking_all = TRACK_ALL_BRANCHES in tracked_branches
    if tracking_all:
        branch_result = list_branches(repo, timeout=timeout)
        if branch_result["status"] != "ok":
            return {
                "repo": repo,
                "branches": tracked_branches,
                "resolved_branches": [],
                "status": branch_result["status"],
                "status_message": f"failed to resolve all remote branches: {branch_result['status_message']}",
                "commits": [],
            }
        branch_names = branch_result["branches"]
    since_q = since.isoformat().replace("+00:00", "Z")
    until_q = until.isoformat().replace("+00:00", "Z")
    commits_by_sha = {}
    errors = []
    for branch in branch_names:
        query = urlencode({"sha": branch, "since": since_q, "until": until_q, "per_page": "100"}, safe="")
        endpoint = f"repos/{repo}/commits?{query}"
        result = subprocess.run(
            ["gh", "api", "--method", "GET", "--paginate", "--slurp", endpoint],
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            errors.append(f"{branch}: {(result.stderr or result.stdout or 'failed to read commits').strip()}")
            continue
        try:
            data = flatten_api_pages(json.loads(result.stdout or "[]"))
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{branch}: failed to parse commits: {exc}")
            continue
        for item in data:
            add_commit(commits_by_sha, item, branch)
    commits = sorted(commits_by_sha.values(), key=lambda item: item.get("date") or "", reverse=True)
    status = "ok"
    if errors and commits:
        status = "partial"
    elif errors:
        status = "failed"
    scope = "all remote branches" if tracking_all else "selected branches"
    status_message = f"{len(commits)} commits in current project week across {len(branch_names)} {scope}"
    if errors:
        status_message = f"{status_message}; errors: {'; '.join(errors)}"
    return {
        "repo": repo,
        "branches": tracked_branches,
        "resolved_branches": branch_names,
        "status": status,
        "status_message": status_message,
        "commits": commits,
    }


def normalize_branches(branches):
    result = []
    for branch in branches or ["main"]:
        name = str(branch or "").strip()
        if name and name not in result:
            result.append(name)
    return result or ["main"]


def flatten_api_pages(pages):
    if not isinstance(pages, list):
        raise ValueError("unexpected paginated response shape")
    items = []
    for page in pages:
        if isinstance(page, list):
            items.extend(page)
        elif isinstance(page, dict):
            items.append(page)
        else:
            raise ValueError("unexpected paginated response item")
    if any(not isinstance(item, dict) for item in items):
        raise ValueError("unexpected paginated response item")
    return items


def add_commit(commits_by_sha, item, branch):
    sha = item.get("sha") or ""
    if not sha:
        return
    commit = item.get("commit") or {}
    author = commit.get("author") or {}
    existing = commits_by_sha.get(sha)
    if existing:
        if branch not in existing["branches"]:
            existing["branches"].append(branch)
        return
    commits_by_sha[sha] = {
        "sha": sha[:12],
        "message": (commit.get("message") or "").splitlines()[0],
        "author": author.get("name") or "",
        "date": author.get("date") or "",
        "url": item.get("html_url") or "",
        "branches": [branch],
    }
