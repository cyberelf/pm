## ADDED Requirements

### Requirement: Flat workstreams inside a project
The system SHALL let a project hold an ordered list of workstreams, each with a unique name within the project, goal, owner (a project team member, see Project team members), status (active, paused or done) and optional target date. Workstreams SHALL have at most two levels (see Sub-workstreams), SHALL follow the project's roles (read views, write creates, edits, reorders and deletes) and SHALL be deleted with their project. Deleting a workstream SHALL remove its links and snapshots but keep the linked materials and TODOs.

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
- **WHEN** a writer runs 按目标生成工作线 on a project whose objectives contain numbered or bulleted lines
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
The system SHALL provide a 工作线 workspace view with a workstream × week matrix (next to the progress view) over the last eight project weeks (snapshot status and summary per cell, the current week's linked material count when no snapshot exists) and a detail view with goal, fields, linked milestones, the snapshot timeline, linked materials and the linked TODOs (see Workstream TODOs). Opening a workstream SHALL show its detail in its own closable sub-tab of the 工作线 tab (next to a 全部工作线 tab holding the board), so several workstreams can stay open without scrolling below the board. Sources SHALL be filterable by workstream (including 未归类), and materials added while a workstream filter is active SHALL be linked to it. Writers SHALL close (关闭) or reopen (重新打开) a workstream from its detail panel; the progress view and matrix SHALL hide closed workstreams by default and offer a per-viewer 显示已关闭 toggle with the closed count.

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
The system SHALL treat past project weeks as locked for workstream snapshots: manual and agent snapshots SHALL only be written for the current project week, except the one-time history initialisation. The project's first successful 「AI 整理」 SHALL classify every unassigned material and fill snapshots that are missing for active workstreams from archived reports of the last eight weeks; every later run SHALL only classify materials created this week and refresh this week's snapshots and follow-up TODOs.

#### Scenario: Manual snapshot for a past week
- **WHEN** a writer records a snapshot for a week before the current one
- **THEN** the system rejects it as locked and keeps that week unchanged

#### Scenario: Incremental organisation
- **WHEN** 「AI 整理」 runs for a project that was organised before
- **THEN** only unassigned materials created this week are classified, past snapshots are left as they are, and the job summary starts with 本周

### Requirement: Workstream TODOs
The system SHALL keep a workstream's follow-ups as ordinary TODOs linked to it (the former 待跟踪项 are migrated: each open item becomes an open TODO, done items are dropped). TODOs SHALL stay private to their account: the workstream view SHALL show a viewer their own linked TODOs, and the project owner SHALL also see the members' linked TODOs read-only. A member with upload access SHALL be able to add a TODO from the workstream view, which lands on their own TODO board linked to the workstream. 「AI 整理」 SHALL add follow-ups found in the current week's evidence as TODOs (marked AI 整理, skipping titles that match a TODO already linked to the workstream) on the board of the workstream 负责人's account when that account can open the project, else of the project owner, and SHALL close only its own TODOs that nobody has edited; a person's title or description edit SHALL take a TODO out of the agent's hands. TODOs carry no due date and raise no warnings.

#### Scenario: Agent follow-up
- **WHEN** this week's evidence for a workstream mentions a new follow-up
- **THEN** 「AI 整理」 adds it as an AI TODO on the 负责人's (or project owner's) board linked to the workstream, and a later run that sees it finished closes it while manual or edited TODOs stay open

#### Scenario: Owner sees members' TODOs
- **WHEN** a member links one of their TODOs to a workstream
- **THEN** the project owner sees it read-only in the workstream view while other members do not

### Requirement: Visual progress view
The 工作线 tab SHALL offer a progress view, the default, next to the week matrix: a summary of workstream health counts, current-week progress and open linked TODOs, and one lane per workstream covering the last eight weeks plus the future weeks up to the latest target or milestone date (at least 4, at most 26), with past weeks colored by snapshot status, milestone and target markers placed by date, a today line, and linked-TODO completion (counting the TODOs the viewer may see).

#### Scenario: Reading the progress view
- **WHEN** a member opens the 工作线 tab
- **THEN** each workstream shows its weekly status lane, upcoming milestones and target date against today, and how many linked TODOs are open

