## ADDED Requirements

### Requirement: Weekly progress update capture
The system SHALL allow a user to record progress updates for a project week, including completed work, in-progress work, blockers, risks, and next steps.

#### Scenario: Save weekly progress update
- **WHEN** a user submits a progress update for the current project week
- **THEN** the system stores the update and makes it available for weekly report generation

#### Scenario: Edit weekly progress update
- **WHEN** a user edits an existing progress update for the same project week
- **THEN** the system saves the revised update and marks the project week as having changed input

### Requirement: Supplement snapshot and history
The system SHALL snapshot the current week's supplement into the weekly report row at each successful generation and expose past weeks' supplements as history synced with the reports.

#### Scenario: Snapshot supplement on generation
- **WHEN** a weekly report generation succeeds for a project week that has a supplement
- **THEN** the system stores that week's supplement content alongside the report content

#### Scenario: Refresh snapshot on regeneration
- **WHEN** the same project week's report is regenerated after the supplement changed
- **THEN** the system replaces the stored supplement snapshot with the supplement used by the new generation

#### Scenario: Archive exposes generation-time supplement
- **WHEN** a user expands a historical weekly report
- **THEN** the system shows the supplement snapshot taken at that report's generation, or nothing for reports generated before snapshots existed

#### Scenario: List supplement history
- **WHEN** a user opens the weekly supplement view
- **THEN** the system lists past weeks' supplements newest first, excluding the current week, bounded to a recent window

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

#### Scenario: Confirm generation from project row
- **WHEN** the workspace user activates a project's report-generation icon
- **THEN** the system presents an application-styled confirmation message box, selects that project if needed after confirmation, and only then creates the manual generation job

#### Scenario: Keep page content free of generation actions
- **WHEN** the user views the project header, overview, or report page
- **THEN** manual generation and schedule-check buttons are absent because generation is available from the project row

#### Scenario: Manually force regeneration without changed inputs
- **WHEN** the workspace user triggers manual report generation and no relevant source input has changed since the last successful report generation
- **THEN** the system still creates a report generation job for the same project week

#### Scenario: Manual regeneration overwrites visible report
- **WHEN** a manually triggered regeneration completes successfully for the current project week
- **THEN** the system replaces the visible project-week report content with the new Markdown report

#### Scenario: Refresh visible report after manual regeneration
- **WHEN** a manual generation or regeneration request finishes
- **THEN** the report UI immediately renders the returned current workspace state without requiring a browser refresh

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

#### Scenario: Export weekly report as PDF
- **WHEN** a user chooses to export a current or historical weekly report as PDF
- **THEN** the system generates or reuses a cached PDF for that report and returns it as a downloadable file

### Requirement: Manual edit of the current weekly report
The system SHALL allow the workspace user to edit the Markdown body of the current project week's generated report in place, while historical weekly reports stay read-only.

#### Scenario: Save a manual report edit
- **WHEN** the workspace user saves an edited Markdown body for the current project week's report
- **THEN** the system stores the edited content, marks the report as manually edited, and renders the edited content in the workspace

#### Scenario: Regeneration overwrites manual edits
- **WHEN** the current project week's report is regenerated after a manual edit
- **THEN** the system replaces the report content with the generated Markdown and clears the manual-edit mark

#### Scenario: Confirm regeneration warns about manual edits
- **WHEN** the workspace user confirms generation for a project whose current week report is marked as manually edited
- **THEN** the confirmation dialog states that regeneration will overwrite the manual changes

#### Scenario: Editing is restricted to the current week
- **WHEN** an edit request targets any week other than the project's current week
- **THEN** the system rejects the request and keeps the historical report unchanged


### Requirement: Weekly report assistant Q&A
The system SHALL provide a 助手问答 side panel in the weekly report workspace for free-form questions about the current week's report, progress, problem causes and conclusions. The internal agent SHALL start from the current report and fetch further evidence on demand through project-scoped read-only tools. Each account SHALL keep its own conversation per project week. Revised reports SHALL never replace the report without an explicit apply by a project writer.

#### Scenario: Ask about this week's progress
- **WHEN** a project reader asks the assistant a question about the current week
- **THEN** the system answers from the report and current-week evidence, cites the evidence sources it relied on, and states when the evidence has no relevant record

