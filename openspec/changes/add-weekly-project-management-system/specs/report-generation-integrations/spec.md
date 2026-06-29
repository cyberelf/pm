## ADDED Requirements

### Requirement: Report provider abstraction
The system SHALL support CLI-based weekly report generation through provider adapters.

#### Scenario: Generate with configured provider
- **WHEN** a report generation job starts for a project
- **THEN** the system invokes the project's configured CLI provider adapter

#### Scenario: Reject unsupported provider
- **WHEN** a project references an unsupported report provider
- **THEN** the system marks the generation job as failed with an unsupported provider error

### Requirement: Codex CLI provider
The system SHALL support Codex CLI as a weekly report generation provider.

#### Scenario: Invoke Codex CLI
- **WHEN** a project is configured to use Codex CLI and a report job starts
- **THEN** the system invokes Codex CLI with the project report context and system prompt

### Requirement: Claude Code CLI provider
The system SHALL support Claude Code CLI as a weekly report generation provider.

#### Scenario: Invoke Claude Code CLI
- **WHEN** a project is configured to use Claude Code CLI and a report job starts
- **THEN** the system invokes Claude Code CLI with the project report context and system prompt

### Requirement: Report context assembly
The system SHALL assemble a report context snapshot before invoking a report provider.

#### Scenario: Build report context
- **WHEN** a report generation job starts
- **THEN** the system includes project metadata, current plan baseline, weekly planned outcomes, manual weekly updates, current-week newly uploaded or manually entered material summaries, current-week Git commits for connected repositories, GitHub activity summaries, prior current-week report content if any, the project system prompt, and the effective report template in the context snapshot

#### Scenario: Include material extraction status
- **WHEN** a report generation job starts and a project material has not produced extractable text
- **THEN** the system includes the material metadata and extraction status in the report context without blocking report generation

### Requirement: Default report template
The system SHALL provide a default Markdown weekly report template when a project does not configure its own template.

#### Scenario: Apply default report template
- **WHEN** a report generation job starts for a project without a project-specific report template
- **THEN** the system uses a default Markdown template containing sections for this week's summary, completed work, in-progress work, blockers and risks, risk forecast, next week plan, GitHub activity summary, and source/input references

#### Scenario: Apply project-specific report template
- **WHEN** a report generation job starts for a project with a project-specific report template
- **THEN** the system uses the project-specific template instead of the default template

### Requirement: Platform-mediated provider handoff
The system SHALL invoke CLI report providers through a temporary working directory and expose project information through a read-only platform context CLI.

#### Scenario: Provide context through platform CLI
- **WHEN** a report generation job starts
- **THEN** the system prompts the CLI provider to retrieve project information only through the platform context CLI

#### Scenario: Prevent direct source access
- **WHEN** a CLI provider generates a report
- **THEN** the system instructs the provider not to read SQLite, uploaded files, application files, GitHub, or `gh` directly

#### Scenario: Read Markdown output from temporary file
- **WHEN** a CLI provider exits successfully
- **THEN** the system reads the Markdown report from the expected temporary output file and stores it as the generation job output

#### Scenario: Fail when output file is missing
- **WHEN** a CLI provider exits successfully but the expected output file is missing or empty
- **THEN** the system marks the generation job as failed with an output file error

#### Scenario: Prevent direct application data writes
- **WHEN** a CLI provider generates a weekly report
- **THEN** the system persists only the Markdown output it reads from the temporary output file

### Requirement: Generation job status
The system SHALL track report generation job status, trigger type, timestamps, provider, input snapshot identity, output, and failure details.

#### Scenario: Complete generation job
- **WHEN** a CLI provider returns a Markdown report successfully
- **THEN** the system marks the job successful, stores the output, and updates the current weekly report

#### Scenario: Fail generation job
- **WHEN** a CLI provider exits unsuccessfully or times out
- **THEN** the system marks the job failed and stores diagnostic failure details

#### Scenario: Record generation trigger type
- **WHEN** a scheduled or manual report generation job is created
- **THEN** the system records whether the job was triggered by schedule or by the workspace user

### Requirement: Generation history visibility
The system SHALL show the workspace user generation run history for a project week without displaying old report bodies by default.

#### Scenario: View generation run history
- **WHEN** a user views generation history for a project week
- **THEN** the system displays each run's trigger type, timestamp, provider, status, failure reason if any, and input snapshot identity or covered time range

#### Scenario: Hide old report body by default
- **WHEN** a user views generation history for a project week
- **THEN** the system does not display previous generated report bodies as separate visible report versions by default

### Requirement: Provider execution controls
The system SHALL execute CLI providers with configured timeouts and bounded input/output handling.

#### Scenario: Provider timeout
- **WHEN** a CLI provider exceeds the configured timeout
- **THEN** the system terminates the provider process and marks the generation job as timed out
