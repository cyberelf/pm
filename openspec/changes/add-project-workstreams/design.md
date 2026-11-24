## Context

Projects already hold materials, a plan (objectives + milestone JSON), weekly supplements, weekly reports and deterministic risk warnings. TODOs are personal and cross-project: a TODO gets a project only when it is closed and archived as a manual material. Report generation, material summaries and template design run through the internal agent; long tasks run on the shared in-process queue as `generation_jobs` rows.

## Goals / Non-Goals

Goals: make parallel long-running lines visible across weeks with minimal manual tagging; keep one project, one weekly report and one permission boundary.

Non-goals: nested workstreams, per-workstream permissions or sharing, a portfolio layer above projects, per-workstream repositories, Gantt charts.

## Decisions

1. **Flat workstreams inside a project.** `workstreams(project_id, name UNIQUE per project, goal, owner_label, status, target_date, position)`. A second level of hierarchy would duplicate the project concept; a portfolio layer would split evidence and sharing.
2. **Link tables with one primary.** `material_workstreams` / `todo_workstreams` (`item, workstream_id, is_primary, source auto|manual`), FK-cascaded on both sides, partial unique index on `(item) WHERE is_primary = 1`. Reassigning replaces all links of the item in that project. A material may only link workstreams of its own project. TODO links require write on the workstream's project and are returned only to the TODO's owner.
3. **Milestones stay in the plan JSON** with an optional `workstream_id`; the existing overdue-milestone rule and editor keep working.
4. **Snapshots are structured rows**, not parsed Markdown: `workstream_weekly(workstream_id, week_key, status advanced|steady|blocked, summary, next_step, source generated|backfill|manual)`, unique per workstream and week. They are extracted from the finished report plus each workstream's linked materials of the week by one extra internal-agent call after a successful generation; a failure there never fails the report. Generated risk forecasts stay in report Markdown — snapshots carry progress, not risk forecasts.
5. **Classification piggybacks on the summary call.** When the project has active workstreams, the upload summary prompt lists them and returns `workstream_id` per file; invalid ids are ignored. Explicit request ids win and are stored `manual`. The 「AI 整理」 job (`trigger_type = 'workstreams'`) batch-classifies unassigned materials by summary (40 per call) and backfills snapshots for the last eight report weeks lacking them; it never overwrites manual links or manual snapshots.
6. **Deterministic health.** `done`/`paused` follow status; otherwise `blocked` when the target date has passed or a linked milestone is overdue, `at risk` when `workstream_stale` fires (no linked material created in the current and previous project week, and the workstream is older than that window), else `on track`. Rules write `risk_warnings` with `source_ref = workstream:<id>`. Only `workstream_overdue` feeds the project progress status.
7. **Seeding is deterministic.** 「按目标生成工作线」 splits the project objectives on numbered or bulleted lines; the name is the line up to the first comma/colon (max 30 chars), the goal is the whole line; existing names are skipped.
8. **Non-report jobs are excluded from report bookkeeping.** `latest_success`, the workspace `jobs` list and the per-week duplicate guard ignore `template` and `workstreams` jobs.

## Risks / Trade-offs

- Misclassification by the agent → every assignment is one click to change and manual links are never overwritten.
- Extra LLM call per report → small JSON-only prompt with bounded evidence; skipped when the project has no workstreams.
- Stale rule noise for slow lines → paused workstreams are exempt.
