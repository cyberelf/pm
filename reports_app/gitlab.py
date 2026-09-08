"""GitLab REST API (v4) access for repository status, branches, and commits.

Requests go straight to the configured GitLab instance with a per-user
personal access token in the PRIVATE-TOKEN header; public projects are
readable without a token. (This used to be delegated to the local `glab`
CLI, which cannot isolate credentials per user.)
"""

import json
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import quote, urlparse

from .config import DEFAULT_GITLAB_SERVER, TRACK_ALL_BRANCHES
from .github import _commit_result, normalize_branches
from .validation import ValidationError, validate_gitlab_server

API_PREFIX = "api/v4"
PAGE_SIZE = 100
MAX_PAGES = 5
USER_AGENT = "weekly-reports"

_insecure_context = None


def _ssl_context(skip_verify):
    """TLS context for self-signed / internal-CA GitLab instances; None keeps
    default certificate verification."""
    global _insecure_context
    if not skip_verify:
        return None
    if _insecure_context is None:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        _insecure_context = context
    return _insecure_context


def resolve_server(server):
    try:
        return validate_gitlab_server(server) or DEFAULT_GITLAB_SERVER
    except ValidationError:
        return DEFAULT_GITLAB_SERVER


def gitlab_host(server):
    return urlparse(resolve_server(server)).hostname


def project_path(repo):
    return quote(str(repo or "").strip(), safe="")


def _request(server, path, token, timeout, skip_verify=False):
    """One GET against the GitLab v4 API with the same result contract as
    github._request: (payload, status_code, error)."""
    url = f"{resolve_server(server).rstrip('/')}/{API_PREFIX}/{path}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    if token:
        request.add_header("PRIVATE-TOKEN", token)
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=_ssl_context(skip_verify)) as response:
            raw = response.read().decode("utf-8")
        try:
            return json.loads(raw or "null"), 200, None
        except ValueError as exc:
            return None, 200, f"failed to parse response: {exc}"
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return None, exc.code, body or str(exc)
    except Exception as exc:
        return None, None, str(exc)


def _api_error(status_code, error):
    text = f"GitLab API error {status_code}: {(error or '').strip()[:300]}"
    if status_code == 404:
        text += "；项目不存在、路径有误，或为私有项目且令牌无权访问（GitLab 对未授权的私有项目同样返回 404）"
    return text


def _unreachable_message(error):
    text = f"GitLab server unreachable: {error}"
    if "certificate verify failed" in str(error):
        text += "；GitLab 证书校验失败（自签名或内部 CA），可在 全局设置 → Git 集成 勾选「跳过 SSL 证书校验」后重试"
    return text


def _unreachable(error):
    return {
        "status": "disconnected",
        "status_message": _unreachable_message(error),
        "activity_summary": "",
        "last_activity_at": None,
    }


def _paginate(server, path, token, timeout, skip_verify=False):
    items = []
    for page in range(1, MAX_PAGES + 1):
        separator = "&" if "?" in path else "?"
        payload, status_code, error = _request(
            server, f"{path}{separator}per_page={PAGE_SIZE}&page={page}", token, timeout, skip_verify=skip_verify
        )
        if status_code is None:
            return None, _unreachable_message(error)
        if status_code != 200:
            return None, _api_error(status_code, error)
        if not isinstance(payload, list):
            return None, "unexpected GitLab API response shape"
        items.extend(payload)
        if len(payload) < PAGE_SIZE:
            break
    return items, None


def check_repo(repo, server="", token="", timeout=20, skip_verify=False):
    encoded = project_path(repo)
    data, status_code, error = _request(server, f"projects/{encoded}", token, timeout, skip_verify=skip_verify)
    if status_code is None:
        return _unreachable(error)
    if status_code == 401:
        return {
            "status": "unauthenticated",
            "status_message": "GitLab token was rejected; check 全局设置 Git 集成 token",
            "activity_summary": "",
            "last_activity_at": None,
        }
    if status_code == 404:
        return {
            "status": "inaccessible",
            "status_message": "项目不存在、group/project 路径有误，或为私有项目且当前令牌无权访问（GitLab 对未授权的私有项目同样返回 404）",
            "activity_summary": "",
            "last_activity_at": None,
        }
    if status_code != 200:
        return {
            "status": "inaccessible",
            "status_message": _api_error(status_code, error),
            "activity_summary": "",
            "last_activity_at": None,
        }
    default_branch = (data.get("default_branch") or "main").strip() or "main"
    merge_requests, _, _ = _request(
        server,
        f"projects/{encoded}/merge_requests?scope=all&state=all&per_page=10&order_by=updated_at",
        token,
        timeout,
        skip_verify=skip_verify,
    )
    issues, _, _ = _request(
        server,
        f"projects/{encoded}/issues?scope=all&state=all&per_page=10",
        token,
        timeout,
        skip_verify=skip_verify,
    )
    parts = [f"Repository {data.get('path_with_namespace') or repo}"]
    if data.get("description"):
        parts.append(data["description"])
    if data.get("last_activity_at"):
        parts.append(f"Last activity: {data['last_activity_at']}")
    parts.append(f"Default branch: {default_branch}")
    if isinstance(merge_requests, list):
        parts.append(f"Recent merge requests: {len(merge_requests)}")
    if isinstance(issues, list):
        parts.append(f"Recent issues: {len(issues)}")
    host = gitlab_host(server)
    return {
        "status": "connected",
        "status_message": f"connected through GitLab API ({host})",
        "activity_summary": "\n".join(parts),
        "last_activity_at": data.get("last_activity_at"),
        "default_branch": default_branch,
    }


def list_branches(repo, server="", token="", timeout=30, skip_verify=False):
    items, error = _paginate(
        server, f"projects/{project_path(repo)}/repository/branches", token, timeout, skip_verify=skip_verify
    )
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
        "branches": [item.get("name") for item in items if isinstance(item, dict) and item.get("name")],
    }


def weekly_commits(repo, since, until, branches=None, server="", token="", timeout=30, skip_verify=False):
    tracked_branches = normalize_branches(branches)
    branch_names = tracked_branches
    tracking_all = TRACK_ALL_BRANCHES in tracked_branches
    if tracking_all:
        branch_result = list_branches(repo, server=server, token=token, timeout=timeout, skip_verify=skip_verify)
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
        items, error = _paginate(server, endpoint, token, timeout, skip_verify=skip_verify)
        if error:
            errors.append(f"{branch}: {error}")
            continue
        for item in items:
            add_commit(commits_by_sha, item, branch)
    return _commit_result(repo, tracked_branches, branch_names, commits_by_sha, errors, tracking_all)


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
