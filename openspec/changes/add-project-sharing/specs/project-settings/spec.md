## MODIFIED Requirements

### Requirement: Personal workspace ownership
The system SHALL keep exactly one owner per project — the account in `projects.user_id` — and SHALL let only that owner grant, change, or revoke per-project collaborator roles; role-based collaboration exists only through explicit owner-granted shares and never grants administrators or other accounts automatic access to a project.

#### Scenario: Assign personal project owner
- **WHEN** the workspace user creates a project
- **THEN** the system assigns that user as the project's owner

#### Scenario: Collaboration only through explicit shares
- **WHEN** another account interacts with a project
- **THEN** the system grants exactly the permissions of the share role the owner granted, or no access at all when no share exists

#### Scenario: Planning owner labels do not grant access
- **WHEN** a project plan uses owner labels on milestones or deliverables
- **THEN** the system treats those labels as planning text and does not grant project access or permissions from them
