## 1. Domain Model and Storage

- [x] 1.1 Define persistence models for personal projects with one owner, project settings, report templates, update schedules, source materials, GitHub repository links, project plans, milestones, deliverables, weekly progress updates, weekly reports, generation jobs, and risk warnings
- [x] 1.2 Add validation for required project fields, schedule weekday/time/timezone values, supported report providers, GitHub repository link format, and local `gh` availability/authentication status
- [x] 1.3 Add storage support for uploaded Markdown, plain text, and PDF project materials, file metadata, extraction status, and source context references
- [x] 1.4 Add plan history or version metadata needed to compare generated reports against the plan baseline used at generation time
- [x] 1.5 Ensure the initial schema does not require organizations, team members, roles, or shared project permissions
- [x] 1.6 Document and enforce first-release assumptions that the backend runs locally with access to workspace storage, local temporary files, `gh`, Codex CLI, and Claude Code CLI

## 2. Project Settings and Source Inputs

- [x] 2.1 Implement personal project creation and project workspace entry flow with the current workspace user as project owner
- [x] 2.2 Implement project settings editing for metadata, report provider, system prompt, project-specific report template, and weekly update schedule
- [x] 2.3 Implement manual project context fields for background, objectives, and constraints
- [x] 2.4 Implement project material upload for Markdown, plain text, and PDF, with unsupported file rejection, metadata display, and extraction status display
- [x] 2.5 Implement GitHub repository association management through local `gh` with connected, disconnected, unauthenticated, and inaccessible statuses

## 3. Project Planning

- [x] 3.1 Implement project plan editing for objectives, milestones, deliverables, optional free-text owner labels, target dates, and statuses
- [x] 3.2 ~~Implement weekly planned outcome creation and editing per project week~~ (removed: weekly planned outcomes feature dropped)
- [x] 3.3 Render the current project plan in the project workspace with milestone and deliverable status and free-text owner labels
- [x] 3.4 Record plan change timestamps or versions when plan content changes after report generation

## 4. Weekly Updates and Scheduling

- [x] 4.1 Implement weekly progress update capture for completed work, in-progress work, blockers, risks, and next steps
- [x] 4.2 Mark a project week as having changed input when manual weekly updates are created or edited
- [x] 4.3 Implement timezone-aware schedule evaluation and ISO project-week calculation using Monday-through-Sunday boundaries in the project timezone
- [x] 4.4 Implement change detection across manual updates, uploaded material changes, and GitHub activity since the last successful generation
- [x] 4.5 Skip duplicate generation when a scheduled update time occurs without relevant changed inputs
- [x] 4.6 Ensure multiple update times in the same project week target the same canonical weekly report identity
- [x] 4.7 Implement manual immediate report generation that can force a job even when no changed input is detected

## 5. GitHub Activity Ingestion

- [x] 5.1 Implement GitHub activity retrieval for associated repositories using the local authenticated GitHub CLI (`gh`)
- [x] 5.2 Store repository activity summaries and last-checked timestamps per project repository link
- [x] 5.3 Support scheduled polling through local `gh` so GitHub activity can trigger weekly report regeneration checks
- [x] 5.4 Surface missing `gh`, unauthenticated `gh`, inaccessible repository, and GitHub ingestion errors without blocking manual project reporting

## 6. Report Generation

- [x] 6.1 Implement report context snapshot assembly from project metadata, plan baseline, manual updates, Markdown/plain-text/PDF/HTML material summaries and extraction statuses, GitHub activity summaries, previous current-week report, a fixed system prompt, and effective report template
- [x] 6.2 Implement the default Markdown weekly report template with sections for this week's summary, completed work, in-progress work, blockers and risks, risk forecast, next week plan, GitHub activity summary, and source/input references
- [x] 6.3 Implement a report provider adapter interface for CLI-based generation using temporary input and output files
- [x] 6.4 Implement the Codex CLI provider adapter with temporary working directory setup, context file input, Markdown output file reading, timeout handling, and failure reporting
- [x] 6.5 Implement the Claude Code CLI provider adapter with temporary working directory setup, context file input, Markdown output file reading, timeout handling, and failure reporting
- [x] 6.6 Implement report generation job lifecycle states, trigger type, timestamps, provider metadata, input snapshot identity, output storage, and diagnostics
- [x] 6.7 Update the canonical project-week report only after a generation job succeeds
- [x] 6.8 Preserve the previous successful project-week report when regeneration fails
- [x] 6.9 Preserve generation job history while exposing only the latest successful report as the visible project-week report
- [x] 6.10 Implement generation history data access that exposes run metadata and diagnostics without showing old report bodies by default
- [x] 6.11 Fail generation jobs when the CLI exits successfully but the expected Markdown output file is missing or empty

