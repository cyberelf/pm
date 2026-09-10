"""GitHub REST API access for repository status, branches, and commits.

Requests go to api.github.com directly. A per-user personal access token is
used when configured; without one only public data is reachable and the
anonymous rate limit applies. (This used to be delegated to the local `gh`
CLI, which cannot isolate credentials per user.)
"""

import json
import urllib.error
import urllib.request
from urllib.parse import quote, urlencode

from .config import TRACK_ALL_BRANCHES

API_BASE = "https://api.github.com"
PAGE_SIZE = 100
MAX_PAGES = 5
USER_AGENT = "zreport"


def _request(path, token, timeout):
    """One GET against the GitHub REST API.

    Returns (payload, status_code, error): status_code is None for network
    level failures, and error carries the response body or exception text.
    """
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
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


def token_kind(token):
    """classic / fine-grained / unknown, detected from the token prefix."""
    token = token or ""
    if token.startswith("github_pat_"):
        return "fine-grained"
    if token.startswith(("ghp_", "gho_", "ghu_", "ghs_", "ghr_")):
        return "classic"
    return "unknown"


def _token_access_hint(token_kind_value):
    if token_kind_value == "fine-grained":
        return "fine-grained token 需在 Repository access 中包含该仓库（Contents: Read-only）；组织仓库还要求 Resource owner 选对组织并由组织批准"
    if token_kind_value == "classic":
        return "经典 token 需勾选 repo 权限（public_repo 仅公开仓库）；组织启用 SAML SSO 时还需在令牌设置里对该组织执行 SSO 授权"
    return "fine-grained token 需在 Repository access 中包含该仓库（Contents: Read-only），经典 token 需 repo 权限"


def _api_error(status_code, error):
    text = f"GitHub API error {status_code}: {(error or '').strip()[:300]}"
    if status_code == 404:
        text += "；仓库不存在、owner/repo 路径有误，或为私有仓库且令牌无权访问（GitHub 对未授权的私有仓库同样返回 404）"
    return text


def _paginate(path, token, timeout):
    items = []
    for page in range(1, MAX_PAGES + 1):
        separator = "&" if "?" in path else "?"
        payload, status_code, error = _request(
            f"{path}{separator}per_page={PAGE_SIZE}&page={page}", token, timeout
        )
        if status_code is None:
            return None, f"GitHub API unreachable: {error}"
        if status_code != 200:
            return None, _api_error(status_code, error)
        if not isinstance(payload, list):
            return None, "unexpected GitHub API response shape"
        items.extend(payload)
        if len(payload) < PAGE_SIZE:
            break
    return items, None


def _unreachable(error):
    return {
        "status": "disconnected",
        "status_message": f"GitHub API unreachable: {error}",
        "activity_summary": "",
        "last_activity_at": None,
    }


def check_repo(repo, token="", timeout=20):
    data, status_code, error = _request(f"/repos/{quote(repo, safe='/')}", token, timeout)
    if status_code is None:
        return _unreachable(error)
    if status_code == 401:
        return {
            "status": "unauthenticated",
            "status_message": "GitHub token was rejected; check 全局设置 Git 集成 token",
            "activity_summary": "",
            "last_activity_at": None,
        }
    if status_code == 404:
        # GitHub answers 404 both for unknown repos and for private repos the
        # token cannot see; one anonymous probe tells the two apart. Guidance
        # is tailored to the detected token type.
        owner = repo.split("/", 1)[0]
        kind = token_kind(token)
        if token:
            _, anon_status, _ = _request(f"/repos/{quote(repo, safe='/')}", "", timeout)
            if anon_status == 200:
                return {
                    "status": "inaccessible",
                    "status_message": f"仓库存在但当前令牌无权访问：{_token_access_hint(kind)}",
                    "activity_summary": "",
                    "last_activity_at": None,
                }
            # owner is an organization? org repos additionally require the
            # token's resource owner to be that org plus org approval
            # (fine-grained) or a SAML SSO authorization (classic).
            org_data, org_status, _ = _request(f"/orgs/{quote(owner, safe='')}", token, timeout)
            if org_status == 200 and org_data and org_data.get("login", "").lower() == owner.lower():
                return {
                    "status": "inaccessible",
                    "status_message": f"{owner} 是组织，组织仓库对令牌有额外要求：{_token_access_hint(kind)}",
                    "activity_summary": "",
                    "last_activity_at": None,
                }
        return {
            "status": "inaccessible",
            "status_message": "仓库不存在、owner/repo 路径有误，或为私有仓库且当前令牌无权访问（GitHub 对未授权的私有仓库同样返回 404）",
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
    pulls, _, _ = _request(
        f"/repos/{quote(repo, safe='/')}/pulls?state=all&per_page=10&sort=updated", token, timeout
    )
    issues, _, _ = _request(
        f"/repos/{quote(repo, safe='/')}/issues?state=all&per_page=10&sort=updated", token, timeout
    )
    parts = [f"Repository {data.get('full_name', repo)}"]
    if data.get("description"):
        parts.append(data["description"])
    if data.get("pushed_at"):
        parts.append(f"Last push: {data['pushed_at']}")
    parts.append(f"Default branch: {default_branch}")
    if isinstance(pulls, list):
        parts.append(f"Recent PRs: {len(pulls)}")
    if isinstance(issues, list):
        parts.append(f"Recent issues: {len([item for item in issues if 'pull_request' not in item])}")
    return {
        "status": "connected",
        "status_message": "connected through GitHub API",
        "activity_summary": "\n".join(parts),
        "last_activity_at": data.get("pushed_at"),
        "default_branch": default_branch,
    }


def list_branches(repo, token="", timeout=30):
    items, error = _paginate(f"/repos/{quote(repo, safe='/')}/branches", token, timeout)
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


def weekly_commits(repo, since, until, branches=None, token="", timeout=30):
    tracked_branches = normalize_branches(branches)
    branch_names = tracked_branches
    tracking_all = TRACK_ALL_BRANCHES in tracked_branches
    if tracking_all:
        branch_result = list_branches(repo, token=token, timeout=timeout)
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
        query = urlencode(
            {"sha": branch, "since": since_q, "until": until_q},
            safe="",
        )
        items, error = _paginate(f"/repos/{quote(repo, safe='/')}/commits?{query}", token, timeout)
        if error:
            errors.append(f"{branch}: {error}")
            continue
        for item in items:
            add_commit(commits_by_sha, item, branch)
    return _commit_result(repo, tracked_branches, branch_names, commits_by_sha, errors, tracking_all)


def _commit_result(repo, tracked_branches, branch_names, commits_by_sha, errors, tracking_all):
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
