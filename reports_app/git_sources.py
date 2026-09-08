"""Dispatch repository reads to the REST client for the configured git host.

Per-user credentials and the global GitHub/GitLab switches travel together
in an auth_info dict built by git_auth_for_user(); report generation looks
the credentials up through the owning project's user, so background jobs
work without a request context.
"""

import json

from .config import (
    GIT_MODE_GITLAB,
    GITHUB_ENABLED_SETTING,
    GITHUB_TOKEN_SETTING,
    GITHUB_TOKENS_SETTING,
    GITLAB_ENABLED_SETTING,
    GITLAB_TOKEN_SETTING,
    GITLAB_URL_SETTING,
)
from .db import get_setting, get_user_setting
from .gitlab import check_repo as gitlab_check_repo
from .gitlab import list_branches as gitlab_list_branches
from .gitlab import weekly_commits as gitlab_weekly_commits
from .github import check_repo as github_check_repo
from .github import list_branches as github_list_branches
from .github import weekly_commits as github_weekly_commits
from .timeutil import iso_now


def load_github_tokens(conn, user_id):
    """Token entries as stored by 全局设置: [{label, owner, token}]. An entry
    with an owner serves that organization's repos only; an ownerless entry
    (classic token or personal fine-grained token) is the fallback for
    everything else. The pre-list single github_token setting still works as
    the deepest fallback so existing accounts keep working untouched."""
    raw = get_user_setting(conn, user_id, GITHUB_TOKENS_SETTING, "")
    try:
        entries = json.loads(raw or "[]")
    except ValueError:
        entries = []
    result = [
        {"label": str(e.get("label") or ""), "owner": str(e.get("owner") or "").strip().lower(), "token": str(e.get("token") or "")}
        for e in entries
        if isinstance(e, dict) and e.get("token")
    ]
    if not result:
        legacy = get_user_setting(conn, user_id, GITHUB_TOKEN_SETTING, "")
        if legacy:
            result = [{"label": "通用", "owner": "", "token": legacy}]
    return result


def github_token_candidates(info, repo):
    """Ordered token entries for a repo: a per-org entry matching the repo's
    owner first, then the ownerless (classic / personal) entry, then the
    legacy single token."""
    owner = (repo or "").split("/", 1)[0].strip().lower()
    entries = info.get("github_tokens") or []
    ordered = [entry for entry in entries if entry["owner"] and entry["owner"] == owner and entry["token"]]
    ordered += [entry for entry in entries if not entry["owner"] and entry["token"]]
    legacy = info.get("github_token", "")
    if legacy and not any(entry["token"] == legacy for entry in ordered):
        ordered.append({"label": "旧令牌", "owner": "", "token": legacy})
    return ordered


def github_token_for(info, repo):
    candidates = github_token_candidates(info, repo)
    return candidates[0]["token"] if candidates else ""


def git_auth_for_user(conn, user_id):
    return {
        "github_token": get_user_setting(conn, user_id, GITHUB_TOKEN_SETTING),
        "github_tokens": load_github_tokens(conn, user_id),
        "gitlab_token": get_user_setting(conn, user_id, GITLAB_TOKEN_SETTING),
        "gitlab_url": get_user_setting(conn, user_id, GITLAB_URL_SETTING),
        "github_enabled": get_setting(conn, GITHUB_ENABLED_SETTING, "1") != "0",
        "gitlab_enabled": get_setting(conn, GITLAB_ENABLED_SETTING, "1") != "0",
    }


def _gitlab_server(info):
    """Every GitLab repo goes through the account's GitLab URL from
    全局设置 → Git 集成; there is no per-repo server address anymore."""
    return (info.get("gitlab_url") or "").strip()


def _disabled_result(message):
    return {
        "status": "disabled",
        "status_message": message,
        "activity_summary": "",
        "last_activity_at": None,
    }


def check_repo(repo, git_mode="github", auth_info=None, timeout=20):
    info = auth_info or {}
    if git_mode == GIT_MODE_GITLAB:
        if not info.get("gitlab_enabled", True):
            return _disabled_result("GitLab 集成已在全局设置中停用，无法读取该仓库")
        return gitlab_check_repo(
            repo, server=_gitlab_server(info), token=info.get("gitlab_token", ""), timeout=timeout
        )
    if not info.get("github_enabled", True):
        return _disabled_result("GitHub 集成已在全局设置中停用，无法读取该仓库")
    candidates = github_token_candidates(info, repo)
    result = github_check_repo(repo, token=candidates[0]["token"] if candidates else "", timeout=timeout)
    if candidates and result.get("status") in {"inaccessible", "unauthenticated"}:
        # the primary token may simply not cover this repo; probe the other
        # configured tokens before reporting the repo inaccessible
        for candidate in candidates[1:]:
            retry = github_check_repo(repo, token=candidate["token"], timeout=timeout)
            if retry.get("status") == "connected":
                label = candidate.get("label") or candidate.get("owner") or "通用令牌"
                retry["status_message"] = f"首选令牌无权访问该仓库，已自动改用「{label}」"
                return retry
    return result


def list_branches(repo, git_mode="github", auth_info=None, timeout=30):
    info = auth_info or {}
    if git_mode == GIT_MODE_GITLAB:
        if not info.get("gitlab_enabled", True):
            return {
                "repo": repo,
                "status": "disabled",
                "status_message": "GitLab 集成已在全局设置中停用",
                "branches": [],
            }
        return gitlab_list_branches(
            repo, server=_gitlab_server(info), token=info.get("gitlab_token", ""), timeout=timeout
        )
    if not info.get("github_enabled", True):
        return {
            "repo": repo,
            "status": "disabled",
            "status_message": "GitHub 集成已在全局设置中停用",
            "branches": [],
        }
    return github_list_branches(repo, token=github_token_for(info, repo), timeout=timeout)


def weekly_commits(repo, since, until, branches=None, git_mode="github", auth_info=None, timeout=30):
    info = auth_info or {}
    if git_mode == GIT_MODE_GITLAB:
        if not info.get("gitlab_enabled", True):
            return {
                "repo": repo,
                "branches": branches or ["main"],
                "resolved_branches": [],
                "status": "disabled",
                "status_message": "GitLab 集成已在全局设置中停用，本周 commits 不可用",
                "commits": [],
            }
        return gitlab_weekly_commits(
            repo,
            since,
            until,
            branches,
            server=_gitlab_server(info),
            token=info.get("gitlab_token", ""),
            timeout=timeout,
        )
    if not info.get("github_enabled", True):
        return {
            "repo": repo,
            "branches": branches or ["main"],
            "resolved_branches": [],
            "status": "disabled",
            "status_message": "GitHub 集成已在全局设置中停用，本周 commits 不可用",
            "commits": [],
        }
    return github_weekly_commits(
        repo, since, until, branches, token=github_token_for(info, repo), timeout=timeout
    )


def refresh_repo(conn, repo_id):
    repo_row = conn.execute(
        """
        SELECT r.*, p.user_id AS owner_user_id
        FROM github_repos r JOIN projects p ON p.id = r.project_id
        WHERE r.id = ?
        """,
        (repo_id,),
    ).fetchone()
    auth_info = git_auth_for_user(conn, repo_row["owner_user_id"])
    result = check_repo(repo_row["repo"], repo_row["git_mode"], auth_info=auth_info)
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