## 7. Report Rendering

- [x] 7.1 Store generated weekly report content as Markdown by default
- [x] 7.2 Render the canonical weekly report on the project report page
- [x] 7.3 Sanitize Markdown output and disable unsafe raw HTML execution
- [x] 7.4 Display generation status, last generated time, and failed regeneration diagnostics in the report UI
- [x] 7.5 Display a generation history panel with trigger type, run timestamp, provider, status, failure reason, and input snapshot identity or covered time range
- [x] 7.6 Add a manual generate/regenerate action for the current project-week report
- [x] 7.7 Add server-side cached PDF export for current and historical weekly reports

## 8. Progress and Risk Tracking

- [x] 8.1 Implement progress status calculation for on track, at risk, blocked, and complete states
- [x] 8.2 Implement missing update risk warnings after configured update times pass without current-period input or activity
- [x] 8.3 Implement overdue milestone risk warnings (blocked weekly outcome warnings removed with the outcomes feature)
- [x] 8.4 Display unavailable local `gh`, inaccessible GitHub repositories, material extraction failures, and report generation failures as diagnostics rather than project risk warnings
- [x] 8.5 Keep generated report risk forecasts as Markdown report content separate from deterministic system risk warning records
- [x] 8.6 Ensure the first-release risk UI does not provide promotion from generated report risk forecasts into system warnings
- [x] 8.7 Implement risk warning lifecycle actions for create, update, resolve, and dismiss
- [x] 8.8 Render current progress status and active risk warnings in the project workspace

## 9. Tests and Verification

- [x] 9.1 Add tests for project settings validation, schedule validation, default and project-specific report template selection, supported material type validation, extraction failure handling, and report provider selection
- [x] 9.2 Add tests for ISO project-week boundaries, weekly update change detection, manual forced generation, local `gh` disconnected states, and duplicate generation skipping
- [x] 9.3 Add tests for current-week report overwrite, generation history visibility, hidden old report bodies by default, and preservation on failed regeneration
- [x] 9.4 Add tests for CLI provider timeout, missing output file, temporary file handoff, and failure states
- [x] 9.5 Add tests for Markdown sanitization
- [x] 9.6 Add tests for PDF export HTML sanitization, progress status, deterministic risk warning rules, source/generation diagnostic separation, no promotion action for generated report risk forecasts, and separation of generated report risk forecasts from system warnings
- [x] 9.7 Run OpenSpec validation and the project test suite before marking the change complete
- [x] 9.8 Verify local runtime setup documentation covers required CLIs, local workspace storage, and the remote deployment non-goal

## 10. Multi-file PDF Materials and Summaries

- [x] 10.1 Implement local PDF text extraction while preserving original upload filenames
- [x] 10.2 Implement one-request multi-file upload and explicit upload/summary loading state
- [x] 10.3 Generate per-file AI summaries from original filenames and leading extracted text with a non-blocking fallback
- [x] 10.4 Add editable persisted file summaries to the workspace and report context
- [x] 10.5 Add regression tests and run the required project and OpenSpec validation
- [x] 10.6 Hide failed uploaded-file records from the normal material list while retaining diagnostics
- [x] 10.7 Add a scoped material-detail API for uploaded and manually entered content
- [x] 10.8 Add and verify a shared read-only material preview modal
- [x] 10.9 Render Markdown, plain-text, and original PDF materials by type in the shared read-only preview modal
- [x] 10.10 Add project-scoped deletion for current-week unlocked materials and local uploaded-file cleanup
- [x] 10.11 Add delete controls and regression tests for unlocked and locked material behavior

## 11. Personal TODO Board

