import json
import shutil
import subprocess
from datetime import datetime, timezone
from urllib.parse import quote, urlparse

from .config import DEFAULT_GITLAB_SERVER, MAX_GITLAB_PAGES, TRACK_ALL_BRANCHES
from .github import flatten_api_pages, normalize_branches
from .validation import ValidationError, validate_gitlab_server

PAGE_SIZE = 100


def resolve_server(server):
    try:
        return validate_gitlab_server(server) or DEFAULT_GITLAB_SERVER
    except ValidationError:
        return DEFAULT_GITLAB_SERVER


def gitlab_host(server):
    return urlparse(resolve_server(server)).hostname


def project_path(repo):
    return quote(str(repo or "").strip(), safe="")


def run_glab(args, timeout):
    return subprocess.run(["glab", *args], text=True, capture_output=True, timeout=timeout)


def check_repo(repo, server="", timeout=20):
    host = gitlab_host(server)
    if not shutil.which("glab"):
        return {
            "status": "disconnected",
            "status_message": "local GitLab CLI (`glab`) is missing",
            "activity_summary": "",
            "last_activity_at": None,
        }
    auth = run_glab(["auth", "status", "--hostname", host], timeout=timeout)
    if auth.returncode != 0:
        return {
            "status": "unauthenticated",
            "status_message": (auth.stderr or auth.stdout or f"local glab is unauthenticated for {host}").strip(),
            "activity_summary": "",
            "last_activity_at": None,
        }
    encoded = project_path(repo)
    view = run_glab(["api", f"projects/{encoded}", "--hostname", host], timeout=timeout)
    if view.returncode != 0:
        return {
            "status": "inaccessible",
            "status_message": (view.stderr or view.stdout or "repository inaccessible").strip(),
            "activity_summary": "",
            "last_activity_at": None,
        }
    try:
        data = json.loads(view.stdout or "{}")
    except (json.JSONDecodeError, ValueError) as exc:
        return {
            "status": "inaccessible",
            "status_message": f"failed to parse repository: {exc}",
            "activity_summary": "",
            "last_activity_at": None,
        }
    default_branch = (data.get("default_branch") or "main").strip() or "main"
    merge_requests = run_glab(
        ["api", f"projects/{encoded}/merge_requests?scope=all&state=all&per_page=10&order_by=updated_at", "--hostname", host],
        timeout=timeout,
    )
    issues = run_glab(
        ["api", f"projects/{encoded}/issues?scope=all&state=all&per_page=10", "--hostname", host],
        timeout=timeout,
    )
    parts = [f"Repository {data.get('path_with_namespace') or repo}"]
    if data.get("description"):
        parts.append(data["description"])
    if data.get("last_activity_at"):
        parts.append(f"Last activity: {data['last_activity_at']}")
    parts.append(f"Default branch: {default_branch}")
    if merge_requests.returncode == 0:
        parts.append(f"Recent merge requests: {len(json.loads(merge_requests.stdout or '[]'))}")
    if issues.returncode == 0:
        parts.append(f"Recent issues: {len(json.loads(issues.stdout or '[]'))}")
    return {
        "status": "connected",
        "status_message": f"connected through local glab ({host})",
        "activity_summary": "\n".join(parts),
        "last_activity_at": data.get("last_activity_at"),
        "default_branch": default_branch,
    }


def list_branches(repo, server="", timeout=30):
    host = gitlab_host(server)
    if not shutil.which("glab"):
        return {
            "repo": repo,
            "status": "disconnected",
            "status_message": "local GitLab CLI (`glab`) is missing",
            "branches": [],
        }
    items, error = fetch_paginated(f"projects/{project_path(repo)}/repository/branches", host, timeout=timeout)
    if error:
        return {
            "repo": repo,
            "status": "failed",
            "status_message": error,
            "branches": [],
        }
    return {
        "repo": repo,
        "status": "ok",
        "status_message": f"{len(items)} branches",
        "branches": [item.get("name") for item in items if item.get("name")],
    }


def weekly_commits(repo, since, until, branches=None, server="", timeout=30):
    tracked_branches = normalize_branches(branches)
    host = gitlab_host(server)
    if not shutil.which("glab"):
        return {
            "repo": repo,
            "branches": tracked_branches,
            "resolved_branches": [],
            "status": "disconnected",
            "status_message": "local GitLab CLI (`glab`) is missing",
            "commits": [],
        }
    branch_names = tracked_branches
    tracking_all = TRACK_ALL_BRANCHES in tracked_branches
    if tracking_all:
        branch_result = list_branches(repo, server=server, timeout=timeout)
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
        endpoint = (
            f"projects/{project_path(repo)}/repository/commits"
            f"?ref_name={quote(branch, safe='')}&since={quote(since_q, safe='')}&until={quote(until_q, safe='')}"
        )
        items, error = fetch_paginated(endpoint, host, timeout=timeout)
        if error:
            errors.append(f"{branch}: {error}")
            continue
        for item in items:
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


def fetch_paginated(endpoint, host, timeout, max_pages=MAX_GITLAB_PAGES):
    items = []
    for page in range(1, max_pages + 1):
        separator = "&" if "?" in endpoint else "?"
        result = run_glab(
            ["api", f"{endpoint}{separator}per_page={PAGE_SIZE}&page={page}", "--hostname", host],
            timeout=timeout,
        )
        if result.returncode != 0:
            return None, (result.stderr or result.stdout or "request failed").strip()
        try:
            data = flatten_api_pages(json.loads(result.stdout or "[]"))
        except (json.JSONDecodeError, ValueError) as exc:
            return None, f"failed to parse response: {exc}"
        items.extend(data)
        if len(data) < PAGE_SIZE:
            break
    return items, None


def add_commit(commits_by_sha, item, branch):
    sha = item.get("id") or item.get("short_id") or ""
    if not sha:
        return
    existing = commits_by_sha.get(sha)
    if existing:
        if branch not in existing["branches"]:
            existing["branches"].append(branch)
        return
    message = (item.get("title") or "").strip() or ((item.get("message") or "").splitlines() or [""])[0]
    commits_by_sha[sha] = {
        "sha": sha[:12],
        "message": message,
        "author": item.get("author_name") or item.get("committer_name") or "",
        "date": normalize_date(item.get("committed_date") or item.get("authored_date") or ""),
        "url": item.get("web_url") or "",
        "branches": [branch],
    }


def normalize_date(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return str(value or "")
