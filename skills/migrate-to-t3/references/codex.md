# Codex migration reference

## Treat the rollout as the source of truth

- Read active transcripts from `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-<timestamp>-<uuid>.jsonl`.
- Read archived transcripts from `$CODEX_HOME/archived_sessions/rollout-<timestamp>-<uuid>.jsonl`.
- Default `CODEX_HOME` to `~/.codex` only when the environment does not set it.
- Treat each rollout JSONL as the authoritative transcript for one destination thread.
- Treat `state_5.sqlite`, its WAL files, `sqlite/codex-dev.db`, and `sqlite/codex-history-snapshots-dev.db` as derived indexes or caches.
- Treat `session_index.jsonl` as an append-style thread-name index, not as a transcript.
- Treat `history.jsonl` and `transcription-history.jsonl` as composer history, not as thread history.

## Parse without losing information

- Stream JSONL one complete line at a time and preserve source order.
- Require the first record to be a `session_meta` object before accepting a rollout.
- Use the first `session_meta.payload.id` as the source thread ID.
- Validate that the filename UUID matches the first metadata ID, and quarantine mismatches for review.
- Do not replace the thread ID with a later `session_meta`; forked and multi-agent histories can contain metadata for other threads.
- Preserve unknown outer record types and unknown payload fields for forward compatibility.
- Preserve `session_meta`, `turn_context`, `response_item`, `event_msg`, `compacted`, `world_state`, and inter-agent metadata.
- Pair tool calls and outputs by `call_id`, not by adjacency alone.
- Treat `response_item` messages as canonical conversation items when transforming records.
- Treat mirrored `event_msg` user and agent messages as activity metadata, and do not emit duplicate visible turns.
- Preserve compaction records and their replacement history instead of expanding or discarding them speculatively.
- Preserve timestamps, encrypted fields, model settings, sandbox settings, Git metadata, and parent or fork relationships.

## Make imports idempotent

- Compute a SHA-256 digest of each complete source rollout before import.
- Key the import ledger by provider, canonical source path, source thread ID, source modification time, digest, and destination thread ID.
- Skip an import when the canonical source path and digest already map to a valid destination thread.
- Allocate destination IDs through the supported T3 import operation.
- Never reuse a foreign UUID without checking every active and archived destination thread for collisions.
- Persist source-to-destination ID mappings before resolving parent, child, and fork edges.
- Resolve relationship edges only after all referenced threads have destination IDs.
- Never overwrite an existing destination thread when an ID or path collision occurs.
- Stage a changed source as a new candidate unless prefix validation proves that it only appended complete records.

## Discover projects and folders

- Read the saved working directory from the first `session_meta.payload.cwd`.
- Use `state_5.sqlite.threads.cwd` only as a discovery hint when the rollout metadata is unavailable.
- Read desktop project roots and thread assignments from `.codex-global-state.json` only when migrating T3 project organization.
- Map a thread to the longest canonical destination project root that contains its remapped working directory.
- Record an explicit old-root to new-root mapping before rewriting home directories or mounted-volume paths.
- Keep a thread projectless when no verified destination root contains its working directory.
- Detect `$CODEX_HOME/worktrees/<id>/<repo>` paths and map them to a verified repository or recreated worktree.
- Do not copy linked Git worktree directories as ordinary folders.

## Preserve archive state

- Keep rollouts found under `archived_sessions` archived in the T3 thread model.
- Keep dated-tree rollouts active unless the source catalog and file location disagree.
- Stop and report archive disagreements instead of guessing.
- Use supported archive and unarchive APIs or CLI commands after import.
- Do not simulate archive state by moving files or editing SQLite rows directly.

## Migrate attachments deliberately

- Inventory `$CODEX_HOME/attachments/<uuid>/` and `attachments/pasted-text-attachments.json` separately from rollouts.
- Find attachment references in local image, local audio, pasted-text, and other file-path fields.
- Copy only referenced files that are within explicitly authorized source roots.
- Hash copied attachments and reuse an existing destination object only when its digest matches.
- Rewrite absolute attachment paths only after the destination copy succeeds.
- Preserve the transcript and mark the attachment unavailable when the source file is missing.
- Never print attachment contents, pasted text, audio, images, or sensitive paths in routine logs.
- Keep required absolute paths only in the private migration plan.

## Track a safe resume cursor

- Treat the last complete JSONL line as the source ingestion boundary.
- Store source byte size, complete-line count, digest, and last imported record identity in the migration ledger.
- Validate that all bytes before the stored boundary are unchanged before incrementally importing appended records.
- Perform a full staged reimport when the source changed before the stored boundary.
- Use rollout order and compaction semantics to reconstruct model history.
- Use `recency_at_ms` or file modification time only for picker ordering, never as a transcript cursor.
- Let Codex choose the resumed working directory through `tui.resume_cwd`, explicit `-C`, or the interactive prompt.

## Enforce hard safety rules

- Inventory and validate everything in read-only mode before writing.
- Stop T3 Code, Codex CLI, and app-server writers before taking the migration snapshot.
- Use a stable read-only source snapshot when providers cannot be quiesced.
- Never edit or copy live SQLite, WAL, SHM, backfill-state, timeline-ledger, or writer-lock files into place.
- Never migrate `auth.json`, credentials, logs, shell snapshots, IPC state, caches, or process-manager state.
- Migrate skills, plugins, configuration, and worktrees only under separate explicit authorization.
- Never delete, rename, truncate, or mutate source sessions.
- Never overwrite unrelated destination projects, threads, attachments, or user state.
- Produce a dry-run manifest with counts, mappings, collisions, skipped items, missing attachments, and validation errors.
- Require a clean second dry run with no unexpected changes before applying the migration.
- Let the supported T3 import operation update events, projections, receipts, and provider state atomically.
- Verify imported threads read-only before allowing resume or deleting any staging copy.
