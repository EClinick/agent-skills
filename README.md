# Ethan Clinick's Agent Skills

[![skills.sh](https://skills.sh/b/EClinick/agent-skills)](https://skills.sh/EClinick/agent-skills)

Reusable workflows for Codex and other Agent Skills-compatible coding agents.

## Available skills

### `ship`

Runs a complete shipping loop for the current changes:

1. Inspect and validate the working tree.
2. Create a feature branch when needed.
3. Lint and test relevant changes.
4. Commit and push with a plain, human-written message.
5. Open or update a pull request.
6. Review the diff, fix valid findings, and repeat until clean.
7. Hand off a merge-ready pull request without merging unless explicitly authorized.

## Install

Install `ship` globally for Codex:

```bash
npx skills add EClinick/agent-skills --skill ship --agent codex --global
```

Or let the CLI prompt for an agent and installation scope:

```bash
npx skills add EClinick/agent-skills --skill ship
```

## Use

Invoke the installed skill in your coding agent:

```text
$ship
```

You can provide a base branch or flags supported by the skill:

```text
$ship main
$ship --no-review
$ship main --merge
```

`--merge` is the only invocation that pre-authorizes merging after the review is
clean. A normal `ship` request never authorizes a merge.
