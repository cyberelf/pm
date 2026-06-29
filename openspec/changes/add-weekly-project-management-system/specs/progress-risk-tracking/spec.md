## ADDED Requirements

### Requirement: Progress status tracking
The system SHALL track project progress status from plan milestones, weekly planned outcomes, manual updates, and deterministic project-risk rules.

#### Scenario: Calculate weekly progress status
- **WHEN** a project week has planned outcomes and progress updates
- **THEN** the system determines whether the week is on track, at risk, blocked, or complete

#### Scenario: Reflect milestone progress
- **WHEN** a milestone status changes
- **THEN** the system updates project progress indicators that depend on that milestone

### Requirement: Missing update risk warning
The system SHALL create a risk warning when a configured weekly update time passes without required progress input or source activity.

#### Scenario: Warn after missing weekly update
- **WHEN** a configured update time passes and the project has no manual weekly update, uploaded material change, or GitHub activity for the current period
- **THEN** the system creates or updates a missing update risk warning

### Requirement: Plan delay risk warning
The system SHALL create a risk warning when milestones or planned weekly outcomes are overdue or marked blocked.

#### Scenario: Warn on overdue milestone
- **WHEN** a milestone target date has passed and the milestone is not complete
- **THEN** the system creates or updates an overdue milestone risk warning

#### Scenario: Warn on blocked outcome
- **WHEN** a weekly planned outcome is marked blocked
- **THEN** the system creates or updates a blocked outcome risk warning

### Requirement: System diagnostics separation
The system SHALL display source and generation failures as operational diagnostics without creating project risk warnings.

#### Scenario: Keep report generation failure out of project risks
- **WHEN** a scheduled or manual report generation job fails for the current project week
- **THEN** the system records the failure in generation history without creating a project risk warning

#### Scenario: Keep unavailable GitHub source out of project risks
- **WHEN** a project has an associated GitHub repository and local `gh` is missing, unauthenticated, or unable to access the repository during the current period
- **THEN** the system displays a GitHub source diagnostic without creating a project risk warning

#### Scenario: Keep material extraction failure out of project risks
- **WHEN** a project material needed for report context has failed text extraction
- **THEN** the system displays a material extraction diagnostic without creating a project risk warning

### Requirement: Generated report risk section separation
The system SHALL keep agent-generated risk forecasts in the weekly report content separate from deterministic system risk warning records.

#### Scenario: Render generated risk forecast
- **WHEN** a generated weekly report contains a risk or forecast section
- **THEN** the system renders that section as part of the Markdown report content

#### Scenario: Do not automatically create warning from generated text
- **WHEN** a generated weekly report contains predicted or extrapolated risks
- **THEN** the system does not create a system risk warning from that text unless a deterministic risk rule is also satisfied

#### Scenario: Do not promote generated risk forecast
- **WHEN** a user views a generated weekly report risk forecast
- **THEN** the system does not provide a first-release action to promote that forecast into a system risk warning

### Requirement: Risk warning lifecycle
The system SHALL allow risk warnings to be created, updated, resolved, and dismissed while preserving their source rule and severity.

#### Scenario: Resolve risk warning
- **WHEN** the condition that created a risk warning no longer applies
- **THEN** the system marks the warning resolved or eligible for resolution

#### Scenario: Dismiss risk warning
- **WHEN** a user dismisses a risk warning
- **THEN** the system records the dismissal without deleting the warning history

### Requirement: Risk dashboard
The system SHALL display progress status and active risk warnings in the project workspace.

#### Scenario: View project risks
- **WHEN** a user opens a project's progress or risk view
- **THEN** the system displays current progress status, active warnings, severity, affected plan items, and last updated time

#### Scenario: View operational diagnostics
- **WHEN** a user opens a project's progress or risk view
- **THEN** the system separately displays source and generation diagnostics without including them in active project risk counts
