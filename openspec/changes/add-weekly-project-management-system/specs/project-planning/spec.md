## ADDED Requirements

### Requirement: Project plan management
The system SHALL allow a user to create and update a project plan containing objectives, milestones, deliverables, optional free-text owner labels, target dates, and status.

#### Scenario: Create project plan
- **WHEN** a user saves a project plan with milestones and deliverables
- **THEN** the system stores the plan as the project's current planning baseline

#### Scenario: Update milestone status
- **WHEN** a user changes a milestone status
- **THEN** the system records the new status for progress tracking and future reports

#### Scenario: Use free-text planning owner
- **WHEN** a user assigns an owner label to a milestone or deliverable
- **THEN** the system stores the label as planning text without creating user membership, roles, or permissions

### Requirement: Weekly planned outcomes
The system SHALL allow a user to define planned outcomes for each project week.

#### Scenario: Add weekly planned outcome
- **WHEN** a user adds planned outcomes for a project week
- **THEN** the system stores those outcomes and associates them with that week

#### Scenario: Use planned outcomes in report context
- **WHEN** a weekly report is generated for a project week
- **THEN** the system includes that week's planned outcomes in the report context

### Requirement: Plan history
The system SHALL preserve enough plan change history to explain differences between past reports and the current plan.

#### Scenario: Change plan after weekly report
- **WHEN** a user updates the project plan after a weekly report has been generated
- **THEN** the system records the plan change time so the report can be compared against the plan version used at generation time

### Requirement: Plan visibility
The system SHALL render the current project plan in the project workspace with milestone and deliverable status.

#### Scenario: View project plan
- **WHEN** a user opens a project's plan page
- **THEN** the system displays the current objectives, milestones, deliverables, free-text owner labels, target dates, and statuses
