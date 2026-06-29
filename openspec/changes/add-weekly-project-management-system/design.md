## Context

The product is a new local personal project management system focused on weekly work tracking. There is no existing implementation or domain spec in this repository, so this design defines the first application boundaries for projects, plans, weekly reports, source ingestion, generated report jobs, and risk signals.

The first release runs as a local personal web application: the browser provides the UI, and the backend runs on the same machine as workspace data, uploaded files, local `gh`, Codex CLI, and Claude Code CLI. The system must support mixed project context sources: manual project data, uploaded materials, and GitHub activity read through the local authenticated GitHub CLI (`gh`). Each project week is calculated in the project's timezone using ISO week boundaries from Monday through Sunday. Each project week has one canonical Markdown report. One or more configured update times act as refresh checkpoints that may regenerate and overwrite that week's visible report when new relevant inputs arrive.

## Goals / Non-Goals

**Goals:**

- Model projects with settings for schedule, report provider, prompt, uploaded materials, and GitHub repository links.
- Scope the first release to a personal single-user workspace where each project has exactly one owner.
- Run the first release as a local web application whose backend can access the local CLI tools and workspace files.
- Capture project plans and weekly expected outcomes so reports and risk checks have a baseline.
- Collect manual weekly updates and source changes into a normalized context package for report generation.
- Read GitHub repository metadata and activity through the local `gh` CLI for the first release.
- Run Codex CLI or Claude Code CLI through a provider abstraction that can be configured per project.
- Use a default Markdown weekly report template when a project does not define its own report template.
- Allow each project to configure its own report template in addition to its system prompt.
- Store generated weekly reports as Markdown and overwrite the current week's report when regeneration is required.
- Allow manual immediate generation or regeneration using the same report context snapshot and overwrite rules as scheduled jobs.
- Show generation job history to the workspace user for audit and troubleshooting, and show prior project-week reports as read-only historical reports.
- Track progress and generate project risk warnings from deterministic rules over plan status, missing updates, source availability, and project gaps.
- Ask the report provider to include a risk section that can summarize observed risks and forecast likely follow-on risks from the assembled context.

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

   Rationale: project plans, weekly expected outcomes, and manual updates remain the product's source of truth. GitHub commits, pull requests, and issues enrich the report and risk checks. The alternative was deriving project state mainly from GitHub, which would not work for non-code tasks and uploaded materials.

13. Use the local authenticated GitHub CLI (`gh`) for first-release GitHub access.

   Rationale: the product is a personal local workspace and already depends on local CLI tools for report generation, so reusing `gh` avoids storing GitHub tokens in the application and keeps private repository access aligned with the user's local GitHub session. The alternatives were public-repository-only access, which would exclude many personal work projects, and OAuth or GitHub App integration, which adds multi-user credential and installation complexity that is out of scope for the first release.

14. Generate system risk warnings with deterministic rules and keep model-predicted risks in report content.

   Rationale: overdue milestones, missing weekly updates, no activity after a scheduled update time, and unavailable source inputs can be tested and explained as project risks. Report generation failures are operational diagnostics and remain in generation history rather than project risk warnings. The generated weekly report can still include a risk section where the CLI provider summarizes risks and forecasts likely follow-on risks, but those generated statements remain report content unless a deterministic project-risk rule also creates a warning. The first release does not support manually promoting report risk forecasts into system warnings. The alternative was allowing generated text or user-selected generated text to create dashboard warnings, which is deferred because it would require additional source tracking and triage semantics.

15. Treat the first release as a personal single-user workspace.

   Rationale: the initial workflow is about one user's weekly tracking and generated status reports, so adding organizations, project members, and role permissions would expand the scope before the reporting loop is proven. The alternative was a team-first permission model, which is deferred until collaboration requirements are explicit.

16. Treat milestone and deliverable owners as optional free-text planning labels.

   Rationale: a personal workspace may still need to mention an external collaborator, vendor, stakeholder, or responsible party in the plan, but those labels must not create system users, roles, membership, or permissions. The alternative was removing owner fields entirely, which would weaken planning expressiveness, or linking owners to users, which would reintroduce a team model that is out of scope.

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
