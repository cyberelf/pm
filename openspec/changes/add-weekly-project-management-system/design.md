## Context

The product is a new local personal project management system focused on weekly work tracking. There is no existing implementation or domain spec in this repository, so this design defines the first application boundaries for projects, plans, weekly reports, source ingestion, generated report jobs, and risk signals.

The first release runs as a local personal web application: the browser provides the UI, and the backend runs on the same machine as workspace data, uploaded files, local `gh`, Codex CLI, and Claude Code CLI. The system must support mixed project context sources: manual project data, uploaded materials, and GitHub activity read through the local authenticated GitHub CLI (`gh`). Each project week is calculated in the project's timezone using ISO week boundaries from Monday through Sunday. Each project week has one canonical Markdown report. One or more configured update times act as refresh checkpoints that may regenerate and overwrite that week's visible report when new relevant inputs arrive.

## Goals / Non-Goals

**Goals:**

- Model projects with settings for schedule, report provider, prompt, uploaded materials, and GitHub repository links.
- Scope the first release to a personal single-user workspace where each project has exactly one owner.
- Run the first release as a local web application whose backend can access the local CLI tools and workspace files.
- Capture project plans so reports and risk checks have a baseline.
- Collect manual weekly updates and source changes into a normalized context package for report generation.
- Read GitHub repository metadata and activity through the local `gh` CLI for the first release.
- Run Codex CLI or Claude Code CLI through a provider abstraction that can be configured per project.
- Use a default Markdown weekly report template when a project does not define its own report template.
- Allow each project to configure its own report template in addition to its system prompt.
- Store generated weekly reports as Markdown and overwrite the current week's report when regeneration is required.
- Allow manual immediate generation or regeneration using the same report context snapshot and overwrite rules as scheduled jobs.
- Show generation job history to the workspace user for audit and troubleshooting, and show prior project-week reports as read-only historical reports.
- Track progress and generate project risk warnings from deterministic rules over plan status, missing updates, and project gaps.
- Show source and generation failures as system diagnostics, not project risks.
- Ask the report provider to include a risk section that can summarize observed risks and forecast likely follow-on risks from the assembled context.
- Provide a workspace-level TODO board that remains separate from project weekly-report views.

**Non-Goals:**

- Building a full issue tracker, chat system, or resource management suite.
- Supporting organization, team, role-based collaboration, shared project membership, or multi-user approval flows.
- Supporting remote server deployment where the browser, backend, CLI tools, and workspace files live on different machines.
- Replacing GitHub issues, pull requests, or repository permissions.
- Guaranteeing report factual accuracy without traceable source inputs.
- Supporting arbitrary report formats beyond Markdown in the initial release.
- Supporting custom per-project week start days in the initial release.
- Promoting agent-generated report risk forecasts into system risk warning records.

## Decisions

1. Use explicit domain models for project settings, plans, weekly updates, materials, repository links, reports, generation jobs, and risk signals.

   Rationale: the workflow depends on historical state and repeatable regeneration rules, so treating reports as derived artifacts from persisted inputs keeps behavior auditable. The alternative was to generate reports directly from form state and GitHub calls, but that would make regeneration and debugging unreliable.

2. Run as a local personal web application in the first release.

   Rationale: report generation and GitHub ingestion depend on local CLIs, local authentication state, temporary files, and local workspace data. Keeping the backend on the same machine as those resources avoids remote credential storage and remote execution complexity. The alternative was remote deployment, which is deferred because it would require a separate runner, credential model, and file access design.

3. Represent weekly schedules as per-project update time rules with timezone-aware timestamps.

   Rationale: each project can have multiple weekly update points, and users may operate across timezones. The alternative was a single global cron schedule, but that would not satisfy project-specific cadence.

4. Use ISO week boundaries in the project timezone for project-week identity.

   Rationale: the weekly report overwrite rule needs a stable project-week key, and ISO Monday-through-Sunday weeks are predictable for work reporting. The alternative was custom week start days per project, which is deferred to keep scheduling and report identity simple in the first release.