- [x] 11.1 Add TODO persistence and validation for open status transitions and optional close reasons
- [x] 11.2 Add TODO APIs with atomic optional project-material archiving on closure
- [x] 11.3 Add a separate responsive Trello-style board and top-right TODO/weekly-report switch
- [x] 11.4 Add backend and frontend regression tests and run required verification
- [x] 11.5 Return sanitized Markdown rendering for TODO card content and preserve raw source for editing
- [x] 11.6 Replace action-row mode buttons with a standalone book-page workspace switch and distinct TODO surface
- [x] 11.7 Keep all three board columns visible and add draft/existing-card inline auto-save editing
- [x] 11.8 Add regressions, restart the local LaunchAgent, and verify the live TODO route and page assets
- [x] 11.9 Move manual report generation to a confirmed project-row icon and remove page-level generation and schedule-check actions
- [x] 11.10 Replace the book control with an accessible animated folded corner that shows current and destination pages
- [x] 11.11 Update regressions, restart the local service, and verify live assets and routes
- [x] 11.12 Replace native report-generation confirmation with an application-styled message box
- [x] 11.13 Restyle the workspace switch as a borderless soft-shadow paper curl and apply blue/green/gray board column themes
- [x] 11.14 Update regressions, restart the local service, and verify live assets and routes

## 10. Workspace navigation restructure

- [x] 10.1 Rework the workspace navigation to 总览 / 过程资料 / 本周补充 / 周报 / 计划和风险 / 设置 with the 设置 tab promoted to a first-level navigation button
- [x] 10.2 Move manual materials before file uploads in the 过程资料 tab and split 计划和风险 into 项目计划 and 进度风险 sub-tabs
- [x] 10.3 Move 系统诊断 into the 设置 tab as its own sub-tab and remove the standalone risks tab

## 11. Supplement history

- [x] 11.1 Snapshot the current week's supplement into the weekly report row on every successful generation and refresh it on same-week regeneration
- [x] 11.2 Expose the generation-time supplement in archived report payloads and render it under expanded historical reports
- [x] 11.3 List past weeks' supplements (newest first, excluding the current week, bounded) in the 本周补充 tab

## 12. Template design as a queued task

- [x] 12.1 Route AI template design through the shared task queue with duplicate and capacity guards instead of a synchronous request
- [x] 12.2 Save the generated template to the project automatically on task success and record failures on the task
- [x] 12.3 Surface template task progress through the queue snapshot with completion and failure toasts

## 13. Manual current-week report edit

- [ ] 13.1 Track manual edits with `weekly_reports.edited_at` (schema + migration) and clear it when regeneration overwrites the row
- [ ] 13.2 Accept manual Markdown edits for the current week only via PUT /api/projects/{id}/reports/{week_key}, and flag edited projects in /api/state
- [ ] 13.3 Add the 编辑 dialog and 已手工调整 badge to the report panel, and warn in the generate confirmation when the current week report is manually edited

## 14. Optional Git activity fetch switches

- [x] 14.1 Add per-repo fetch switches (PR/MR, issues, milestones) to `github_repos` with an on-demand `GET /api/projects/{id}/repos/{rid}/activity` read bounded to the current project week
- [x] 14.2 Implement GitHub REST pull/issue/milestone readers and a bounded GraphQL read of organization Projects (v2) board items; GitLab merge-request/issue/milestone readers including ancestor group milestones
- [x] 14.3 Deduplicate organization project reads per organization when several repos of the same org enable the switch, and feed extras plus org boards into report evidence only when switched on
- [x] 14.4 Add the 抓取项 checkbox column to the repo table (组织Project shown for GitHub only) with save-on-toggle behavior and regression tests
- [x] 14.5 Add the repository-level Projects (v2) fetch switch (fetch_repo_projects) alongside the organization one via a shared bounded GraphQL selection set; GitLab repos expose no board toggles


## 15. Excel uploads, original download and cold storage

- [x] 15.1 Add bounded XLSX/XLS worksheet extraction and preserve failed originals in the file list
- [x] 15.2 Add original downloads with UTF-8 attachment names and existing project read permissions
- [x] 15.3 Add admin-only cold-storage configuration, hourly calendar-month transfers and manual scans with status
- [x] 15.4 Verify copies before switching persisted paths, preserve original files on failure and retain access across directory changes
- [x] 15.5 Include cold originals and a restore manifest in full backups; document local and Docker storage behavior
- [x] 15.6 Run regression and OpenSpec checks, restart the service and verify live endpoints and frontend assets