### Requirement: Sub-workstreams
The system SHALL let a top-level workstream hold sub-workstreams (子工作线) of the same project, one level deep: a sub-workstream SHALL NOT have children, a workstream with children SHALL NOT be placed under another, and names SHALL stay unique across both levels. Sub-workstreams SHALL carry their own links, snapshots, TODOs, milestones and warnings. An active parent's displayed health SHALL be the worst of its own and its active children's, naming the children that pulled it down, and a parent's staleness SHALL count material linked to its children. Deleting a parent SHALL turn its children into top-level workstreams. Closing a workstream (status done, shown as 已关闭) SHALL also close its open children, and reopening or creating an open child under a closed parent SHALL reopen the parent, so an open line never sits under a closed one. Lists SHALL show children right under their parent (`parent / name` as the path), the progress view and matrix SHALL let a viewer fold a parent's children, a parent's sources filter SHALL include its children's materials, and the agent SHALL prefer the most specific line when classifying and summarise a parent across its children without copying their follow-ups.

#### Scenario: Nesting depth
- **WHEN** a writer tries to create a workstream under a sub-workstream
- **THEN** the system rejects it

#### Scenario: Close and reopen a parent
- **WHEN** a writer closes a parent workstream and later reopens one of its sub-workstreams
- **THEN** closing marks the parent and all its children 已关闭, and reopening the child makes the parent active again while its other children stay closed

#### Scenario: Parent rolls up a child at risk
- **WHEN** a sub-workstream's target date has passed
- **THEN** the sub-workstream and its parent both show 受阻, and only the sub-workstream raises the warning

### Requirement: Project plan tab and project risks
The project's 总览 tab SHALL hold the risk list, and the project plan SHALL live in its own 项目计划 tab, which SHALL also list every workstream's milestones read-only with a link to their workstream. Each milestone SHALL have a stable id and belong to one workstream or to the project: a workstream's milestones SHALL be added, edited, completed, moved or deleted in its detail panel, and the 项目计划 tab SHALL edit the objectives, project-level milestones (assigning one to a workstream moves it there) and deliverables without touching workstream milestones. The 风险提醒 panel SHALL list this week's deterministic warnings with the project progress status, linking workstream warnings to their workstream. An overdue milestone of an active workstream SHALL be reported only by `workstream_overdue`; `overdue_milestone` SHALL cover project-level milestones and those of inactive workstreams.

#### Scenario: Move a project milestone into a workstream
- **WHEN** a writer picks a workstream for a project-level milestone in 项目计划
- **THEN** the milestone moves to that workstream's detail and timeline and leaves the project-level list, showing under 工作线里程碑 in 项目计划

#### Scenario: One warning per overdue milestone
- **WHEN** a milestone of an active workstream passes its date unfinished
- **THEN** the risk list shows the workstream's overdue warning and no separate milestone warning

### Requirement: PR and issue activity per workstream
The system SHALL sync, for each connected repository with its PR or issue switch on, the pull/merge requests and issues updated in the current project week during 「AI 整理」, and SHALL store those the report run already fetched without new remote calls. Each item SHALL be linked to at most one workstream: a person's choice first (kept for later weeks), else an earlier agent link, else the repository's default workstream, else the internal agent's classification. Linked items SHALL be snapshot and follow-up evidence, SHALL count as activity for the staleness rule, and SHALL be listed in the workstream detail and per-week lanes; unlinked items of the week SHALL be listed for manual assignment.

#### Scenario: Repository default
- **WHEN** a repository has a default workstream and one of its PRs is merged this week
- **THEN** 「AI 整理」 links the PR to that workstream and the week's snapshot can cite it as progress

#### Scenario: Manual choice survives
- **WHEN** a writer moves an issue to another workstream
- **THEN** later syncs keep that link even if the repository default changes

### Requirement: Project team members
The system SHALL keep a per-project team (项目组成员) in the project settings. A member SHALL be either linked to an enabled account (its name defaulting to the username) or a free-text name for someone without an account; names SHALL be unique within the project and an account SHALL appear at most once. Every project member SHALL see the team; only managers SHALL add, rename or remove members and change or drop a member's linked account. A workstream's owner SHALL be chosen from the project's members; renaming a member SHALL rename the owner everywhere it is shown, and removing a member SHALL leave the workstreams it owned without an owner. Free-text owner labels from older data or clients SHALL be matched to, or create, a member of that name, linking an account whose username matches exactly.

#### Scenario: Pick a workstream owner from the team
- **WHEN** a writer edits a workstream
- **THEN** the owner field offers the project's members and stores the chosen member

#### Scenario: Migrate free-text owners
- **WHEN** the service starts on data whose workstreams carry free-text owner labels
- **THEN** each distinct label becomes a project member once and the workstreams point at it

#### Scenario: Rename or remove a member
- **WHEN** a manager renames a member or removes it from the team
- **THEN** the workstreams it owns show the new name, or no owner after removal
