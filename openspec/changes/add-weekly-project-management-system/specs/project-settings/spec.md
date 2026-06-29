## ADDED Requirements

### Requirement: Project creation
The system SHALL allow the workspace user to create a personal project with a name, description, owner, start date, optional end date, and status.

#### Scenario: Create project with required fields
- **WHEN** a user submits valid required project fields
- **THEN** the system creates the project and opens its project workspace

#### Scenario: Reject project without name
- **WHEN** a user submits a project without a name
- **THEN** the system rejects the request and reports that the project name is required

### Requirement: Personal workspace ownership
The system SHALL scope first-release projects to a personal single-user workspace with exactly one project owner and no team membership or role-based collaboration.

#### Scenario: Assign personal project owner
- **WHEN** the workspace user creates a project
- **THEN** the system assigns that user as the project's owner

#### Scenario: No team member management
- **WHEN** the workspace user edits project settings
- **THEN** the system does not require team members, roles, or shared project permissions

#### Scenario: Planning owner labels do not grant access
- **WHEN** a project plan uses owner labels on milestones or deliverables
- **THEN** the system treats those labels as planning text and does not grant project access or permissions from them

### Requirement: Local workspace runtime
The system SHALL run the first release as a local personal web application whose backend accesses workspace data and required local CLI tools on the same machine.

#### Scenario: Use local backend resources
- **WHEN** the system reads GitHub activity or generates a report
- **THEN** the backend uses local workspace storage, local temporary files, and local CLI tools available on the same machine

#### Scenario: Remote deployment not required
- **WHEN** the first release is installed or run
- **THEN** the system does not require support for a remote backend separated from local `gh`, Codex CLI, Claude Code CLI, or workspace files

### Requirement: Project settings
The system SHALL allow a user to edit project settings including project metadata, weekly update schedule, report provider, report system prompt, and GitHub repository associations.

#### Scenario: Save project settings
- **WHEN** a user changes project settings and saves them
- **THEN** the system persists the new settings for future planning, reporting, and risk checks

#### Scenario: Validate weekly update schedule
- **WHEN** a user configures weekly update times
- **THEN** the system validates each time with a weekday, local time, and timezone before saving

#### Scenario: Use ISO project week boundaries
- **WHEN** the system evaluates weekly update schedules or report identity for a project
- **THEN** the system calculates the project week in the project's timezone from Monday through Sunday

### Requirement: Project source materials
The system SHALL allow a user to add project context through manual fields, uploaded Markdown/plain text/PDF project materials, and manually entered material notes.

#### Scenario: Add manual project context
- **WHEN** a user saves manual project background, objectives, or constraints
- **THEN** the system stores that content as project source context

#### Scenario: Upload project material
- **WHEN** a user uploads a Markdown, plain text, or PDF project material file
- **THEN** the system stores the file, records its metadata, and makes it available for report context extraction

#### Scenario: Add current-week manual material
- **WHEN** a user saves manually entered material content for a project
- **THEN** the system stores the title, content, creation time, and update time as a project material source

#### Scenario: Edit current-week manual material
- **WHEN** a user edits manually entered material created in the current project week
- **THEN** the system updates the material content and update time

#### Scenario: Lock previous-week manual material
- **WHEN** a user attempts to edit manually entered material created before the current project week
- **THEN** the system rejects the edit and keeps the historical material unchanged

#### Scenario: Reject unsupported project material
- **WHEN** a user uploads a file that is not Markdown, plain text, or PDF
- **THEN** the system rejects the upload and reports that the file type is unsupported

#### Scenario: Record material extraction failure
- **WHEN** text extraction fails for a stored project material
- **THEN** the system keeps the original file metadata and marks the material extraction status as failed

### Requirement: GitHub repository association
The system SHALL allow a project to be associated with one or more GitHub repositories accessed through the local authenticated GitHub CLI (`gh`).

#### Scenario: Add GitHub repository link
- **WHEN** a user adds a valid GitHub repository association and local `gh` can access the repository
- **THEN** the system stores the association and records it as an activity source for the project

#### Scenario: Detect invalid GitHub repository link
- **WHEN** a user adds an invalid or inaccessible GitHub repository association
- **THEN** the system rejects the association or marks it as disconnected with an actionable status

#### Scenario: Detect missing GitHub CLI authentication
- **WHEN** a user adds a GitHub repository association and local `gh` is missing or unauthenticated
- **THEN** the system marks the association as disconnected and reports that local GitHub CLI authentication is required

### Requirement: Per-project report configuration
The system SHALL support per-project configuration of the weekly report provider, system prompt, and Markdown report template.

#### Scenario: Configure Codex report generation
- **WHEN** a user selects Codex CLI as the project's report provider and saves a system prompt
- **THEN** the system uses that provider and prompt for future weekly report generation jobs

#### Scenario: Configure Claude Code report generation
- **WHEN** a user selects Claude Code CLI as the project's report provider and saves a system prompt
- **THEN** the system uses that provider and prompt for future weekly report generation jobs

#### Scenario: Configure project report template
- **WHEN** a user saves a project-specific Markdown report template
- **THEN** the system uses that template for future weekly report generation jobs for that project

#### Scenario: Use default report template
- **WHEN** a project has no project-specific Markdown report template
- **THEN** the system uses the default weekly report template for future weekly report generation jobs
