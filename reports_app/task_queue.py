"""Shared background queue for report generation and voice TODO jobs.

Tasks are bounded by a configurable capacity counted as queued + running
(default 5) and dispatched with configurable parallelism (default 2). Both
values live in app_settings so the UI can change them at runtime; environment
variables provide the defaults when no setting is stored. Task state itself
stays in the domain tables (generation_jobs, voice_jobs), so the in-flight
count is derived from the database and survives process restarts.
"""

import os
import sys
import threading
import traceback
from collections import deque

from .config import (
    DEFAULT_QUEUE_CAPACITY,
    DEFAULT_QUEUE_PARALLELISM,
    MAX_QUEUE_CAPACITY,
    MAX_QUEUE_PARALLELISM,
    QUEUE_CAPACITY_ENV_VAR,
    QUEUE_CAPACITY_SETTING,
    QUEUE_PARALLELISM_ENV_VAR,
    QUEUE_PARALLELISM_SETTING,
)
from .db import connect, get_setting
from .reports import run_report_job
from .timeutil import current_week_key, iso_now
from .validation import ValidationError
from .voice_todos import create_voice_job, run_voice_job


class QueueFullError(Exception):
    """Raised when a submission would exceed the configured queue capacity."""


def _bounded_int_setting(conn, setting_key, env_var, default, maximum):
    # Stored setting wins; when it is missing or unparsable the environment
    # variable is the next source, and the built-in default is last.
    for raw in (get_setting(conn, setting_key, ""), os.environ.get(env_var, "")):
        try:
            value = int(str(raw).strip())
        except ValueError:
            continue
        return max(1, min(maximum, value))
    return default


def queue_capacity(conn):
    return _bounded_int_setting(conn, QUEUE_CAPACITY_SETTING, QUEUE_CAPACITY_ENV_VAR, DEFAULT_QUEUE_CAPACITY, MAX_QUEUE_CAPACITY)


def queue_parallelism(conn):
    return _bounded_int_setting(conn, QUEUE_PARALLELISM_SETTING, QUEUE_PARALLELISM_ENV_VAR, DEFAULT_QUEUE_PARALLELISM, MAX_QUEUE_PARALLELISM)


def active_task_count(conn):
    report_jobs = conn.execute(
        "SELECT COUNT(*) AS n FROM generation_jobs WHERE status IN ('queued', 'running')"
    ).fetchone()["n"]
    voice_jobs = conn.execute(
        "SELECT COUNT(*) AS n FROM voice_jobs WHERE status IN ('queued', 'transcribing', 'structuring')"
    ).fetchone()["n"]
    return report_jobs + voice_jobs


_queues = {}
_queues_lock = threading.Lock()


def get_task_queue(db_path):
    """One queue instance per database path so the service and every test
    database each get an isolated dispatcher while all request handlers share
    theirs."""
    key = str(db_path)
    with _queues_lock:
        queue = _queues.get(key)
        if queue is None:
            queue = TaskQueue(key)
            _queues[key] = queue
    return queue


class TaskQueue:
    """FIFO dispatcher that starts a runner thread whenever a parallel slot
    is free. Parallelism is re-read from the database on every dispatch
    decision, so a settings change takes effect without a restart."""

    def __init__(self, db_path):
        self._db_path = db_path
        self._condition = threading.Condition()
        self._pending = deque()
        self._running = 0
        threading.Thread(target=self._dispatch_loop, daemon=True, name="task-queue-dispatcher").start()

    def submit(self, runner, *args):
        with self._condition:
            self._pending.append((runner, args))
            self._condition.notify()

    def _parallelism(self):
        try:
            with connect(self._db_path) as conn:
                return queue_parallelism(conn)
        except Exception:
            print("task queue could not read parallelism; assuming 1", file=sys.stderr, flush=True)
            return 1

    def _dispatch_loop(self):
        while True:
            with self._condition:
                while True:
                    if not self._pending:
                        # submit() notifies; the timeout only guards against a
                        # lost wakeup so the process never keeps the queue idle
                        # with a busy spin.
                        self._condition.wait(timeout=60.0)
                    elif self._running >= self._parallelism():
                        # a slot frees up on _execute's notify; the short
                        # timeout also picks up parallelism raised in settings
                        self._condition.wait(timeout=0.5)
                    else:
                        break
                runner, args = self._pending.popleft()
                self._running += 1
            threading.Thread(target=self._execute, args=(runner, args), daemon=True).start()

    def _execute(self, runner, args):
        try:
            runner(*args)
        except Exception:
            print(f"task queue runner crashed: {traceback.format_exc()}", file=sys.stderr, flush=True)
        finally:
            with self._condition:
                self._running -= 1
                self._condition.notify()


