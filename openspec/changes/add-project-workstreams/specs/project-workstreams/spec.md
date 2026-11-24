## ADDED Requirements

### Requirement: Flat workstreams inside a project
The system SHALL let a project hold an ordered list of workstreams, each with a unique name within the project, goal, owner label, status (active, paused or done) and optional target date. Workstreams SHALL have at most two levels (see Sub-workstreams), SHALL follow the project's roles (read views, write creates, edits, reorders and deletes) and SHALL be deleted with their project. Deleting a workstream SHALL remove its links and snapshots but keep the linked materials and TODOs.

#### Scenario: Create and edit a workstream
- **WHEN** a project writer creates a workstream with a name not used in the project
- **THEN** the system stores it and lists it in project order with its derived health

#### Scenario: Duplicate or empty names are rejected
- **WHEN** a writer submits an empty name or a name already used in the project
- **THEN** the system rejects the request without changes

#### Scenario: Read-only collaborator
- **WHEN** a read collaborator calls a workstream write endpoint
- **THEN** the system rejects it with a permission error while the workstream view stays readable

#### Scenario: Seed from plan objectives
- **WHEN** a writer runs 从目标生成 on a project whose objectives contain numbered or bulleted lines
- **THEN** the system creates one workstream per line, named by the line's first clause, with the whole line as its goal, skipping names that already exist; an indented line or a `1.1`-style number under a top-level line becomes a sub-workstream of it

### Requirement: Material and TODO workstream links
The system SHALL let a material carry at most one primary workstream and any number of related workstreams of the same project, and SHALL let an account link its own TODOs the same way to workstreams of projects it can write. Links SHALL record whether they were assigned automatically or manually. TODO links SHALL be returned only to the TODO's owner. Closing a TODO into a project SHALL copy that project's links onto the archived material.

#### Scenario: Assign a material
- **WHEN** a writer sets a material's primary and related workstreams
- **THEN** the system replaces the material's links and marks them manual

#### Scenario: Foreign workstream rejected
- **WHEN** a request links a material to a workstream of another project
- **THEN** the system rejects it

#### Scenario: Private TODO links
- **WHEN** a collaborator opens a workstream that another account's TODO is linked to
- **THEN** the collaborator does not see that TODO

#### Scenario: Close a linked TODO
- **WHEN** an account closes a TODO linked to a workstream into that workstream's project
- **THEN** the archived material carries the same workstream links

### Requirement: Agent-assisted classification
The system SHALL classify uploaded files to an active workstream in the same internal-agent call that summarises them when the project has active workstreams and the request names none, SHALL honour an explicit workstream in the request as a manual link, and SHALL never overwrite manual links automatically. A queued 「AI 整理」 job SHALL classify unassigned materials in bounded batches and update weekly snapshots as defined under locked past weeks, sharing the task queue's capacity accounting.

#### Scenario: Upload classified automatically
- **WHEN** a writer uploads a file without choosing a workstream in a project with active workstreams
- **THEN** the material is linked to the workstream the agent returned, marked automatic, or stays unassigned when the agent returns none or an unknown id

#### Scenario: Explicit choice wins
- **WHEN** an upload or manual material names a workstream
- **THEN** the material is linked to it as manual and the agent's suggestion is ignored

#### Scenario: Batch organise
- **WHEN** a writer starts 「AI 整理」
- **THEN** the system queues one job per project, rejects a second concurrent one, links unassigned materials, adds missing snapshots, and leaves manual links and manual snapshots unchanged

### Requirement: Weekly workstream snapshots
The system SHALL keep at most one snapshot per workstream and project week with status (advanced, steady or blocked), a one-line progress summary and a next step. After a successful report generation for the current week in a project with workstreams the system SHALL extract snapshots for active workstreams from the report and the week's linked materials through the internal agent; a failed extraction SHALL NOT fail the report. Writers MAY edit the current week's snapshot, which marks it manual. Generated risk forecasts SHALL stay in report Markdown.

#### Scenario: Snapshots after generation
- **WHEN** a weekly report is generated successfully for a project with active workstreams
- **THEN** each active workstream has a snapshot for that week unless a manual snapshot already exists

