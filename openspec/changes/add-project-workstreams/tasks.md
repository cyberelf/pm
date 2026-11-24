# Tasks

## 1. Data and backend

- [x] 1.1 Tables `workstreams`, `material_workstreams`, `todo_workstreams`, `workstream_weekly` with cascades and the primary-link partial unique indexes
- [x] 1.2 `reports_app/workstreams.py`: CRUD, reorder, seeding from objectives, link replacement for materials and TODOs, snapshot upsert, health, workspace payload
- [x] 1.3 Routes under `/api/projects/{id}/workstreams`, material link route, TODO link route, 「AI 整理」 enqueue; role checks
- [x] 1.4 Deterministic `workstream_stale` / `workstream_overdue` rules; overdue feeds progress status
- [x] 1.5 Exclude non-report jobs (`template`, `workstreams`) from report bookkeeping

## 2. Agent

- [x] 2.1 Upload summary prompt returns a workstream per file; explicit ids win
- [x] 2.2 Snapshot extraction after report generation; failures never fail the report
- [x] 2.3 「AI 整理」 job: batch classification of unassigned materials and snapshot backfill for up to eight archived weeks
- [x] 2.4 Report evidence and instruction organise progress by workstream

## 3. Operations

- [x] 3.1 `workstream_list`, `workstream_show` (agent, read-only); `materials_add --workstream`; workstream column in `materials_list`

## 4. Frontend

- [x] 4.1 工作线 tab: matrix, detail panel, create/edit/delete/reorder, 从目标生成, AI 整理 with queue progress
- [x] 4.2 Sources filter by workstream, assignment dialog, filtered uploads and manual materials
- [x] 4.3 TODO card workstream chip and assignment; close dialog defaults to the workstream's project
- [x] 4.4 Plan milestone workstream select

## 5. Verification

- [x] 5.1 Unit and API tests for links, isolation, rules, snapshots, classification, operations and frontend wiring
- [x] 5.2 Run tests and OpenSpec validation, reinstall the service and verify the new endpoints live

Validation (2026-11-23): all 257 unit tests (11 workstream backend tests, 2 workstream frontend tests) and `node --check` passed; OpenSpec validation passed with only long-requirement warnings. On a throwaway server against a snapshot of the live database (offline provider, no scheduler), seeding agent guard's objectives created 5 workstreams, 「AI 整理」 classified and backfilled 7 weeks, and headless Chrome exercised the matrix, detail panel, manual snapshot, milestone select, material and TODO assignment, the close-dialog default and deletion at desktop and phone widths with no page errors. The snapshot and session were deleted afterwards.
Live check (2026-11-23, platform 1.3.21, real provider, service temporarily bound to 127.0.0.1 because the VPN address times out from this host): on a temporary project, seeding created 2 workstreams, an uploaded note was classified to 东风交付 in the summary call (5s), an explicit manual material stayed manual, `/api/ops/workstream_list` answered, the generated report had one sub-heading per workstream, snapshot extraction wrote advanced snapshots with next steps while keeping a manual one, and 「AI 整理」 succeeded. It also showed the job was marked successful before its snapshots existed, so the job now stays running until extraction finishes. The temporary project, uploads and session were removed and the 10.200.200.3 binding restored.

## 6. Locked weeks, tracking items and progress view

- [x] 6.1 Lock past weeks for snapshots; the first 「AI 整理」 initialises history once, later runs only classify and refresh the current week; report refresh skips past weeks
- [x] 6.2 `workstream_items` (待跟踪项) with CRUD API, agent follow-ups from current-week evidence (dedupe, close only agent items), open items in report evidence and `workstream_show`
- [x] 6.3 Overdue open items mark health 有风险 and raise the medium `workstream_item_overdue` warning
- [x] 6.4 进展 view (default) with summary strip and week lanes, milestone/target/today markers and item completion; 周矩阵 kept as the second view; items section in the detail panel

## 7. Sub-workstreams and plan/risks in the workstream tab

- [x] 7.1 `workstreams.parent_id` (two levels at most, names unique per project), tree order, parent validation, children promoted on delete, nested seeding from indented / `1.1` objective lines
- [x] 7.2 Parent health rolls up active children (`child_alerts`), staleness counts children's material; warnings stay per line
- [x] 7.3 Agent prompts carry the hierarchy (classify to the most specific line; parent snapshots see children's material, follow-ups stay on the child); report evidence carries parent and milestones per workstream
- [x] 7.4 Milestones with stable ids (`reports_app/plans.py`), workstream milestone CRUD API, `project_milestones` plan saves; `overdue_milestone` no longer duplicates `workstream_overdue`
- [x] 7.5 UI: 计划和风险 tab removed; 风险提醒 and 项目计划 panels in 工作线; nested, foldable lanes and matrix rows; sub-workstreams and editable milestones in the detail panel; 上级工作线 in the dialog; parent filters include children
- [x] 7.6 `workstream_list` shows the tree, `workstream_show` lists sub-workstreams and milestones

## 8. PR / issue activity

- [x] 8.1 `workstream_git_items` and `github_repos.workstream_id`; sync of this week's PRs/MRs and issues in 「AI 整理」 (fetch before writes) and from the report's extras
- [x] 8.2 Link order manual > earlier agent > repository default > agent classification; manual link and repository default APIs
- [x] 8.3 PR/issue evidence in snapshot prompts, staleness counts linked activity, report extras tagged with the workstream
- [x] 8.4 UI: PR / Issue list and 改归属 in the detail, 本周未归类 PR/Issue, lane and matrix counts, PR/Issue 归属 per repository; `workstream_show` / `workstream_list` include them
- [x] 8.5 Detail shows linked materials and PRs/issues as icon chips (shape = type, color = status) with hover / tap cards
