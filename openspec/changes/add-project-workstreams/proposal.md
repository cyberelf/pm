## Why

Large projects such as "agent guard" run several parallel long-running lines of work (customer delivery, product, partnership, financing, team) inside one project. Everything shares one weekly report and one milestone list, so the per-week view hides the per-line view: answering "how far has financing moved in the last two months" means re-reading every report. Splitting the lines into separate projects would fragment materials, sharing, repositories and the single weekly report the audience reads, and would force a project choice before every upload.

## What Changes

- Add a `project-workstreams` capability: one flat level of 工作线 inside a project (name, goal, owner label, status active/paused/done, target date, order). No nesting, no separate permissions — workstreams follow the project's roles.
- Materials carry one optional primary workstream plus optional related workstreams; the viewer's own TODOs can carry the same links (TODOs stay private to their account). Closing a TODO into a project copies its links of that project onto the archived material.
- Plan milestones gain an optional `workstream_id`.
- Per-workstream weekly snapshots (`workstream_weekly`: status advanced/steady/blocked, one-line progress, next step) are extracted by the internal agent after each successful report generation; a queued 「AI 整理」 job classifies unassigned materials and backfills snapshots from the last eight archived reports.
- Uploaded files are classified to a workstream in the same internal-agent call that writes their summary; an explicit workstream in the request (the active filter in the UI, `--workstream` in the CLI) always wins. Manual reassignment marks the link manual.
- Deterministic rules: `workstream_stale` (an active workstream with no linked material for two project weeks) and `workstream_overdue` (target date passed while not done). Workstream health is derived from status and these rules.
- Report evidence includes the workstreams and each new material's workstream; the agent is instructed to organise progress by workstream and to say explicitly when one had no progress.
- UI: a 工作线 workspace tab with a workstream × week matrix (last eight weeks) and a detail panel (goal, milestones, snapshot timeline, linked materials, my open TODOs); 「从目标生成」 seeds workstreams from numbered plan objectives; the sources tab filters by workstream and assigns via a shared dialog; TODO cards show and edit their workstream; the close-TODO dialog defaults to the workstream's project.
- Operations: read-only `workstream_list` / `workstream_show` (CLI `project workstreams list|show`, assistant tools) and a `workstream` parameter on `materials_add`; `materials_list` shows each material's workstream.

## Capabilities

### New Capabilities

- `project-workstreams`: flat workstreams inside a project with material/TODO/milestone links, weekly snapshots, deterministic health rules, a long-range matrix view, and agent-assisted classification and backfill.

## Impact

- Code: `reports_app/db.py` (tables `workstreams`, `material_workstreams`, `todo_workstreams`, `workstream_weekly`), new `reports_app/workstreams.py`, `reports_app/materials.py` (summary prompt classification), `reports_app/reports.py` (evidence, snapshot extraction, job bookkeeping), `reports_app/risks.py`, `reports_app/todos.py`, `reports_app/task_queue.py`, `reports_app/operations.py`, `reports_app/server.py`, `static/*`.
- Platform-only change: bumps `APP_VERSION`; the CLI discovers the new operations from the manifest, so there is no PyPI release.
- Per-user isolation stays intact: workstream data is project data under existing roles; TODO links are visible only to the TODO's owner.