#### Scenario: Evidence is fetched on demand
- **WHEN** a question can be answered from the current report
- **THEN** the assistant answers without calling tools or remote Git APIs
- **AND** questions about history, materials, plans, supplements, risks, commits or PRs call only the matching tools (weekly list/show, search, material/report/TODO show, materials list, plan, weekly supplement, risks, Git repos/commits/activity), whose results are bounded and limited to the project and the asking account, and the answer lists the tools it consulted

#### Scenario: Stream an answer
- **WHEN** a user asks the assistant a question
- **THEN** the answer runs in the background and streams to the panel as resumable server-sent events, showing each tool call as it starts and finishes and the answer text as it is generated
- **AND** tools requested in the same model round run concurrently, the user can stop the run, a page reload reattaches to it, and a second question waits until the first run ends

#### Scenario: Show the work log
- **WHEN** the assistant thinks or calls tools while answering
- **THEN** the panel lists thinking segments, raw tool calls and interim notes in order with live timers and final durations, marks failed calls, lets each tool call expand to its input and a result excerpt, and keeps the log with the stored answer

#### Scenario: Adjust a report conclusion
- **WHEN** a user asks the assistant to change a conclusion of the current week report
- **THEN** the answer explains the change and offers a revised report that leaves the stored report unchanged until applied
- **AND** a follow-up adjustment builds on the latest unapplied revision

#### Scenario: Apply a revision
- **WHEN** a project writer applies a revision from their own current-week conversation
- **THEN** the system replaces the current week report with the revision, marks it manually edited, and records the revision as applied
- **AND** read-only collaborators, other accounts' revisions, and revisions from earlier weeks cannot be applied

#### Scenario: Conversations stay private to the account and week
- **WHEN** another collaborator opens the panel, or the project week changes
- **THEN** the panel shows only that account's conversation for the current week

#### Scenario: Assistant call fails
- **WHEN** the internal agent is not configured or the call fails
- **THEN** the system shows the failure and stores neither the question nor an answer

### Requirement: Shared operation registry
The system SHALL define each project, material, report, TODO, search and Git operation once, with a name, description, JSON-Schema parameters, a read-only annotation and a single handler, and SHALL expose that definition through the HTTP API, the zreport CLI and the report assistant's tools without separate per-interface implementations.

#### Scenario: Discover operations
- **WHEN** a client requests the operation manifest
- **THEN** the system returns every operation with its parameters, read-only annotation, CLI command path and rendering hint, without requiring a session

#### Scenario: CLI follows the server
- **WHEN** the zreport CLI starts
- **THEN** it builds its server commands from the manifest, caches it per server for offline help, and runs commands through the operation endpoint
- **AND** it reports clearly when no manifest is available instead of failing as an unknown command

#### Scenario: Same result through every interface
- **WHEN** the same read-only operation runs through the HTTP API, the CLI and the assistant for the same project
- **THEN** each returns the same data, apart from agent-only output bounds

#### Scenario: Access follows the operation
- **WHEN** an operation names a project
- **THEN** the system resolves it by ID or exact name among the caller's accessible projects and requires the operation's project role
- **AND** assistant calls are pinned to the conversation's project, cannot reach other projects' records and can use only read-only operations

### Requirement: Excel material extraction and original downloads
The system SHALL accept XLSX and XLS uploads, extract worksheet names and cell text without executing formulas, and retain original bytes. The system SHALL also accept DOCX and Word 97-2003 DOC uploads, extracting body text with standard-library parsers bounded to 2000000 text characters and, for DOCX, 64 MiB of expanded data. Extraction SHALL be bounded to 200000 cells and 2000000 text characters, with XLSX expanded data bounded to 64 MiB. A failed extraction SHALL preserve the original and display the failed file in the material list. Downloads SHALL require project read access and return an attachment with the original UTF-8 filename, including for historical and failed files.

#### Scenario: Upload an Excel workbook
- **WHEN** a project writer uploads a supported Excel file with multiple worksheets
- **THEN** its extracted text contains worksheet names and row values for preview, summaries and weekly report evidence

#### Scenario: Upload a Word document
- **WHEN** a project writer uploads a DOCX or Word 97-2003 DOC file
- **THEN** its extracted text contains the body paragraphs in order, DOCX headings and list items marked in Markdown, and table rows tab-separated
- **AND** an encrypted, Word 6/95, empty or corrupt document, or a DOCX part carrying a DTD, is marked failed while its original stays downloadable

#### Scenario: Download an original file
- **WHEN** a project reader downloads an uploaded file, including an archived or extraction-failed upload
- **THEN** the system returns the original bytes with an attachment filename
- **AND** accounts without project access cannot download it