Validation (2026-11-15): `python3 -m unittest` — 208 tests passed; `npx --yes @fission-ai/openspec validate add-weekly-project-management-system` — valid, with pre-existing duplicate task ID warnings; `node --check static/app.js` and `git diff --check` passed. A temporary account on the LaunchAgent service verified XLSX upload, extracted preview, byte-identical download, cold-storage configuration, and fresh browser controls. Temporary data was removed. Service binding was temporarily changed to 127.0.0.1 for verification because the configured VPN address timed out; the original 10.200.200.3 binding was restored and confirmed listening.

## 16. Image material uploads

- [x] 16.1 Accept PNG/JPEG/GIF/WebP uploads validated by file signature, storing the sniffed media type and rejecting SVG
- [x] 16.2 Recognise images up to 5 MiB through the internal agent's vision call (OpenAI image_url / Anthropic image blocks) with the admin-only 图片识别模型 and optional OpenAI-compatible 图片识别 API 地址 settings as extracted Markdown; keep failed originals when it is unset or fails
- [x] 16.3 Serve images inline for preview and show the image with its recognised text in the preview dialog
- [x] 16.4 Add regression tests for recognition, spoofed content, oversize images and provider request shapes

## 17. macOS backup permission diagnosis

- [x] 17.1 Record and print the service entry point separately from the framework interpreter so Full Disk Access guidance identifies the correct executable
- [x] 17.2 Preserve the original failure path and errno in backup permission errors; present TCC as a possible cause and show the running interpreter
- [x] 17.3 Cover generated service commands and permission diagnostics with regression tests

Validation (2026-11-15): The final working tree passed all 213 unit tests. OpenSpec validation passed with existing duplicate-task-ID warnings and a warning on the concurrent image-recognition requirement length. Comparing background probes showed that directly launching Python.app was denied, while /usr/bin/python3 succeeded after its Full Disk Access entry was removed and re-added. The service was restored to that authorized entry point and reinstalled. A one-time LaunchAgent using the same entry point ran the full backup successfully (run 16): 177 uploads, 8,219,305 bytes, zreport-backup-20261115-193622. The copied SQLite database passed PRAGMA quick_check and all 177 upload files were present. The service remains on the original bind address; local HTTP access to that VPN listener still timed out. Concurrent image-upload edits were kept separate from this repair.

## 18. Compressed full backups

- [x] 18.1 Create a ZIP with the consistent database snapshot, uploads and cold originals; publish only completed archives and record compressed size
- [x] 18.2 Retain ZIPs and legacy directories together with numeric collision ordering and preserve unrelated files
- [x] 18.3 Verify archive restoration, cold manifests, compression failures and mixed-format retention; document extraction before restore
- [x] 18.4 Run regression and OpenSpec validation, restart and verify a live compressed backup, push changes and clean temporary environment

Validation (2026-11-15): All 216 unit tests passed; OpenSpec validation passed with the existing duplicate-task-ID and image-requirement-length warnings. The normal LaunchAgent was reinstalled for platform 1.3.13. A one-time LaunchAgent using the same entry point completed and committed backup run 17: zreport-backup-20261115-200211.zip, 222 upload/cold-original files, 11,034,074 compressed bytes (16,338,165 uncompressed bytes). All ZIP CRC checks passed, file counts and cold manifest entries were checked, and the extracted database passed PRAGMA quick_check. The verification LaunchAgent, copied ZIP, restored database, test caches and logs were removed; the backup archive and application data were retained. Local HTTP health checks against the configured VPN listener still timed out, as before this change; backup API behavior was covered by the HTTP regression tests.

## 19. Horizontal global settings tabs

- [x] 19.1 Show one global settings panel at a time using horizontal tabs and preserve existing form nodes and save handlers
- [x] 19.2 Filter tabs by account role, fall back from unavailable admin sections and support keyboard navigation
- [x] 19.3 Keep narrow-screen tabs on one horizontally scrollable row; refresh asset cache keys and ZIP backup help text
- [x] 19.4 Complete regression, browser and OpenSpec checks, restart for the platform version bump and push

