## 1. Domain Model and Storage

- [x] 1.1 Define persistence models for personal projects with one owner, project settings, report templates, update schedules, source materials, GitHub repository links, project plans, milestones, deliverables, weekly planned outcomes, weekly progress updates, weekly reports, generation jobs, and risk warnings
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
- [x] 3.2 Implement weekly planned outcome creation and editing per project week
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

- [x] 6.1 Implement report context snapshot assembly from project metadata, plan baseline, weekly planned outcomes, manual updates, Markdown/plain-text/PDF material summaries and extraction statuses, GitHub activity summaries, previous current-week report, project system prompt, and effective report template
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

## 8. Progress and Risk Tracking

- [x] 8.1 Implement progress status calculation for on track, at risk, blocked, and complete states
- [x] 8.2 Implement missing update risk warnings after configured update times pass without current-period input or activity
- [x] 8.3 Implement overdue milestone and blocked weekly outcome risk warnings
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
- [x] 9.6 Add tests for progress status, deterministic risk warning rules, source/generation diagnostic separation, no promotion action for generated report risk forecasts, and separation of generated report risk forecasts from system warnings
- [x] 9.7 Run OpenSpec validation and the project test suite before marking the change complete
- [x] 9.8 Verify local runtime setup documentation covers required CLIs, local workspace storage, and the remote deployment non-goal
