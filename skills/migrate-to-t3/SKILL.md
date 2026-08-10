---
name: migrate-to-t3
description: Discover, plan, and execute migrations that the current T3 Code import surface supports for existing project folders and optional Codex or Claude Code session history. Use when a user asks to add or migrate projects, workspaces, Codex threads, or Claude Code conversations into T3 Code with path reconciliation, idempotency, resume-link validation, and post-import verification.
---

# Migrate to T3 Code

Plan every migration from read-only source data, then apply it only through a supported T3 import boundary.
Treat project registration, visible history, and native provider resumption as separate capabilities.
Use the bundled executable only to build plans because it never applies changes.
Expect provider-history application to stop safely when the installed T3 version lacks a supported historical import operation.

## Interpret the scope

Accept these invocation options:

- `--projects-only`: Register projects only.
  Do not create threads, messages, activities, attachments, or provider bindings.
- `--provider codex`: Import Codex sessions and their prerequisite projects.
- `--provider claude-code`: Import Claude Code sessions and their prerequisite projects.
- Repeat `--provider` to select both providers.
- Accept `--provider claude` as an alias for `claude-code`.
- `--project PATH`: Limit the plan to this project path.
  Accept the option more than once.
  Include sessions from verified linked worktrees that reconcile to the selected project.
- `--session ID`: Limit provider scope to this native or plan session ID.
  Accept the option more than once.
- `--include-archived`: Include archived Codex rollouts.
- `--claude-branches active|all`: Import only the active Claude branch by default.
- `--no-resume-links`: Import display history without adopting native provider sessions.

Treat `--projects-only` and `--provider` as mutually exclusive.
When no scope is supplied, inventory both providers and present choices without applying anything.
Provider selection includes prerequisite projects, but it does not authorize importing every discovered session.

## Build the plan

1. Locate T3, Codex, and Claude homes without exposing secrets.
2. Read [T3 target rules](references/t3-code.md).
3. Read [Codex source rules](references/codex.md) when Codex is selected or contributes project discovery.
4. Read [Claude Code source rules](references/claude-code.md) when Claude Code is selected or contributes project discovery.
5. Run the bundled planner from this skill directory:

```bash
python3 scripts/plan_migration.py --projects-only
python3 scripts/plan_migration.py --provider codex
python3 scripts/plan_migration.py --provider claude-code
python3 scripts/plan_migration.py --provider codex --provider claude-code
```

6. Add `--project`, `--session`, `--include-archived`, branch, home, or path-map options needed by the request.
7. Write a private plan only when useful by adding `--output <path>`.
8. Report projects, sessions, branches, message counts, unvalidated resume candidates, unsupported subagents, skips, unstable files, and path conflicts.

The planner reads metadata and content structure but never includes transcript bodies in its output.
Treat the resulting plan as sensitive because it contains absolute paths, titles, and source fingerprints.
Treat it as a source inventory, not as an exact apply plan.

## Reconcile projects

- Resolve transcript `cwd` or `relocatedCwd` to a canonical absolute path.
- Apply explicit path mappings before canonicalization.
- Deduplicate projects by canonical path, not basename or provider-encoded directory name.
- Reuse an existing T3 project whose canonical `workspace_root` matches.
- Leave project directories in place.
  Never copy or move repositories as part of registration.
- Skip missing paths by default and report them.
- Set `worktree_path` only when the source is verified to be a dedicated worktree.

## Check the target capability

Inspect the current T3 contracts or RPC surface before applying.
Do not infer support from database tables.

- For project-only plans, use the supported `project.create` operation or an equivalent current public API.
- For provider plans, require a versioned import operation that can atomically create historical messages and activities and optionally adopt provider resume state.
- Require the target operation to dry-run against its thread catalog, provider bindings, and import ledger and assign `create`, `append`, `skip`, or `conflict` to every selected session.
- If historical import is unavailable, stop before mutation and name the missing capability.
- Never add a raw SQLite, projection-table, orchestration-event, or provider-runtime fallback.

## Apply

Never apply the bundled planner's source-only inventory directly.
Apply only after the supported target operation has produced a destination-reconciled dry run and the user has explicitly authorized that exact plan.
Invalidate approval when a source fingerprint or path mapping changes.
Do not treat a provider plan as executable until the capability check succeeds.

1. Create or reuse projects before dependent threads.
2. Import finalized messages rather than streaming deltas.
3. Preserve native provider IDs as provenance while generating collision-safe T3 IDs.
4. Map meaningful tool and task records to activities without exposing hidden reasoning.
   Keep subagents unsupported unless the target dry run explicitly represents and counts them.
5. Mark historical checkpoint and revert support as unavailable.
6. Validate native session availability before installing a resume cursor.
7. Import attachments only after validating type, size, ownership, and source availability.
8. Record an import batch ID and idempotency keys.
9. Keep every Codex and Claude source file unchanged.

## Verify

After application:

1. Compare imported project, thread, message, activity, attachment, and skipped counts with the plan.
2. Inspect representative first and last visible messages without printing sensitive content into logs.
3. Verify every adopted provider binding against the intended provider instance.
4. Start one explicitly approved test turn only when the user authorizes sending a provider request.
5. Rebuild the same plan and require an unchanged rerun to produce zero mutations.
6. Report the batch ID, unavailable resume links, warnings, and supported rollback boundary.

## Hard gates

- Treat source stores as read-only.
- Never replay historical prompts to reconstruct context.
- Never expose transcript text, tool output, patches, secrets, or attachment contents in routine logs.
- Never import thinking or encrypted reasoning as visible messages.
- Never treat prompt history, caches, locks, shell snapshots, or file backups as conversation transcripts.
- Never mutate a live T3 SQLite store directly.
- Never claim a session is resumable until the native provider confirms the session exists.
- Never claim imported historical turns support T3 checkpoints or revert.
