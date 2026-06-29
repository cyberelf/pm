import json
import shutil
import subprocess
from urllib.parse import quote

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
        ["gh", "repo", "view", repo, "--json", "nameWithOwner,pushedAt,description"],
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


def weekly_commits(repo, since, until, timeout=30):
    if not shutil.which("gh"):
        return {
            "repo": repo,
            "status": "disconnected",
            "status_message": "local GitHub CLI (`gh`) is missing",
            "commits": [],
        }
    since_q = quote(since.isoformat().replace("+00:00", "Z"), safe="")
    until_q = quote(until.isoformat().replace("+00:00", "Z"), safe="")
    endpoint = f"repos/{repo}/commits?since={since_q}&until={until_q}&per_page=100"
    cmd = ["gh", "api", "--method", "GET", endpoint]
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    if result.returncode != 0:
        return {
            "repo": repo,
            "status": "failed",
            "status_message": (result.stderr or result.stdout or "failed to read commits").strip(),
            "commits": [],
        }
    try:
        data = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        return {
            "repo": repo,
            "status": "failed",
            "status_message": f"failed to parse commits: {exc}",
            "commits": [],
        }
    commits = []
    for item in data[:100]:
        commit = item.get("commit") or {}
        author = commit.get("author") or {}
        commits.append(
            {
                "sha": (item.get("sha") or "")[:12],
                "message": (commit.get("message") or "").splitlines()[0],
                "author": author.get("name") or "",
                "date": author.get("date") or "",
                "url": item.get("html_url") or "",
            }
        )
    return {
        "repo": repo,
        "status": "ok",
        "status_message": f"{len(commits)} commits in current project week",
        "commits": commits,
    }