5. Normalize all report inputs into a report context snapshot before invoking a CLI provider.

   Rationale: Codex and Claude Code CLIs may have different invocation details, but both need the same project context, plan baseline, manual updates, uploaded material references or extracted text, and GitHub activity summary. The alternative was provider-specific context assembly, which would duplicate business rules and make reports inconsistent.

6. Separate report instructions into a system prompt and a Markdown report template.

   Rationale: the system prompt controls generation behavior, tone, and constraints, while the report template controls the expected Markdown sections. The default template includes this week's summary, completed work, in-progress work, blockers and risks, next week plan, GitHub activity summary, and source/input references. A project-specific template replaces the default template for that project. The alternative was relying only on free-form system prompts, which would make the default output shape inconsistent and harder to test.

7. Run report generation through a background job with provider-specific adapters.

   Rationale: CLI execution can be slow, fail, or need retry and logging. A job boundary lets the UI remain responsive and exposes status. The alternative was synchronous generation from the page, which would be fragile for large repositories or uploads.

8. Support both scheduled and manual report generation triggers.

   Rationale: scheduled update times keep weekly reporting consistent, while a manual trigger lets the user generate immediately after uploading material, editing updates, or missing a schedule. Manual generation uses the same context snapshot, provider execution, job history, and canonical report overwrite rules as scheduled generation. Unlike scheduled generation, manual generation may be forced even when no changed input is detected.

9. Execute CLI providers through platform-mediated context access.

   Rationale: the system owns application state, GitHub access, and report persistence. The CLI provider receives a small prompt with a read-only platform context CLI command and must retrieve project information through that tool rather than reading SQLite, uploaded files, application files, GitHub, or `gh` directly. This supports progressive disclosure for large projects and lets the platform mediate future content types such as images. The job still runs in a temporary working directory and the system persists only the provider's Markdown output. The alternatives were inlining the full context in the prompt, which does not scale, or letting the provider inspect local files and GitHub directly, which bypasses platform permissions and source semantics.

10. Store one canonical current report per project-week while retaining generation job history.

   Rationale: the user expects later configured update times in the same project week to refresh the same visible report instead of creating multiple stage reports. Keeping job history preserves auditability without cluttering the report page. The alternative was keeping every configured-time report as a separate visible report, which conflicts with the overwrite requirement.

11. Expose generation job history as run metadata, and expose prior project-week reports as read-only history.

   Rationale: the personal user needs to understand when generation ran, which provider was used, whether it failed, and what input period or snapshot it used. Prior project-week reports are useful history and can be shown read-only without weakening the canonical overwrite model for the current project week. Generation runs remain run metadata rather than report versions.

12. Treat GitHub integration as an activity source, not a source of project authority.

   Rationale: project plans and manual updates remain the product's source of truth. GitHub commits, pull requests, and issues enrich the report and risk checks. The alternative was deriving project state mainly from GitHub, which would not work for non-code tasks and uploaded materials.

13. Use the local authenticated GitHub CLI (`gh`) for first-release GitHub access.

   Rationale: the product is a personal local workspace and already depends on local CLI tools for report generation, so reusing `gh` avoids storing GitHub tokens in the application and keeps private repository access aligned with the user's local GitHub session. The alternatives were public-repository-only access, which would exclude many personal work projects, and OAuth or GitHub App integration, which adds multi-user credential and installation complexity that is out of scope for the first release.

14. Generate system risk warnings with deterministic rules and keep model-predicted risks in report content.

   Rationale: overdue milestones and missing weekly updates can be tested and explained as project risks. Report generation failures, GitHub connectivity/authentication failures, and material extraction failures are operational diagnostics and remain outside project risk warnings. The generated weekly report can still include a risk section where the CLI provider summarizes risks and forecasts likely follow-on risks, but those generated statements remain report content unless a deterministic project-risk rule also creates a warning. The first release does not support manually promoting report risk forecasts into system warnings. The alternative was allowing generated text or user-selected generated text to create dashboard warnings, which is deferred because it would require additional source tracking and triage semantics.

15. Treat the first release as a personal single-user workspace.

   Rationale: the initial workflow is about one user's weekly tracking and generated status reports, so adding organizations, project members, and role permissions would expand the scope before the reporting loop is proven. The alternative was a team-first permission model, which is deferred until collaboration requirements are explicit.

