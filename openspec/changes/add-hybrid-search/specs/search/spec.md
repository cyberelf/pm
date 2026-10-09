## ADDED Requirements

### Requirement: Hybrid search over reports and materials
The system SHALL provide a search endpoint over the account's generated weekly reports and material extracted text that combines keyword matching with optional vector similarity, returning up to a caller-specified number of fused results.

#### Scenario: Keyword search always available
- **WHEN** a signed-in user queries the search endpoint with a non-empty query
- **THEN** the system returns hits drawn from that account's weekly reports and materials with title, source type, project, snippet, and score, even when no embedding model is configured

#### Scenario: Vector half activates with an embedding model
- **WHEN** the administrator has set an embedding model in 全局设置
- **THEN** the search embeds the query against the configured OpenAI-compatible endpoint and fuses the vector ranking with the keyword ranking using reciprocal rank fusion, and the response reports mode "hybrid"

#### Scenario: Embedding failure does not fail the search
- **WHEN** the embeddings endpoint is unreachable or returns an error
- **THEN** the search still returns keyword results and reports the embedding error in the response instead of returning an HTTP error

### Requirement: Lazy incremental indexing
The system SHALL index searchable content lazily at query time: chunk texts on paragraph boundaries, store a hash of each chunk (including the embedding model name), embed only new or changed chunks within a per-request budget, and remove chunks whose source row was deleted or whose content changed.

#### Scenario: First search after new content
- **WHEN** a user searches after new weekly reports or materials were added
- **THEN** the system indexes and embeds up to the per-request budget of pending chunks before ranking, and later searches only process remaining or changed chunks

#### Scenario: Edited material invalidates old chunks
- **WHEN** a material's text or a report's markdown changes
- **THEN** the chunks whose stored hash no longer matches are removed before the search runs

#### Scenario: Switching the embedding model
- **WHEN** the administrator changes the embedding model setting
- **THEN** every stored chunk is re-embedded lazily by subsequent searches because the stored hashes include the previous model name

### Requirement: Search respects account isolation
The system SHALL limit search to projects owned by the authenticated account, treating another account's project id as an empty result rather than an error.

#### Scenario: Foreign project filter
- **WHEN** a user passes a project id owned by a different account
- **THEN** the search returns an empty hit list with a success status

### Requirement: CLI search command
The CLI SHALL provide `zreport search QUERY` with optional project scope (`-p`), result count (`-n`, default 10), source filter (`--type report|material`), and raw JSON output (`--json`).

#### Scenario: Search from the terminal
- **WHEN** a signed-in CLI user runs `zreport search "部署" -n 5`
- **THEN** the CLI prints a ranked table of hits and, when the vector half is disabled, a note explaining that an embedding model enables hybrid search

### Requirement: Hits are addressable and viewable in full
Search hits SHALL carry a unique per-type id (`source_id`), and the CLI SHALL provide `material show <ID>`, `report show <ID>`, and `todo show <ID>` that return the full content of the referenced item; the id-addressed server lookups SHALL enforce per-account isolation.

#### Scenario: Open a search hit in full
- **WHEN** a user runs `zreport material show <ID>` or `zreport report show <ID>` with an id from a search hit
- **THEN** the CLI prints the item's complete extracted text or rendered report content with its project and metadata

#### Scenario: Another account's id
- **WHEN** a user addresses an item owned by a different account by id
- **THEN** the lookup responds 404 instead of returning the content
