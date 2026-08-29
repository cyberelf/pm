## ADDED Requirements

### Requirement: Personal TODO board
The system SHALL provide a workspace-level personal TODO board separate from project weekly reports.

#### Scenario: Switch to TODO board
- **WHEN** the user chooses TODO from the top-right workspace switch
- **THEN** the system shows the TODO board independently of the selected project's weekly report tabs

#### Scenario: View TODO workflow
- **WHEN** the TODO board loads
- **THEN** the system groups cards into pending, in-progress, and closed columns

#### Scenario: Show all workflow columns
- **WHEN** the TODO board is visible
- **THEN** the pending, in-progress, and closed columns are rendered together without requiring another view selection

#### Scenario: Switch workspace like book pages
- **WHEN** the user changes between TODO and weekly reports
- **THEN** a standalone top-right folded-corner control changes the application mode and the two modes have clearly different visual surfaces

#### Scenario: Preview folded-corner destination
- **WHEN** the mode-switch corner is idle
- **THEN** it displays the current page, and when hovered or keyboard-focused it unfolds downward to display the destination page

#### Scenario: Present switch as paper curl
- **WHEN** the workspace page is visible
- **THEN** the switch has no visible button container and appears as a softly shadowed sheet curled from the upper-right corner

#### Scenario: Color-code workflow columns
- **WHEN** the TODO board is visible
- **THEN** pending, in-progress, and closed columns use blue, green, and neutral gray as their respective primary colors

#### Scenario: Create TODO
- **WHEN** the user submits a TODO with a non-empty title
- **THEN** the system stores it in the pending column

#### Scenario: Start or return TODO
- **WHEN** the user moves an open TODO between pending and in-progress
- **THEN** the system persists the new open status without closing the TODO

#### Scenario: Create from pending draft card
- **WHEN** the user clicks the draft card at the bottom of the pending column and enters a title
- **THEN** the card is created automatically when editing finishes and a fresh draft remains at the bottom

#### Scenario: Edit existing TODO inline
- **WHEN** the user clicks an existing TODO card and changes its title or description
- **THEN** the card becomes an inline editor and automatically persists valid changes when editing finishes

#### Scenario: Keep archived material aligned after editing a closed TODO
- **WHEN** the user edits a closed TODO that has linked project material
- **THEN** the system updates the linked material content while preserving the TODO close reason and project association

#### Scenario: Render TODO Markdown
- **WHEN** a saved TODO description contains Markdown
- **THEN** the board renders sanitized formatted HTML while the inline editor retains the original Markdown source

### Requirement: Controlled TODO closure
The system SHALL close TODOs only through a dedicated operation that records a non-empty close reason.

#### Scenario: Reject closure without reason
- **WHEN** the user attempts to close a TODO without a non-empty reason
- **THEN** the system rejects the operation and leaves the TODO open

#### Scenario: Close TODO without project
- **WHEN** the user supplies a close reason and does not select a project
- **THEN** the system closes the TODO and stores the reason without creating project material

#### Scenario: Close TODO into project materials
- **WHEN** the user supplies a close reason and selects a project
- **THEN** the system atomically closes the TODO, associates it with that project, and adds a Markdown manual material containing the TODO details and close reason to the project

#### Scenario: Prevent repeated closure
- **WHEN** the user attempts to close an already closed TODO
- **THEN** the system rejects the operation without adding another project material