#### Scenario: Extraction failure
- **WHEN** snapshot extraction fails
- **THEN** the report is still saved and marked successful

### Requirement: Deterministic workstream health
The system SHALL derive each workstream's health deterministically: done and paused follow status; otherwise blocked when its target date has passed or a milestone linked to it is overdue, at risk when no material linked to it was created in the current or previous project week and it is older than that window, else on track. The system SHALL raise `workstream_overdue` (high) and `workstream_stale` (medium) risk warnings for those conditions, resolve them when the condition clears, and only `workstream_overdue` SHALL affect the project's progress status.

#### Scenario: Stale workstream
- **WHEN** an active workstream older than two project weeks has no linked material created in the current or previous week
- **THEN** its health is at risk and a `workstream_stale` warning is active

#### Scenario: Paused workstream exempt
- **WHEN** a workstream is paused
- **THEN** no stale or overdue warning is raised for it

### Requirement: Workstream evidence in report generation
The system SHALL include the project's workstreams and each new material's workstream in the bounded report evidence and SHALL instruct the internal agent to organise progress by active workstream, stating explicitly when one had no evidence this week.

#### Scenario: Evidence carries workstreams
- **WHEN** a report is generated for a project with workstreams
- **THEN** the evidence lists the workstreams and tags each new material with its primary workstream name

