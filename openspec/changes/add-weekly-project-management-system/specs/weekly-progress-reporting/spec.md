## ADDED Requirements

### Requirement: Weekly progress update capture
The system SHALL allow a user to record progress updates for a project week, including completed work, in-progress work, blockers, risks, and next steps.

#### Scenario: Save weekly progress update
- **WHEN** a user submits a progress update for the current project week
- **THEN** the system stores the update and makes it available for weekly report generation

#### Scenario: Edit weekly progress update
- **WHEN** a user edits an existing progress update for the same project week
- **THEN** the system saves the revised update and marks the project week as having changed input

### Requirement: Multiple weekly update times
The system SHALL support multiple configured update times within the same week for each project as refresh checkpoints for the same project-week report.

#### Scenario: Identify project week
- **WHEN** the system evaluates a configured update time
- **THEN** the system assigns it to the ISO project week calculated in the project's timezone from Monday through Sunday

#### Scenario: Trigger first weekly update time
- **WHEN** the first configured update time for a project week is reached
- **THEN** the system evaluates whether a weekly report generation job is needed for that project week

#### Scenario: Trigger later weekly update time
- **WHEN** a later configured update time in the same project week is reached
- **THEN** the system evaluates new manual updates, uploaded materials, and GitHub activity since the previous generation

#### Scenario: Keep one report identity across update times
- **WHEN** multiple configured update times occur in the same project week
- **THEN** the system uses the same project-week report identity for each successful generation

### Requirement: Regenerate current weekly report when inputs change
The system SHALL regenerate the current project-week report when a configured update time occurs and relevant manual input, uploaded material, or GitHub activity has changed since the last successful report generation.

#### Scenario: Regenerate after new manual update
- **WHEN** a configured update time occurs after a new manual weekly update was saved
- **THEN** the system creates a new report generation job for the same project week

#### Scenario: Regenerate after GitHub activity
- **WHEN** a configured update time occurs after new associated GitHub activity was detected
- **THEN** the system creates a new report generation job for the same project week

#### Scenario: Skip regeneration without changed inputs
- **WHEN** a configured update time occurs and no relevant source input has changed since the last successful report generation
- **THEN** the system does not create a duplicate report generation job

### Requirement: Manual report generation
The system SHALL allow the workspace user to manually generate or regenerate the current project-week report on demand.

#### Scenario: Manually generate current weekly report
- **WHEN** the workspace user triggers manual report generation for a project week
- **THEN** the system creates a report generation job using the same context snapshot, provider, and project-week identity rules as scheduled generation

#### Scenario: Manually force regeneration without changed inputs
- **WHEN** the workspace user triggers manual report generation and no relevant source input has changed since the last successful report generation
- **THEN** the system still creates a report generation job for the same project week

#### Scenario: Manual regeneration overwrites visible report
- **WHEN** a manually triggered regeneration completes successfully for the current project week
- **THEN** the system replaces the visible project-week report content with the new Markdown report

### Requirement: Current weekly report overwrite
The system SHALL keep only the latest successful generated Markdown report as the canonical visible report for a project week.

#### Scenario: Overwrite visible report after regeneration
- **WHEN** a regenerated report for the same project week completes successfully
- **THEN** the system replaces the visible project-week report content with the new Markdown report

#### Scenario: Do not create separate visible reports per update time
- **WHEN** a later configured update time in the same project week generates a report successfully
- **THEN** the system does not create a separate visible stage report for that update time

#### Scenario: Preserve generation history when overwriting
- **WHEN** a regenerated report replaces the visible project-week report
- **THEN** the system preserves the generation run record for audit and troubleshooting

#### Scenario: Preserve previous report on failed regeneration
- **WHEN** a regenerated report for the same project week fails
- **THEN** the system keeps the previous successful report as the visible project-week report

### Requirement: Markdown report rendering
The system SHALL store weekly reports in Markdown format by default and render them on the project report page.

#### Scenario: View weekly report
- **WHEN** a user opens a generated weekly report
- **THEN** the system renders the Markdown report content as formatted page content

#### Scenario: View historical weekly reports
- **WHEN** a user opens the report page for a project with reports from prior project weeks
- **THEN** the system shows those historical weekly reports as read-only rendered Markdown

#### Scenario: Lock historical weekly reports
- **WHEN** a user views a historical weekly report
- **THEN** the system does not provide controls to edit or regenerate that historical report

#### Scenario: Sanitize Markdown rendering
- **WHEN** a report contains raw HTML or unsafe content
- **THEN** the system renders the report without executing unsafe content
