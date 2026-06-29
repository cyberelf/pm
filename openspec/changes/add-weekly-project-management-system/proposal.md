## Why

Individual knowledge workers need a consistent way to track weekly project work without manually assembling status reports from plans, uploaded materials, and GitHub activity. This change introduces a local personal project management workspace focused on recurring weekly progress capture, automated report generation, and visible risk signals.

## What Changes

- Add project creation and settings so each project can define metadata, schedule, source materials, GitHub links, and report generation configuration.
- Add project planning support for milestones, planned work, optional free-text owner labels, timelines, and expected weekly outcomes.
- Add weekly progress update support with multiple configured update times per week.
- Add manual immediate report generation so the workspace user can generate or regenerate the current project-week report on demand.
- Define each project week by the project's timezone using ISO week boundaries from Monday through Sunday.
- Add document upload for Markdown, plain text, and PDF materials plus manual input sources that can be used as project context for planning and reporting.
- Add GitHub association through the local authenticated GitHub CLI (`gh`) so repository activity can be considered during report generation.
- Add automated weekly report generation through configurable CLI providers, including Codex CLI and Claude Code CLI.
- Add per-project system prompt configuration for weekly report generation.
- Add a default Markdown weekly report template and allow each project to configure its own report template.
- Render weekly reports in Markdown by default and support one canonical report per project week; multiple configured update times are refresh checkpoints that overwrite the current week's visible report after successful regeneration.
- Add progress tracking and risk warning views based on deterministic rules over plans, weekly updates, source availability, and detected project gaps.
- Include a risk section in generated weekly reports where the CLI provider can summarize observed risks and forecast likely follow-on risks from available context.
- Scope the first release to a personal single-user workspace where each project has one owner and no team membership or role-based collaboration.
- Scope the first release to a local web application where the backend and required CLIs run on the same machine as the workspace data.
- Do not support custom per-project week start days in the first release.
- Do not support promoting agent-generated report risk forecasts into system risk warnings in the first release.

## Capabilities

### New Capabilities

- `project-settings`: Project creation, configuration, source materials, GitHub associations, update schedules, and report prompt/provider settings.
- `project-planning`: Project plans, milestones, planned weekly outcomes, optional free-text owner labels, and timeline tracking.
- `weekly-progress-reporting`: Weekly progress capture, scheduled update points, report regeneration rules, Markdown storage, and page rendering.
- `report-generation-integrations`: CLI-based report generation using Codex or Claude Code with project-specific prompts and gathered context.
- `progress-risk-tracking`: Progress status tracking and risk warning behavior derived from plans, updates, reports, and missing or delayed activity.

### Modified Capabilities

- None.

## Impact

- Requires new application data models for projects, plans, weekly updates, materials, repository links, generated reports, report generation jobs, and risk signals.
- Requires background scheduling or job orchestration for configured weekly update times and report regeneration.
- Requires file upload/storage support and text extraction for Markdown, plain text, and PDF project materials.
- Requires local GitHub CLI (`gh`) integration for repository metadata and activity detection.
- Requires CLI execution integration for Codex and Claude Code report generation.
- Requires Markdown rendering in the project report UI.
- Does not require organization, team, role, or project sharing APIs in the first release.
- Does not require remote server deployment support in the first release.
