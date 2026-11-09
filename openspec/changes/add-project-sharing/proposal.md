## Why

Projects are strictly single-owner today, but real work is collaborative: a project owner needs to let teammates read the weekly reports, contribute materials and weekly updates, or help manage repositories and settings — without handing over ownership or exposing anyone else's projects.

## What Changes

- Add a `project-sharing` capability: a project's owner can grant other accounts per-project roles — 只读 (read), 读写 (write), 管理 (manage) — stored in a new `project_shares` table (unique per project+user, cascade on user/project delete).
- Role hierarchy `owner > manage > write > read`. Read views the whole workspace and exports PDFs; write additionally contributes materials (upload/manual/summary), weekly updates, plan edits, current-week report edits, generation triggers, and TODO archiving into the project; manage additionally changes project settings/schedules/status, manages Git repositories, and deletes materials. Risk status changes follow write. Only the owner grants, changes, or revokes shares.
- Unknown or unshared projects keep answering 404 (existence masking); insufficient roles answer 403 with a Chinese message.
- `GET /api/state` now also lists shared projects with `role` and `shared_by`; `workspace` payloads carry `role`; the id-addressed CLI material/report lookups, hybrid search scope, and task-queue visibility extend to accessible (owned ∪ shared) projects.
- New owner-only share management API: `GET/PUT/DELETE /api/projects/{id}/shares` with upsert-by-username; sharing to the owner themself or to a disabled account is rejected.
- UI: shared projects show a 「共享 · 角色」 badge in the sidebar and an owner/permission hint in the top bar; the workspace hides controls above the viewer's role and renders settings read-only (disabled inputs never fire autosave); settings gain a 共享 sub-tab (owner only) for member management; the close-TODO archive dropdown lists writable projects only.
- Project generation runs exclusively through the internal agent and stays local-only; sharing adds no remote runners, external identity providers, or additional LLM providers.

## Capabilities

### New Capabilities

- `project-sharing`: Owner-granted per-project collaborator roles (read/write/manage) with share management, role-checked project APIs, and shared scope in state, search, and queue visibility.

### Modified Capabilities

- `project-settings`: the first-release "personal single-user workspace, no role-based collaboration" requirement is superseded — projects still have exactly one owner, but the owner can now grant per-project collaborator roles.

## Impact

- Code: `reports_app/db.py` (`project_shares` table), `reports_app/sharing.py` (new), `reports_app/server.py` (role checks on every project route, share routes, `/api/state`), `reports_app/todos.py`, `reports_app/search_index.py`, `reports_app/task_queue.py`, `static/app.js`, `static/styles.css`, `static/index.html`.
- Platform-only change: bumps `APP_VERSION`; no CLI/PyPI release (the CLI keeps working unchanged — shared projects simply appear in `project list` and role-denied writes surface the 403 message).
- Per-user data isolation stays intact otherwise: shares only widen access to one project, admins gain no automatic access to others' projects, and every other account's data remains invisible.