16. Treat milestone and deliverable owners as optional free-text planning labels.

   Rationale: a personal workspace may still need to mention an external collaborator, vendor, stakeholder, or responsible party in the plan, but those labels must not create system users, roles, membership, or permissions. The alternative was removing owner fields entirely, which would weaken planning expressiveness, or linking owners to users, which would reintroduce a team model that is out of scope.

17. Extract uploaded PDFs locally and summarize a multi-file upload through one configured provider invocation.

   Rationale: local PDF extraction keeps original documents inside the personal workspace, while one bounded prompt containing each original filename and leading extracted text avoids unnecessary provider calls. Summaries are persisted per material and remain manually editable. If generation fails, upload still succeeds with an explicit fallback summary and failure status.

18. Allow deletion only while a material belongs to the current project week.

   Rationale: current-week inputs are still being curated and may be removed when added by mistake, while previous-week inputs are historical report evidence and must remain locked. The server enforces the project-scoped week check for both uploaded and manually entered materials; deleting an uploaded material also removes its local stored file after the database change commits.

19. Model TODO closure as a dedicated, atomic operation.

   Rationale: closing goes through a dedicated operation that records an optional close reason (empty is allowed). The close operation may also select one project; in that case the system creates a Markdown manual material containing the TODO and its close reason in the same database transaction, then records the material association on the TODO. A normal status update cannot bypass these closure requirements.

20. Keep TODO navigation separate from weekly reporting.

   Rationale: TODOs are workspace-level capture items rather than project-week report records. A standalone folded page corner in the top-right alternates between the existing project reporting workspace and a visually distinct dense three-column board. At rest it names the current page; on hover or keyboard focus the corner unfolds downward to reveal the destination page, clearly separating global navigation from contextual actions.

21. Edit TODO cards inline and render their saved descriptions as sanitized Markdown.

   Rationale: board work should stay spatial and immediate. Each card enters an inline title/Markdown editor when clicked and saves automatically when focus leaves the card. Editing a closed card that was archived to a project updates its linked manual material in the same transaction while preserving the close reason. The pending column always ends with a draft card that creates a TODO through the same focus-leave behavior. Read mode uses the existing server-side Markdown sanitizer rather than executing raw HTML in the browser.

22. Place manual report generation on the project row with confirmation.

   Rationale: generation is project-scoped and potentially slow, so its single manual entry point belongs beside each project's settings control. The icon first selects the project when necessary, opens an application-styled confirmation message box, and only starts generation after explicit confirmation. Removing page-level generation and schedule-check buttons keeps the workspace header and report content focused on navigation and results.

23. Render the workspace switch as a borderless paper curl and color-code board columns.

   Rationale: the mode switch should read as a sheet curling from the upper-right corner rather than as a conventional button. Its interactive wrapper remains keyboard accessible but has no visible button box; a soft-shadow triangular paper underside expands on hover/focus and reveals the destination. Pending, in-progress, and closed columns use blue, green, and neutral gray body colors respectively so workflow state is visible before reading labels.

24. Answer weekly report questions through a grounded assistant conversation.

   Rationale: the assistant is interactive, so a question is answered synchronously inside the request (the HTTP server is threaded) rather than through the report task queue. Assembling the full report evidence up front made every question wait for Git APIs, so the prompt carries only the current report plus a cheap local inventory, and the internal agent calls read-only tools on demand. Tool names mirror the zreport CLI read commands (project weekly list/show, search, material show, report show, todo list/show) and extend them with project context the CLI lacks (materials list, plan, weekly supplement, risks, Git repos/commits/activity). The application executes each tool scoped to the project and account and returns bounded JSON, so the model still never touches the database, files or credentials; Git results are cached for ten minutes and tool failures are returned to the model instead of failing the turn. At most six tool rounds run before a final answer is forced. Revisions travel between fixed markers as a complete report so applying one is a plain replacement through the existing manual-edit path; nothing is written to the report without explicit confirmation by a project writer.

