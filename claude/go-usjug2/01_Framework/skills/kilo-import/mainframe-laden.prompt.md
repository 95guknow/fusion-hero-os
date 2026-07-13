# Prompt: mainframe laden

Purpose
- Assist with tasks related to “mainframe laden” (loading, transferring, or preparing data/workloads for a mainframe environment).

Scope
- Workspace-scoped helper prompt for repeatable tasks: generating load scripts, validation checks, transfer plans, data mapping, and run instructions targeted at mainframe environments (z/OS, JCL, FTP/SFTP, Connect:Direct, batch jobs).
- Not for deep platform administration or privileged credential exchange; assume the user will provide connection details and sensitive secrets out-of-band.

Inputs (explicit)
- `target`: target mainframe type or system (e.g., `z/OS`, `TN3270`, `Connect:Direct`).
- `source`: source artifact description (local file, lakehouse path, dataset name).
- `format`: data file format (e.g., `CSV`, `EBCDIC`, `FixedWidth`).
- `action`: desired outcome (e.g., `create JCL`, `generate transfer script`, `validate checksum`, `simulate load`).
- `credentials_note` (optional): placeholder text the assistant should leave where credentials must be inserted.

Outputs (format)
- Prefer concise actionable artifacts: a script (PowerShell/Bash/JCL), step-by-step runbook, data mapping table, and validation checklist.
- When producing code, include a short usage example and where to insert credentials (do not include real secrets).

Examples
- "Generate a JCL job to load EBCDIC-fixed-width file from SFTP to z/OS PDS, map fields A,B,C to DB2 columns X,Y,Z."
- "Create a PowerShell script to upload CSV to Connect:Direct and run post-load checksum validation."

Edge cases & constraints
- If `format` is `EBCDIC`, include encoding conversion steps and sample iconv commands.
- If `target` is ambiguous, ask for clarification before producing code.
- If `source` points to cloud storage, include temporary download steps and recommended CLI commands.

Follow-up questions the prompt should ask when needed
1. Which mainframe system exactly (z/OS, VSE, z/VM, or middleware)?
2. Do you want sample credentials placeholders or an integration with an existing credential store?
3. Is this a one-off transfer or an automated scheduled job?

Invocation template
"You are a DevOps engineer preparing to `{{action}}` from `{{source}}` to `{{target}}` in `{{format}}` format. Produce: (1) the scripts required, (2) a short runbook with commands to execute, and (3) a validation checklist. Leave credential placeholders as `{{CREDENTIALS_HERE}}`."

Notes
- Keep answers short and focused; prefer step lists over long prose.
- If the user asks in German, respond in German; otherwise match the user's language.

---

Status: Draft — please confirm what you mean by "mainframe laden" (uploading data, generating JCL, or scheduling batch jobs).
