## ADDED Requirements

### Requirement: Owner-granted per-project roles
The system SHALL allow a project's owner to grant other enabled accounts a per-project role — read (只读), upload (上传资料), write (读写), or manage (管理) — stored per project and user, and SHALL keep the owner (projects.user_id) above every share role in the hierarchy `owner > manage > write > upload > read`.

#### Scenario: Grant a share
- **WHEN** the owner submits an existing enabled username with a valid role
- **THEN** the system stores the share and lists the member with username, role, and grant time

#### Scenario: Update an existing share
- **WHEN** the owner submits the same username with a different role
- **THEN** the system updates that member's role in place

#### Scenario: Reject invalid share grants
- **WHEN** the owner submits an unknown username, a disabled account, the owner's own username, or a role outside read/upload/write/manage
- **THEN** the system rejects the request without changing existing shares

#### Scenario: Revoke a share
- **WHEN** the owner removes a member
- **THEN** that account immediately loses access to the project and its content disappears from the account's project list and search scope

### Requirement: Share management is owner-only
The system SHALL restrict viewing and changing the share list (grant, role change, revoke) to the project owner, and SHALL deny any other role with a permission error.

#### Scenario: Collaborator cannot manage members
- **WHEN** an upload, write or manage collaborator calls the share management API
- **THEN** the system rejects the request with a permission error

#### Scenario: Owner sees each member's last access
- **WHEN** the owner lists the share members
- **THEN** each member shows when it last opened the project through the web UI or CLI (recorded at most every five minutes), or that it never has

### Requirement: Role-checked project access
The system SHALL enforce the role hierarchy on every project-scoped API: read may view the workspace, materials, weekly reports, PDF export, repository configuration, and diagnostics; upload additionally adds or edits materials and summaries, sets a material's workstreams, links the account's TODOs to the project's workstreams, and archives TODOs into the project; write additionally saves weekly updates and the plan, edits the current-week report, triggers generation, maintains workstreams (lines, snapshots, milestones, 待跟踪项, PR / issue links) and queues 「AI 整理」, and changes risk warning status; manage additionally saves project settings and schedules, adds/updates/deletes repositories, refreshes repositories, deletes materials, and pauses or resumes the project.

#### Scenario: Read-only collaborator view
- **WHEN** a read collaborator opens the workspace
- **THEN** the system returns the full workspace content but rejects every write endpoint with a permission error

#### Scenario: Upload collaborator contributes materials only
- **WHEN** an upload collaborator uploads a material and files it under a workstream
- **THEN** the system accepts both, but rejects saving the weekly update, editing the report or plan, generating, changing workstreams, and queuing 「AI 整理」 with a permission error

#### Scenario: Write collaborator contributes
- **WHEN** a write collaborator uploads a material, saves the weekly update, edits the current-week report, or queues 「AI 整理」
- **THEN** the system accepts the change and it is visible to the owner and other collaborators

#### Scenario: Write collaborator cannot configure
- **WHEN** a write collaborator changes project settings, toggles project status, manages repositories, or deletes a material
- **THEN** the system rejects the request with a permission error

#### Scenario: Manage collaborator configures
- **WHEN** a manage collaborator saves project settings or deletes a material
- **THEN** the system accepts the change

#### Scenario: Unknown or unshared projects stay invisible
- **WHEN** an account without ownership or a share requests a project's APIs
- **THEN** the system answers not found without revealing whether the project exists

### Requirement: Shared projects in account surfaces
The system SHALL include shared projects in the account's project list with the granted role and the owner's username, SHALL carry the role in workspace payloads, and SHALL extend hybrid search scope and task-queue visibility to accessible (owned or shared) projects.

#### Scenario: Project list shows shared projects
- **WHEN** a collaborator loads the account state
- **THEN** the response lists the shared project with its role and the owner's username alongside owned projects

#### Scenario: Collaborator sees generation jobs they triggered
- **WHEN** a write collaborator queues a report generation
- **THEN** the queue snapshot lists that project's job for them

#### Scenario: Search covers shared projects
- **WHEN** a collaborator searches and a shared project's report or material matches
- **THEN** the hit is returned; after revocation it no longer appears
