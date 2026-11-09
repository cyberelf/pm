# Tasks

## 1. Backend

- [x] Add `project_shares` table to `reports_app/db.py` (UNIQUE(project_id, user_id), FK cascade both sides, index on user_id)
- [x] New `reports_app/sharing.py`: role constants and ranking (owner > manage > write > read), `project_role`, `require_role` (403 with Chinese messages), `share_rows`/`set_share`/`remove_share`, `ACCESSIBLE_PROJECTS_SQL`
- [x] `/api/projects/{id}/*`: replace the owner-only check with `project_role` (404 masking) plus per-route `require_role` — write for materials add/update, weekly-update, plan, report edit, generate, schedule-check; manage for settings, suggest-template, status, repos CRUD/refresh, material delete; read for all GETs
- [x] Share management routes `GET/PUT/DELETE /api/projects/{id}/shares` (owner-only; upsert by username; reject owner-self, disabled accounts, bad roles)
- [x] `/api/state` returns shared projects with `role` + `shared_by`; `workspace` payload carries `role`
- [x] Risks status change requires write on the risk's project; `close_todo` archive requires write
- [x] Search scope (`search_index.py`) and queue visibility (`task_queue.py`) extend to accessible projects; id-addressed CLI material/report lookups accept shares

## 2. Tests

- [x] `ProjectSharingTest` in `tests/test_core.py`: share management API + guards (bad role, unknown user, owner-self, disabled account, non-owner 403, revoke cuts access), `/api/state` visibility + 404 masking, role permission matrix over the live server, generation/queue visibility and risk dismissal by role, `close_todo` write requirement, search scope grant/revoke

## 3. Frontend

- [x] Role helpers (`projectRoleOf`, `canWriteWorkspace`, `canManageWorkspace`, `isProjectOwner`) and sidebar 「共享 · 角色」 badge; hide generate/settings entries by role
- [x] Top-bar shared-owner hint; settings form disabled (no autosave) below manage; Git tab add-row/notes/branches/flags/actions read-only below manage
- [x] Sources/Updates/Plan/Report render read-only below write; report edit button gated
- [x] Owner-only 共享 sub-tab: member table with inline role select, add-by-username form, remove with confirm, error toasts + reload
- [x] Close-TODO archive dropdown filtered to writable projects; bump static asset versions

## 4. Docs & Release

- [x] Bump `APP_VERSION` in `reports_app/config.py` (platform-only; no git tag, no PyPI release)
- [x] README feature mention (共享一段)