Validation (2026-11-15): All 216 unit tests, node --check static/app.js and git diff --check passed. OpenSpec validation passed with existing warnings. A fresh isolated Chromium page loaded the actual static HTML/CSS/JS with authentication requests stubbed: all nine admin tabs selected exactly one linked panel, drafts survived switching, keyboard End/Right navigation worked, and regular-account fallback exposed only appearance/Git/password. Desktop rendering was inspected at 1440px; mobile emulation at 390px kept the 358px tab strip on one scrollable row with 863px of content and no page overflow. The platform version was bumped to 1.3.14 and the normal LaunchAgent reinstalled. The isolated page and temporary fixture, screenshots, test caches and logs were removed.

## 20. Weekly report assistant Q&A

- [x] 20.1 Store per-account, per-project-week assistant conversations and expose ask, list, clear and apply endpoints with read/write role checks
- [x] 20.2 Answer through the internal agent with multi-turn history, the current report, cached bounded evidence, recent historical reports and active risk warnings
- [x] 20.3 Parse marked revised reports, keep them unapplied until a writer confirms, and carry the latest unapplied revision into follow-up adjustments
- [x] 20.4 Add the docked 助手问答 side panel with suggestions, loading states, revision preview and apply confirmation; cover backend and frontend behavior with tests

Validation (2026-11-21): All 226 unit tests, node --check static/app.js and git diff --check passed; OpenSpec validation passed with only the existing duplicate-task-ID and image-requirement-length warnings. An isolated fake-provider instance was exercised in headless Chromium at 1440px (light and dark) and 390px: suggestion question, adjustment proposal, apply confirmation, 已手工调整 badge and clear all worked with no page errors. The topbar toggle was moved into the project heading because the page-corner hit area covers the topbar's right edge. The LaunchAgent was reinstalled for platform 1.3.15; over the HTTPS listener the live assistant answered a real-LLM question with cited materials and PRs in about 45s, a follow-up resolved its reference from history in about 4s via the evidence cache, and the verification session and messages were removed. Plain HTTP on the VPN listener still times out locally, as before.

## 21. On-demand assistant tools

- [x] 21.1 Replace upfront evidence assembly with the current report plus a local inventory in the assistant prompt
- [x] 21.2 Add project-scoped, bounded read-only tools mirroring the zreport CLI read commands plus plan, supplement, risks, materials list and Git repos/commits/activity, with a ten-minute Git cache
- [x] 21.3 Run an OpenAI/Anthropic tool-calling loop in the internal agent with a forced final answer after six rounds; record and show the consulted tools per answer
- [x] 21.4 Cover tool scoping, truncation, errors, caching and both provider loop formats with tests; verify against the live provider

Validation (2026-11-21): All 230 unit tests and node --check passed; OpenSpec validation passed with only the existing warnings. Platform 1.3.16 was reinstalled and verified over HTTPS against the live Anthropic-compatible provider: questions answerable from the current report returned in 5–10s with no tool calls (previously about 45s for the first question); a history comparison called only weekly_show (17s), a material quote called search then material_show (21s), and a latest-commits question called git_commits for one repository (2.2s inside a 15s answer). The verification session and its messages were removed.

## 22. Shared operation registry

- [x] 22.1 Define project, material, report, TODO, search and Git operations once (MCP-style schema, read-only annotation, CLI path, render hint, handler) with project resolution by ID or name and per-operation roles
- [x] 22.2 Publish GET /api/ops and POST /api/ops/<name>; keep existing REST routes for the web UI and older CLI clients
- [x] 22.3 Rebuild the zreport CLI on the discovered manifest with a per-server cache, generic table/record/text/message rendering and stdin/file parameters; keep login/logout/whoami/skill native; bump CLI to 1.6.0
- [x] 22.4 Replace the assistant's hand-written tools with the read-only agent operations bound to the conversation's project
- [x] 22.5 Cover registry invariants, HTTP roles, agent binding, cross-interface parity and CLI cache fallback with tests; keep the existing CLI end-to-end tests passing unchanged

Validation (2026-11-21): All 236 unit tests (including the unchanged CLI end-to-end suite), node --check and git diff --check passed; OpenSpec validation passed with only the existing warnings. Platform 1.3.17 was reinstalled: GET /api/ops published 19 operations; the manifest-driven CLI listed projects, weekly reports, risks, repositories, search hits and 95 ai-defenders commits (3.3s) against the live service; the assistant answered a supplement-and-history question by calling supplement_show and weekly_show in one round (14s). Verification sessions and messages were removed. CLI 1.6.0 is not yet tagged for PyPI.

