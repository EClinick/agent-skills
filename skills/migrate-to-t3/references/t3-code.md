# T3 Code target rules

## Storage model

Treat the T3 server as the owner of projects, threads, provider sessions, and workspace state.
Treat clients as RPC consumers.

Use the configured T3 home rather than assuming `~/.t3`.
Expect canonical live data beneath its `userdata` directory, including `state.sqlite` and `attachments`.
Do not treat Electron data under `Library/Application Support/t3code` as project or conversation history.

Treat `orchestration_events` as canonical history.
Treat project, thread, message, activity, turn, and session tables as projections.
Treat provider runtime state as a separate durable binding between a T3 thread and a provider-native session.

## Capability gate

Inspect the current contracts or server RPC surface before applying a plan.
Require schema validation, transactional event creation, projection updates, idempotency, and error reporting from the target operation.

Allow project-only migration through a current public project-creation operation.
Require a versioned historical import operation for session migration.
Require that operation to support provider provenance and optional resume cursors.
Require a destination dry run that reconciles existing threads, provider bindings, and a durable import ledger.

Fail closed when the capability is absent.
Do not write directly to `state.sqlite`, `orchestration_events`, projection tables, command receipts, projector cursors, or provider runtime tables.
Do not copy a live SQLite file without its WAL state.

## Normalized import contract

Require the target operation to accept or derive these project fields:

- Stable import key
- Display title
- Canonical `workspace_root`
- Source providers
- Created and updated timestamps when available

Require each imported thread to retain:

- Source provider and provider instance
- Native session ID
- Source path and source fingerprint
- Import batch ID
- Canonical project path
- Title and timestamps
- Branch or worktree metadata when verified
- Finalized visible messages
- Normalized activities
- Attachment metadata
- Optional validated resume cursor

Generate deterministic import identities from the provider, native session ID, and native record identity.
Make an unchanged rerun produce zero mutations.
Allow a growing source transcript to append only unseen native records.
Do not treat the bundled source inventory as an exact apply plan.

## Provider bindings

Keep display history and provider resumption independent.
Imported messages do not give the provider its original context.
A resume cursor does not reconstruct missing T3 display history.

Use `{ "threadId": "<native-id>" }` for a validated Codex resume cursor.
Use the current Claude adapter cursor shape with the native Claude UUID for a validated Claude Code resume cursor.
Bind only to an existing configured T3 provider instance.
Import the thread as stopped and display-only when native state is unavailable.

## Messages and activities

Import one final non-streaming record per historical visible message.
Preserve source ordering and native record identity.
Map tool calls, tool results, tasks, plans, and provider lifecycle records to activities only when the mapping is meaningful.
Retain unsupported metadata as provenance rather than displaying it as chat.
Never expose hidden thinking or encrypted reasoning.

Do not synthesize historical checkpoint references or diff blobs.
Start normal T3 checkpointing with the first post-import turn.

## Attachments

Validate every attachment against current T3 type, MIME, size, ID, and filename rules.
Copy only referenced files that still exist and are owned by the selected source session.
Hash-deduplicate copied content.
Record an unavailable marker rather than retaining a broken absolute path.

## Apply and verify

Prefer a staging T3 home for any substantial import.
Require stable source fingerprints between plan and apply.
Create projects before dependent threads.
Apply atomically per thread and retain an import batch ID.

Verify materialized project, thread, message, activity, attachment, and provider-binding counts.
Inspect representative UI history when browser access is available.
Rerun the same plan and require zero changes.
Use only rollback behavior provided by the versioned import capability.
Never invent rollback by deleting database rows.