25. Define operations once and expose them through thin adapters.

   Rationale: hand-written CLI commands and assistant tools had already drifted (the CLI accepted fewer upload types than the server; the assistant had tools the CLI lacked). Following the MCP tool shape — name, description, JSON-Schema input, `readOnlyHint` — each operation is one registry entry with one handler. HTTP publishes the manifest and an invoke endpoint, the CLI discovers the manifest at runtime the way MCP clients list tools (so new operations need no PyPI release) and caches it for offline help, and the assistant receives the read-only `agent` subset bound to its project. Login, logout, whoami and skill installation stay native to the CLI because they are client-side concerns. Existing REST routes stay for the web UI and older CLI versions.

26. Stream assistant answers from background runs and execute round tools concurrently.

   Rationale: a blocking request showed nothing for up to a minute while tools and the model worked. A question now starts an in-memory run on its own thread; events (round, text deltas, tool start/end, terminal state) are appended with increasing ids and served as server-sent events, which the browser's EventSource consumes with built-in reconnection through Last-Event-ID, so the stream survives network blips and page reloads while the run keeps going. Both SDKs stream (OpenAI `stream=True` with tool-call deltas, Anthropic `messages.stream`). Tool calls from one model round run in a small thread pool, each on its own SQLite connection, so slow Git calls overlap with local reads. Runs stay out of the report task queue because they are interactive; one active run per account and project bounds concurrency, and finished runs are kept for five minutes so late subscribers can replay them. Text from rounds that end in tool calls is treated as preamble and cleared when the next round begins; the report-revision block is hidden while streaming and appears as a proposal only after the run completes. Nothing is stored for failed or stopped runs.

27. Present assistant progress as a T3 Code-style work log.

   Rationale: tool chips with durations hidden in tooltips left users seeing only a generic thinking label, because local tools finish in milliseconds while model thinking takes most of the time. Following T3 Code, the answer carries a chronological work log — thinking segments, raw tool calls and interim text — one muted line each, with running rows shimmering and timers ticking, finished rows showing durations, and tool rows expanding to the raw input and a bounded result excerpt. Every run event carries a run-relative server timestamp so live views, reattached views and the stored log agree; the server builds the log from the same events the browser renders and stores it with the answer, where it folds into an elapsed-time summary.

## Risks / Trade-offs

- CLI provider availability may vary by deployment environment -> Add provider health checks, command path configuration, timeout limits, and clear job failure states.
- Local runtime scope limits remote access -> Treat remote deployment as out of scope and document that the backend must run on the machine with `gh`, Codex CLI, Claude Code CLI, temporary file access, and workspace storage.
- CLI providers could cause unintended side effects -> Run providers in a temporary working directory with context and output file handoff, then persist only the Markdown output read by the system.
- Personal workspace scope can limit future collaboration features -> Keep an owner field on projects and avoid hard-coding anonymous global state so a later team model can migrate cleanly.
- Uploaded project materials may be large or fail text extraction -> Limit first-release support to Markdown, plain text, and PDF; store original files, extract text asynchronously, reject unsupported formats, and include extraction status in report context.
- Local `gh` may be missing, unauthenticated, or unable to access a repository -> Add `gh` availability checks, actionable disconnected states, and last-checked timestamps per repository link.
- Overwriting the current weekly report may hide useful history -> Preserve generation job history and timestamps while showing only the latest successful report as the canonical report for the project-week.
- Generation history can be mistaken for report version history -> Label generation runs separately from read-only historical weekly reports.
- Generated reports can contain unsupported or unsafe Markdown -> Render Markdown through a sanitizer and disable raw HTML by default.
- Risk warnings can become noisy -> Store warning state, severity, source rule, and dismissal/resolution metadata so users can triage recurring warnings.
- Model-generated risk forecasts can be mistaken for system warnings -> Keep report risk sections visually and semantically separate from deterministic risk warning records and do not provide a first-release promotion workflow.

## Migration Plan

This is a new capability set with no existing data migration. Implement behind the new project management routes and data models. Rollback can disable scheduler execution and report generation jobs while preserving stored project, plan, update, and report records.

## Open Questions

- None.
