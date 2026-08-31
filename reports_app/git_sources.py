"""Dispatch repository reads to the local CLI that owns the configured git host."""

from .config import GIT_MODE_GITLAB
from .gitlab import check_repo as gitlab_check_repo
from .gitlab import list_branches as gitlab_list_branches
from .gitlab import weekly_commits as gitlab_weekly_commits
from .github import check_repo as github_check_repo
from .github import list_branches as github_list_branches
from .github import weekly_commits as github_weekly_commits
from .timeutil import iso_now


def check_repo(repo, git_mode="github", gitlab_server="", timeout=20):
    if git_mode == GIT_MODE_GITLAB:
        return gitlab_check_repo(repo, server=gitlab_server, timeout=timeout)
    return github_check_repo(repo, timeout=timeout)


def list_branches(repo, git_mode="github", gitlab_server="", timeout=30):
    if git_mode == GIT_MODE_GITLAB:
        return gitlab_list_branches(repo, server=gitlab_server, timeout=timeout)
    return github_list_branches(repo, timeout=timeout)


def weekly_commits(repo, since, until, branches=None, git_mode="github", gitlab_server="", timeout=30):
    if git_mode == GIT_MODE_GITLAB:
        return gitlab_weekly_commits(repo, since, until, branches, server=gitlab_server, timeout=timeout)
    return github_weekly_commits(repo, since, until, branches, timeout=timeout)


def refresh_repo(conn, repo_id):
    repo_row = conn.execute("SELECT * FROM github_repos WHERE id = ?", (repo_id,)).fetchone()
    result = check_repo(repo_row["repo"], repo_row["git_mode"], repo_row["gitlab_server"])
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
