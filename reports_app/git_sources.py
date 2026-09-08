"""Dispatch repository reads to the REST client for the configured git host.

Per-user credentials and the global GitHub/GitLab switches travel together
in an auth_info dict built by git_auth_for_user(); report generation looks
the credentials up through the owning project's user, so background jobs
work without a request context.
"""

from .config import (
    GIT_MODE_GITLAB,
    GITHUB_ENABLED_SETTING,
    GITHUB_TOKEN_SETTING,
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


def git_auth_for_user(conn, user_id):
    return {
        "github_token": get_user_setting(conn, user_id, GITHUB_TOKEN_SETTING),
        "gitlab_token": get_user_setting(conn, user_id, GITLAB_TOKEN_SETTING),
        "gitlab_url": get_user_setting(conn, user_id, GITLAB_URL_SETTING),
        "github_enabled": get_setting(conn, GITHUB_ENABLED_SETTING, "1") != "0",
        "gitlab_enabled": get_setting(conn, GITLAB_ENABLED_SETTING, "1") != "0",
    }


def _gitlab_server(gitlab_server, info):
    """A repo's own server address wins; the account's GitLab URL is the
    fallback so self-hosted users only configure it once."""
    return (gitlab_server or "").strip() or (info.get("gitlab_url") or "").strip()


def _disabled_result(message):
    return {
        "status": "disabled",
        "status_message": message,
        "activity_summary": "",
        "last_activity_at": None,
    }


def check_repo(repo, git_mode="github", gitlab_server="", auth_info=None, timeout=20):
    info = auth_info or {}
    if git_mode == GIT_MODE_GITLAB:
        if not info.get("gitlab_enabled", True):
            return _disabled_result("GitLab 集成已在全局设置中停用，无法读取该仓库")
        return gitlab_check_repo(
            repo, server=_gitlab_server(gitlab_server, info), token=info.get("gitlab_token", ""), timeout=timeout
        )
    if not info.get("github_enabled", True):
        return _disabled_result("GitHub 集成已在全局设置中停用，无法读取该仓库")
    return github_check_repo(repo, token=info.get("github_token", ""), timeout=timeout)


def list_branches(repo, git_mode="github", gitlab_server="", auth_info=None, timeout=30):
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
            repo, server=_gitlab_server(gitlab_server, info), token=info.get("gitlab_token", ""), timeout=timeout
        )
    if not info.get("github_enabled", True):
        return {
            "repo": repo,
            "status": "disabled",
            "status_message": "GitHub 集成已在全局设置中停用",
            "branches": [],
        }
    return github_list_branches(repo, token=info.get("github_token", ""), timeout=timeout)


def weekly_commits(repo, since, until, branches=None, git_mode="github", gitlab_server="", auth_info=None, timeout=30):
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
            server=_gitlab_server(gitlab_server, info),
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
        repo, since, until, branches, token=info.get("github_token", ""), timeout=timeout
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
    result = check_repo(repo_row["repo"], repo_row["git_mode"], repo_row["gitlab_server"], auth_info=auth_info)
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