### Requirement: Long-range workstream view
The system SHALL provide a 工作线 workspace view with a workstream × week matrix (next to the progress view) over the last eight project weeks (snapshot status and summary per cell, the current week's linked material count when no snapshot exists) and a detail panel with goal, fields, linked milestones, the snapshot timeline, linked materials and the viewer's own linked open TODOs. Sources SHALL be filterable by workstream (including 未归类), and materials added while a workstream filter is active SHALL be linked to it.

#### Scenario: Open the matrix
- **WHEN** a reader opens the 工作线 tab
- **THEN** each workstream shows its health, owner and one cell per recent week

#### Scenario: Filtered upload
- **WHEN** a writer uploads a file while the sources view is filtered to a workstream
- **THEN** the material is linked to that workstream as manual

### Requirement: Workstream operations
The system SHALL expose read-only `workstream_list` and `workstream_show` operations through the HTTP operations API, the CLI and the assistant, and a `workstream` parameter on `materials_add` that links the new materials as manual; `materials_list` SHALL include each material's primary workstream.

#### Scenario: Assistant answers per workstream
- **WHEN** the assistant is asked about one workstream's progress
- **THEN** it can call `workstream_show` for the bound project and receive that workstream's snapshots, milestones and linked materials

### Requirement: Locked past weeks and incremental organisation
The system SHALL treat past project weeks as locked for workstream snapshots: manual and agent snapshots SHALL only be written for the current project week, except the one-time history initialisation. The project's first successful 「AI 整理」 SHALL classify every unassigned material and fill snapshots that are missing for active workstreams from archived reports of the last eight weeks; every later run SHALL only classify materials created this week and refresh this week's snapshots and tracking items.

#### Scenario: Manual snapshot for a past week
- **WHEN** a writer records a snapshot for a week before the current one
- **THEN** the system rejects it as locked and keeps that week unchanged

#### Scenario: Incremental organisation
- **WHEN** 「AI 整理」 runs for a project that was organised before
- **THEN** only unassigned materials created this week are classified, past snapshots are left as they are, and the job summary starts with 本周

### Requirement: Workstream tracking items
The system SHALL keep shared tracking items (待跟踪项) per workstream with title, optional owner and due date, and open/done status, visible to every project member and editable by writers. The agent SHALL be able to add follow-ups found in the current week's evidence (marked as agent items, skipping titles that match an existing item of the workstream) and close only its own open items; a person's edit SHALL turn an item into a manual one. An open item past its due date SHALL mark the workstream at risk and raise a medium `workstream_item_overdue` warning that does not block the project status.

#### Scenario: Agent follow-up
- **WHEN** this week's evidence for a workstream mentions a new follow-up
- **THEN** 「AI 整理」 adds it as an AI item, and a later run that sees it finished closes it while manual items stay open

#### Scenario: Overdue item
- **WHEN** an open item's due date has passed
- **THEN** the workstream health is 有风险 and the risk list shows a medium warning for it

### Requirement: Visual progress view
The 工作线 tab SHALL offer a progress view, the default, next to the week matrix: a summary of workstream health counts, current-week progress and open or overdue tracking items, and one lane per workstream covering the last eight weeks plus the future weeks up to the latest target, milestone or due date (at least 4, at most 26), with past weeks colored by snapshot status, milestone and target markers placed by date, a today line, and tracking-item completion.

#### Scenario: Reading the progress view
- **WHEN** a member opens the 工作线 tab
- **THEN** each workstream shows its weekly status lane, upcoming milestones and target date against today, and how many tracking items are open or overdue

### Requirement: Sub-workstreams
The system SHALL let a top-level workstream hold sub-workstreams (子工作线) of the same project, one level deep: a sub-workstream SHALL NOT have children, a workstream with children SHALL NOT be placed under another, and names SHALL stay unique across both levels. Sub-workstreams SHALL carry their own links, snapshots, tracking items, milestones and warnings. An active parent's displayed health SHALL be the worst of its own and its active children's, naming the children that pulled it down, and a parent's staleness SHALL count material linked to its children. Deleting a parent SHALL turn its children into top-level workstreams. Lists SHALL show children right under their parent (`parent / name` as the path), the progress view and matrix SHALL let a viewer fold a parent's children, a parent's sources filter SHALL include its children's materials, and the agent SHALL prefer the most specific line when classifying and summarise a parent across its children without copying their follow-ups.

#### Scenario: Nesting depth
- **WHEN** a writer tries to create a workstream under a sub-workstream
- **THEN** the system rejects it

#### Scenario: Parent rolls up a child at risk
- **WHEN** a sub-workstream has an overdue tracking item
- **THEN** the sub-workstream and its parent both show 有风险, and only the sub-workstream raises the warning

### Requirement: Plan and risks inside the workstream tab
The 工作线 tab SHALL hold the project plan and the risk list, replacing the separate 计划和风险 tab. Each milestone SHALL have a stable id and belong to one workstream or to the project: a workstream's milestones SHALL be added, edited, completed, moved or deleted in its detail panel, and the 项目计划 panel SHALL edit the objectives, project-level milestones (assigning one to a workstream moves it there) and deliverables without touching workstream milestones. The 风险提醒 panel SHALL list this week's deterministic warnings with the project progress status, linking workstream warnings to their workstream. An overdue milestone of an active workstream SHALL be reported only by `workstream_overdue`; `overdue_milestone` SHALL cover project-level milestones and those of inactive workstreams.

#### Scenario: Move a project milestone into a workstream
- **WHEN** a writer picks a workstream for a project-level milestone in 项目计划
- **THEN** the milestone moves to that workstream's detail and timeline and leaves the project-level list

#### Scenario: One warning per overdue milestone
- **WHEN** a milestone of an active workstream passes its date unfinished
- **THEN** the risk list shows the workstream's overdue warning and no separate milestone warning

### Requirement: PR and issue activity per workstream
The system SHALL sync, for each connected repository with its PR or issue switch on, the pull/merge requests and issues updated in the current project week during 「AI 整理」, and SHALL store those the report run already fetched without new remote calls. Each item SHALL be linked to at most one workstream: a person's choice first (kept for later weeks), else an earlier agent link, else the repository's default workstream, else the internal agent's classification. Linked items SHALL be snapshot and tracking-item evidence, SHALL count as activity for the staleness rule, and SHALL be listed in the workstream detail and per-week lanes; unlinked items of the week SHALL be listed for manual assignment.

#### Scenario: Repository default
- **WHEN** a repository has a default workstream and one of its PRs is merged this week
- **THEN** 「AI 整理」 links the PR to that workstream and the week's snapshot can cite it as progress

#### Scenario: Manual choice survives
- **WHEN** a writer moves an issue to another workstream
- **THEN** later syncs keep that link even if the repository default changes
