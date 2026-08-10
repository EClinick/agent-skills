# Claude Code source reference

Use this reference when importing Claude Code folders and sessions into T3 Code.

## Locate the source

- Read primary transcripts from `~/.claude/projects/<project-key>/<session-uuid>.jsonl`.
- Treat each primary filename UUID as the source session ID, and confirm it against record `sessionId` values.
- Discover sessions by scanning primary JSONL files, not by reading `~/.claude/history.jsonl`.
- Treat `history.jsonl` as optional prompt-history metadata with `display`, `pastedContents`, `project`, `sessionId`, and `timestamp`.
- Ignore `~/.claude/sessions/<pid>.json` because it is a live-process registry, not historical session storage.
- Preserve the detected Claude Code version and unknown fields for forward compatibility.

## Resolve the project folder

- Resolve the destination folder from the latest valid `relocated.relocatedCwd`, then transcript `cwd`, then a matching history row `project`, then an explicit user mapping.
- Preserve both the lexical source path and its resolved real path when the source still exists.
- Represent a verified linked worktree as a thread `worktree_path` under its main repository project unless the user explicitly chooses a separate project.
- Never decode `<project-key>` back into a filesystem path.
- Remember that Claude replaces every non-ASCII-alphanumeric path character with `-`.
- Remember that Claude truncates keys over 200 characters and appends a hash.
- Treat the encoded key as lossy and potentially colliding.

## Parse the transcript

- Parse one JSON object per line and retain original append order as the stable tie-breaker.
- Reject or quarantine malformed interior lines.
- Ignore an incomplete trailing line only when a concurrent-write check confirms that the source is active.
- Distinguish conversational records from operational records such as `mode`, `permission-mode`, `last-prompt`, titles, queue operations, file-history records, and PR links.
- Map user and assistant `message.content` blocks by type, including `text`, `thinking`, `tool_use`, `tool_result`, and `image`.
- Preserve tool-use IDs and tool-result references so T3 can reconnect calls and results.
- Preserve timestamps as source metadata, but never sort the conversation by timestamp.

## Reconstruct branches

- Build a graph from record `uuid` and `parentUuid` values.
- Validate duplicate UUIDs, missing parents, cycles, multiple roots, and branch points before import.
- Select the latest valid `last-prompt.leafUuid` as the active leaf when present.
- Otherwise select the last valid conversation-bearing leaf in append order.
- Walk `parentUuid` from the selected leaf to a root, then reverse that chain for the canonical conversation.
- Preserve alternate branches as explicit branches or source-only provenance when T3 supports them.
- Never concatenate abandoned, retried, or rewound branches into the canonical conversation.
- Handle `system` records such as compaction boundaries and summaries without treating every system record as a visible chat message.

## Import titles and resume identity

- Prefer the latest `custom-title`, then the latest `ai-title` or `agent-name`, then the source session UUID.
- Preserve the Claude UUID as `sourceSessionId` and record `sourceProvider: claude-code`.
- Namespace source identity by provider and resolved project because UUID collisions across project directories are possible.
- Generate a T3-native session ID when the destination already contains that identity.
- Never overwrite an unrelated T3 session merely because its UUID matches.
- Do not claim that a T3 import remains resumable until the configured Claude provider validates the native UUID.
- Remember that Claude `--resume` requires a valid UUID and searches the current project, related worktrees, then a unique global match.

## Import subagents and workflows

- Read direct subagents from `<project-key>/<session-id>/subagents/agent-<agent-id>.jsonl`.
- Read optional adjacent `agent-<agent-id>.meta.json` files.
- Link a subagent to the parent tool call through metadata `toolUseId` when available.
- Preserve `agentId`, `parentAgentId`, `spawnDepth`, `agentType`, model, worktree metadata, and stopped state.
- Tolerate missing or minimal metadata from older sessions.
- Read workflow agents from `<session-id>/subagents/workflows/<workflow-id>/agent-*.jsonl`.
- Treat workflow `journal.jsonl` and `<session-id>/workflows/<workflow-id>.json` as workflow state, not ordinary chat turns.
- Keep subagent graphs separate from the primary graph unless T3 has an explicit nested-agent representation.
- Treat the bundled planner's subagent count as unsupported source inventory, not as planned activity or thread output.

## Handle attachments and auxiliary state

- Resolve inline image blocks and attachment records before consulting `~/.claude/image-cache` or `~/.claude/paste-cache`.
- Copy only assets proven to be referenced by an imported record.
- Verify asset size, type, checksum, and destination permissions before copying.
- Treat `~/.claude/file-history/<session-id>/` as optional file-restore history, not chat content.
- Treat `~/.claude/tasks/<session-id>/` as optional todo state.
- Treat `~/.claude/plans/` and `<project-key>/memory/` as separate folder context with no guaranteed session ownership.
- Exclude `session-env`, `shell-snapshots`, hooks, raw tool-result blobs, debug logs, and unreferenced caches by default.

## Enforce hard safety rules

- Keep every Claude source file read-only.
- Never rename, delete, truncate, repair, or append to Claude storage.
- Require Claude sessions to be quiescent, or take a stable snapshot with size and modification-time checks before and after reading.
- Retry a changing file instead of importing a mixed snapshot.
- Run an inventory and dry run before writing T3 data.
- Make reruns idempotent through a durable source-to-destination manifest.
- Require an explicit conflict policy before replacing any existing T3 record or asset.
- Process payloads locally and never log prompts, tool inputs, tool outputs, environment values, file-history contents, or credentials.
- Apply restrictive permissions to manifests, temporary snapshots, copied attachments, and destination records.
- Report skipped, malformed, ambiguous, active, and partially imported sessions without exposing their content.