### Requirement: Image material recognition
The system SHALL accept PNG, JPEG, GIF and WebP uploads whose file signature matches a supported raster format, store the sniffed media type rather than the client-declared one, and reject SVG or mismatched content before storing anything. The internal agent SHALL recognise images up to 5 MiB with an administrator-configured image recognition model that shares the LLM key and, unless an optional OpenAI-compatible image recognition endpoint is configured, the LLM provider and endpoint, producing Markdown with the image's visible text and an objective description as the extracted text for summaries and weekly report evidence. A recognition failure SHALL preserve the original and mark extraction failed. Image previews SHALL be served inline only with the stored image media type under project read access.

#### Scenario: Upload a screenshot
- **WHEN** a project writer uploads a supported image
- **THEN** its recognised text and description appear in the preview below the image and feed summaries and report evidence

#### Scenario: Reject a disguised file
- **WHEN** an upload has an image extension but non-image content, or is an SVG
- **THEN** the system rejects the upload and stores no file or material record

#### Scenario: Recognition is unavailable
- **WHEN** no image recognition model is configured, the image exceeds 5 MiB, or the model rejects image input
- **THEN** the material is stored with failed extraction and stays previewable and downloadable

### Requirement: Local file cold storage
The system SHALL allow administrators to configure and enable a local absolute cold-storage directory independently of full backups. The scheduler SHALL check hourly and transfer uploaded originals strictly older than one calendar month in Asia/Shanghai, clamping the day at month end. Administrators SHALL also be able to trigger a scan and view the latest scan time, transferred count and errors. Unconfigured cold storage SHALL be disabled by default.

#### Scenario: Safely transfer an aged upload
- **WHEN** a file is older than the calendar-month cutoff and cold storage is enabled
- **THEN** the system copies the original to a project/material-specific location, verifies size and SHA-256, commits its new path and archive root, and only then removes an unreferenced hot copy
- **AND** extraction text, material timestamps, preview, project permissions and download behavior remain intact

#### Scenario: A transfer fails
- **WHEN** a cold-storage copy, verification or database update fails
- **THEN** the hot original remains accessible and the scan records an error, with retry available on a subsequent scan

#### Scenario: Change storage configuration
- **WHEN** the administrator changes the cold-storage directory or disables future transfers
- **THEN** previously archived originals remain accessible at their recorded locations
- **AND** cold storage cannot overlap application data or a full-backup target

#### Scenario: Back up cold originals
- **WHEN** a full backup is taken after files have been transferred
- **THEN** it includes all referenced cold originals and a manifest of their original storage paths
- **AND** a missing cold original fails the backup rather than producing an incomplete successful backup

### Requirement: Compressed full backups
The system SHALL produce full backups as DEFLATE-compressed ZIP archives named using China time. Each archive SHALL include a consistent SQLite snapshot, uploaded files and referenced cold originals with their restore manifest. The recorded backup size SHALL be the archive size in bytes.

#### Scenario: Complete and restore a compressed backup
- **WHEN** an administrator or the scheduler starts a full backup
- **THEN** the system stages the snapshot locally and publishes one completed ZIP in the configured target
- **AND** extracting that ZIP provides reports.sqlite3, uploads and any cold originals and manifest at their existing restore paths
- **AND** a failed snapshot, copy, compression or publication leaves no completed archive or temporary files from that attempt

#### Scenario: Retain backups across a format upgrade
- **WHEN** a successful backup exceeds the configured retention count
- **THEN** the newest backups are retained across ZIP archives and legacy directories together
- **AND** timestamp collision suffixes are ordered numerically, with unrelated files and symbolic links untouched

### Requirement: Global settings tabs
The global settings workspace SHALL use a horizontal tab strip to display one settings section at a time. It SHALL preserve form contents while switching tabs and show only sections permitted for the current account.

#### Scenario: Navigate settings on desktop and mobile
- **WHEN** a user opens global settings or selects a section
- **THEN** the selected tab and its associated panel are active, with other panels hidden
- **AND** narrow screens scroll the tab strip horizontally without wrapping it or widening the page
- **AND** keyboard users can navigate tabs using Left, Right, Home and End

#### Scenario: Apply account permissions to tabs
- **WHEN** settings are loaded for a regular user
- **THEN** only appearance, Git integration and password tabs are available
- **AND** an unavailable selected administrator tab falls back to appearance
