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
