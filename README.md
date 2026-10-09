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

### `demo-workbench`

[Create and iterate on local demo videos](skills/demo-workbench/SKILL.md) from a
brief, reference video and optional soundtrack. The agent runs the CLI, edits the
scene, renders numbered versions, imports real reviews, and serves/stops the
existing gallery. Localhost is the default; tailnet access requires an explicit
request.

**Separate prerequisite:** [demo-workbench](https://github.com/EClinick/demo-workbench)
0.2.x is public and available on npm as
[`@eclinick/demo-workbench`](https://www.npmjs.com/package/@eclinick/demo-workbench)
(verified with 0.2.0). With installation approval:

```bash
npm install -g @eclinick/demo-workbench
```

Use `npm.cmd` in PowerShell. The executable remains `demo-workbench`
(`demo-workbench.cmd` in PowerShell). The unrelated unscoped npm package belongs
to someone else: never install it or invoke `npx demo-workbench`.
This public skill does not install the tool, distribute its application/gallery/media,
or grant redistribution rights. See the CLI's
[installation docs](https://github.com/EClinick/demo-workbench/blob/main/docs/installation.md)
for prerequisites and the Git-source alternative.

## Install

Install `ship` globally for Codex:

```bash
npx skills add EClinick/agent-skills --skill ship --agent codex --global
```

Or let the CLI prompt for an agent and installation scope:

```bash
npx skills add EClinick/agent-skills --skill ship
```

Install `demo-workbench` for Codex in the current project:

```bash
npx skills add EClinick/agent-skills --skill demo-workbench --agent codex
```

Add `--global` for user scope, or replace `codex` with your intended agent (for
example `claude-code` or `pi`). Omit `--agent` to choose interactively. In native
Windows PowerShell use `npx.cmd`. These commands install instructions, not the
separate CLI.

The canonical skill is a regular directory in this repository. Skills CLI installs
an independent snapshot; its optional agent symlinks point at that installed copy,
not at this author checkout or another repository. Updates are explicit via
`npx skills update demo-workbench` (add `--global` for user scope), separate from
CLI updates. See [Skills CLI docs](https://github.com/vercel-labs/skills#install-a-skill).
No npm publication is needed for the skill; [skills.sh discovery](https://skills.sh/docs/faq)
is based on installs, not a guarantee of immediate search indexing.

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

For a demo, describe the work and supply your files, for example:

```text
Use $demo-workbench to make a 3-second motion study from ./reference.mp4,
with ./soundtrack.wav. Create a new ./motion-study project, adapt the scene
to the reference's timing, render a first version, and open the gallery on
localhost. No critic agents yet.
```

You can also ask to revise an existing generated project, render another version,
serve explicitly on your tailnet, or stop its gallery. Without a reference, the
skill starts a neutral scene; it does not promise automatic visual fidelity.
