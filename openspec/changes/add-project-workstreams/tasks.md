# Tasks

## 1. Data and backend

- [ ] 1.1 Tables `workstreams`, `material_workstreams`, `todo_workstreams`, `workstream_weekly` with cascades and the primary-link partial unique indexes
- [ ] 1.2 `reports_app/workstreams.py`: CRUD, reorder, seeding from objectives, link replacement for materials and TODOs, snapshot upsert, health, workspace payload
- [ ] 1.3 Routes under `/api/projects/{id}/workstreams`, material link route, TODO link route, 「AI 整理」 enqueue; role checks
- [ ] 1.4 Deterministic `workstream_stale` / `workstream_overdue` rules; overdue feeds progress status
- [ ] 1.5 Exclude non-report jobs (`template`, `workstreams`) from report bookkeeping

## 2. Agent

- [ ] 2.1 Upload summary prompt returns a workstream per file; explicit ids win
- [ ] 2.2 Snapshot extraction after report generation; failures never fail the report
- [ ] 2.3 「AI 整理」 job: batch classification of unassigned materials and snapshot backfill for up to eight archived weeks
- [ ] 2.4 Report evidence and instruction organise progress by workstream

## 3. Operations

- [ ] 3.1 `workstream_list`, `workstream_show` (agent, read-only); `materials_add --workstream`; workstream column in `materials_list`

## 4. Frontend

- [ ] 4.1 工作线 tab: matrix, detail panel, create/edit/delete/reorder, 从目标生成, AI 整理 with queue progress
- [ ] 4.2 Sources filter by workstream, assignment dialog, filtered uploads and manual materials
- [ ] 4.3 TODO card workstream chip and assignment; close dialog defaults to the workstream's project
- [ ] 4.4 Plan milestone workstream select

## 5. Verification

- [ ] 5.1 Unit and API tests for links, isolation, rules, snapshots, classification, operations and frontend wiring
- [ ] 5.2 Run tests and OpenSpec validation, reinstall the service and verify the new endpoints live
