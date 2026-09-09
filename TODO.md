# TODO

Deferred work and known limitations, kept here so the README stays a usage
document. Newest items go last within a section.

## PDF text extraction

- Uploaded PDFs are stored and surfaced in report context with extraction
  status, but text extraction is currently always marked failed: the
  standard-library backend has no PDF parser yet (README → Uploads). Adding a
  small parsing dependency (for example `pypdf`) or invoking an external
  `pdftotext` would close this.
