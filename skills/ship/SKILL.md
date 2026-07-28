---
name: ship
description: Ship the current changes by linting, testing, committing, pushing, opening or updating a pull request, reviewing the diff, fixing valid findings, and repeating until the review is clean. Use when the user says /ship, "ship it", "ship this", or asks to run the commit-review-fix-merge loop.
---

# /ship - commit, review, fix, ship

Run the full shipping loop for the current working tree.
Arguments (all optional): a base branch (`/ship main`), `--no-review` to skip the Codex pass, `--merge` to pre-authorize merging once the review is clean.

## Phase 1: Preflight

1. `git status` and `git diff --stat` to see what is being shipped. Summarize it in one or two sentences for the user.
2. If on the default branch (main/master), create a feature branch first. Never commit directly to the default branch.
3. Run the project's lint/format command if one exists (check package.json, Makefile, and repository guidance). Fix any failures before proceeding.
4. If tests relevant to the changed files are cheap to run, run them now. Report failures instead of shipping them.

## Phase 2: Commit and push

Commit-message rules (hard requirements):

- NEVER add a co-author line or agent attribution of any kind.
- Write a plain, human-sounding message describing the change. Match the style of recent `git log` messages in the repo.

Then push the branch.

## Phase 3: PR

- If a PR already exists for this branch (`gh pr view`), update it; otherwise create one with `gh pr create`.
- PR body: what changed, why, and how it was verified. No AI attribution footers.

## Phase 4: Codex review loop

Skip this phase only if the user passed `--no-review`.

1. Trigger a Codex review of the diff using the codex plugin (`codex:rescue` agent or `/codex:rescue`), asking it to review the PR diff for correctness, security, and quality.
2. Triage every finding - do not blindly apply all of them:
   - **Valid**: fix it. Apply fixes one finding at a time, each as its own focused change, and tell the user what was fixed and why.
   - **Invalid/noise**: skip it and record a one-line reason. If the finding came in as a PR comment, reply to the comment explaining why it was skipped.
3. Commit and push the fixes (same commit rules as Phase 2).
4. Re-run the review. Loop until Codex has no new valid findings, up to 3 rounds. If findings persist after 3 rounds, stop and summarize the disagreement for the user instead of looping forever.

## Phase 5: Finish

- **Never merge without explicit approval.** Merge only if the user passed `--merge` up front or says so after seeing the clean review. "Ship" alone does NOT authorize merging.
- Final report: branch, PR link, lint/test status, review rounds, findings fixed vs skipped (with reasons), and whether it is ready to merge.

## Hard gates (override everything else)

- If the user says "don't commit", "audit only", or similar at any point, stop all write operations immediately and wait.
- Never force-push, never amend published commits, never merge or close PRs without explicit approval.
- If lint or tests fail and the fix is not obvious and small, report instead of shipping.