## 23. Streaming assistant with concurrent tools

- [x] 23.1 Stream both providers (OpenAI tool-call deltas, Anthropic messages.stream) with round/text events and cooperative cancellation
- [x] 23.2 Run the tool calls of one round concurrently on per-call database connections and emit tool_start/tool_end
- [x] 23.3 Answer questions as background runs with ordered event ids, an SSE endpoint resumable via Last-Event-ID, cancel, one active run per account and project, and reattachment after reload
- [x] 23.4 Render live tool chips, streamed text with the revision block hidden, and a stop button in the panel; restore stopped or failed questions to the input
- [x] 23.5 Cover streaming formats, concurrency, resume, busy/cancel/error runs and the EventSource UI with tests; verify in a browser and against the live provider

Validation (2026-11-21): All 241 unit tests and node --check passed; OpenSpec validation passed with only the existing warnings. In headless Chromium against an isolated fake-provider instance, tool chips ran live, text streamed with the revision block hidden behind a progress note, a mid-answer reload reattached and completed, and stop restored the question without storing a turn. Platform 1.3.18 was reinstalled; on the live Anthropic-compatible provider one question started weekly_show and repos_commits together in the first round (1 ms and 4.6 s), then streamed 460 text deltas to completion at 35 s. The verification session and messages were removed.

## 24. Assistant work log

- [x] 24.1 Record thinking segments, tool calls (with result excerpts) and interim text with run-relative timestamps and durations; store the log with each answer and read older tool-only traces
- [x] 24.2 Render the log T3 Code-style: raw tool calls, live shimmer and ticking timers, durations, failure marks, expandable input/result, folded summary on stored answers; disable the input while a thread loads

Validation (2026-11-21): All 242 unit tests and node --check passed; OpenSpec validation passed with only the existing warnings. Platform 1.3.19 was reinstalled. In headless Chromium against the live service and provider, one question showed 思考中 at 0.4s, then 思考 7.5s and four parallel tool rows (weekly_show 3ms, supplement_show 3ms, materials_list 12ms, repos_commits ticking to 4.1s), a second 思考 19s segment and the streamed answer, stored as 已工作 36s · 4 次工具调用. The verification messages and session were removed; the account's existing conversation was left untouched.

## 25. Word material uploads

- [x] 25.1 Accept `.docx` and `.doc` uploads; extract DOCX body text through stdlib ZIP/XML (headings, lists, tables, content controls; DTDs refused) and DOC text through a stdlib OLE compound-file reader and the Word 97 piece table
- [x] 25.2 Bound extraction to 2000000 characters and 64 MiB DOCX expanded data; mark encrypted, Word 6/95, empty and corrupt documents failed while keeping originals
- [x] 25.3 Add regression tests with a hand-built DOCX and a DOC fixture, and list Word in the upload picker

Validation (2026-11-23): All 244 unit tests and node --check passed; OpenSpec validation passed with only the existing warnings. Platform 1.3.20 was reinstalled. Because the configured VPN address timed out from this host, the service was temporarily bound to 127.0.0.1: a temporary project received a textutil-generated `.doc` and `.docx`, both extracted (Chinese, accented Latin, tables) with summaries generated, and the served upload picker listed `.docx,.doc`. The temporary project, uploads and session were removed and the 10.200.200.3 binding was restored and confirmed listening.

## 26. Uploads off the write lock

- [x] 26.1 Run image recognition and the batched summary/workstream model call before any database write, then insert the material rows with their summaries and links in one short transaction, so the scheduler and other requests never wait on the model
- [x] 26.2 Remove the batch's stored files when any upload in it fails, and give SQLite connections a 15 s busy timeout
- [x] 26.3 Add a regression test where a second connection writes with no busy wait while the model calls are running

## 27. Plan and risks moved into 工作线

- [x] 27.1 Remove the 计划和风险 tab; the 工作线 tab carries the 风险提醒 and 项目计划 panels and each workstream edits its own milestones (see `add-project-workstreams` §7)

## 28. Workstream PR / issue sync

- [x] 28.1 Sync this week's PR / issue activity into workstreams (see `add-project-workstreams` §8)

## 29. 项目计划 tab restored

- [x] 29.1 Move the project plan back to its own 项目计划 tab after 周报; risks stay in 工作线 (see `add-project-workstreams` §9)