def enqueue_report_generation(conn, db_path, project_id, trigger_type, force=False):
    """Insert a queued generation job and hand it to the shared task queue.

    The duplicate check, capacity check, and job insert run inside one
    immediate transaction so concurrent submissions cannot overshoot the
    capacity. Returns the new job id; raises ValidationError when the same
    project week already has a job queued or running, QueueFullError when the
    queue is at capacity.
    """
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        raise ValidationError("project not found")
    week_key = current_week_key(project["timezone"])
    now = iso_now()
    conn.execute("BEGIN IMMEDIATE")
    try:
        duplicate = conn.execute(
            "SELECT id FROM generation_jobs WHERE project_id = ? AND week_key = ? AND status IN ('queued', 'running')",
            (project_id, week_key),
        ).fetchone()
        if duplicate:
            raise ValidationError("this project already has a generation job queued or running for the current week")
        capacity = queue_capacity(conn)
        if active_task_count(conn) >= capacity:
            raise QueueFullError(f"task queue is full (capacity {capacity})")
        cur = conn.execute(
            """
            INSERT INTO generation_jobs
            (project_id, week_key, trigger_type, provider, status, queued_at, started_at)
            VALUES (?, ?, ?, ?, 'queued', ?, ?)
            """,
            (project_id, week_key, trigger_type, project["report_provider"], now, now),
        )
        job_id = cur.lastrowid
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    get_task_queue(db_path).submit(run_report_job, db_path, job_id, project_id, trigger_type, force)
    return job_id


def enqueue_voice_job(conn, db_path, payload, voice_agent, asr_endpoint, asr_model, asr_language, user_id):
    """Insert a queued voice job and hand it to the shared task queue with the
    same capacity accounting as report generation."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        capacity = queue_capacity(conn)
        if active_task_count(conn) >= capacity:
            raise QueueFullError(f"task queue is full (capacity {capacity})")
        job_id = create_voice_job(conn, user_id)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    get_task_queue(db_path).submit(
        run_voice_job, db_path, job_id, payload, voice_agent, asr_endpoint, asr_model, asr_language
    )
    return job_id


def task_queue_state(conn, user_id=None, is_admin=False):
    """Queue snapshot for the frontend. Tasks stay visible to their owner
    (report tasks through the owning project); queue configuration values are
    included only for administrators."""
    if user_id is None:
        project_filter, params = "", ()
        project_names = {row["id"]: row["name"] for row in conn.execute("SELECT id, name FROM projects")}
        voice_filter = ""
    else:
        project_filter, params = " AND project_id IN (SELECT id FROM projects WHERE user_id = ?)", (user_id,)
        project_names = {
            row["id"]: row["name"]
            for row in conn.execute("SELECT id, name FROM projects WHERE user_id = ?", (user_id,))
        }
        voice_filter = " AND user_id = ?"
    tasks = []
    for row in conn.execute(
        f"""
        SELECT id, project_id, week_key, trigger_type, provider, status, started_at
        FROM generation_jobs
        WHERE status IN ('queued', 'running'){project_filter}
        ORDER BY id
        """,
        params,
    ):
        item = dict(row)
        item["kind"] = "report"
        item["project_name"] = project_names.get(item["project_id"], "")
        tasks.append(item)
    for row in conn.execute(
        f"""
        SELECT id, status, created_at, updated_at
        FROM voice_jobs
        WHERE status IN ('queued', 'transcribing', 'structuring'){voice_filter}
        ORDER BY id
        """,
        params if user_id is None else (user_id,),
    ):
        item = dict(row)
        item["kind"] = "voice"
        tasks.append(item)
    state = {
        "active": len(tasks),
        "tasks": tasks,
    }
    if is_admin:
        state["capacity"] = queue_capacity(conn)
        state["parallelism"] = queue_parallelism(conn)
    return state
