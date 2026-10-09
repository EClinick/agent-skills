---
name: demo-workbench
description: Create or iterate on local demo videos from a description, reference video and optional soundtrack using the separately installed demo-workbench CLI. Use when asked to build or edit an animation, render numbered versions, review exact outputs, open the existing review gallery on localhost or an explicitly requested tailnet, or stop that project's serving.
---

# Demo workbench

Run the workflow for the user, not just a list of commands. This is a thin driver
for **demo-workbench 0.2.x** (verified with 0.2.0), not a renderer or gallery bundle.
The [CLI repository](https://github.com/EClinick/demo-workbench) is currently
**private and requires access**. Installing this public skill neither installs
the CLI nor grants access or redistribution rights.

Authoritative references (require repository access):
- [Installation and prerequisites](https://github.com/EClinick/demo-workbench/blob/main/docs/installation.md)
- [CLI workflow](https://github.com/EClinick/demo-workbench/blob/main/README.md)
- [Generated-project contracts](https://github.com/EClinick/demo-workbench/blob/main/template/README.md)

Use installed `--help` and the actual project's README for its frozen runtime;
linked `main` documentation can evolve. Do not duplicate the application, rebuild
its gallery, or fetch private content into this skill.

## 1. Check the environment and intent

- Identify the actual OS **and shell**, current directory and available process
  tools. For a new project, discover the executable on PATH, then run `--version`,
  `--help` and read-only `doctor`. For an existing project, use its local runtime
  checks in section 2 instead; a missing global CLI is not a blocker.
  Add `doctor --tailnet` **only for explicit tailnet intent**.
  Do not treat doctor as proof of rendering or remote reachability.

  | Shell | Discover | Invoke |
  | --- | --- | --- |
  | macOS/Linux/WSL POSIX | `command -v demo-workbench` | `demo-workbench`, `npm` |
  | Native Windows PowerShell | `Get-Command demo-workbench.cmd` | `demo-workbench.cmd`, `npm.cmd` |
  | Native Windows cmd.exe | `where demo-workbench` | `demo-workbench`, `npm` (double-quoted paths) |

  The examples below use POSIX spellings; translate for the detected shell.
  Quote paths/arguments, never interpolate media names as shell code. WSL uses
  Linux Node/npm/Git/FFmpeg and Linux paths; native Windows uses Windows tools
  and paths. Do not mix environments or change PowerShell execution policy.
- If the CLI is absent, outside 0.2.x, or doctor fails, diagnose before mutation.
  Explain the specific missing prerequisite using the installation docs: supported
  Node LTS with npm (CLI minimum Node 18), Git 2.28+, FFmpeg/ffprobe with libx264,
  AAC and drawtext, and a user-writable npm prefix whose executables are on PATH.
  Git-source installation also requires existing authenticated private-repository
  access; browser/agent GitHub access does not necessarily authenticate Git.
  The documented route is `npm install --global --ignore-scripts --omit=dev
  --no-audit --no-fund 'git+https://github.com/EClinick/demo-workbench.git#main'`
  (one command; use `npm.cmd` in PowerShell). `main` moves; prefer an approved full
  commit SHA for a pinned install. Obtain approval before any installation,
  update, dependency download, authentication, global/config or network change.
  If access is denied, explain that the repository owner must grant access; do
  not bypass it, invent a release tag, embed credentials, use sudo, or invoke
  `npx demo-workbench` / an unverified registry package. If docs are inaccessible,
  say so. Do not silently upgrade existing projects to make commands work.
- Use the supplied creative brief, inputs, destination and constraints. Inspect
  the supplied media. Ask only for missing essentials (e.g. which of ambiguous
  files/destinations to use); do not impose a questionnaire. No reference is a
  valid choice: state that the starter is neutral, not an automatic recreation
  or a fidelity guarantee. An optional soundtrack must be supplied explicitly;
  reference audio is **not** automatically used.

## 2. Choose new or existing project

**New:** Confirm the intended destination does not exist, including an empty
folder or symlink, and its parent exists. Do not pre-create the target or clear an
existing one. For supplied inputs, let init copy them; never move/delete originals.
For example (substitute the user's actual paths, omit absent input flags):

```sh
demo-workbench init "./motion-study" --reference "./reference.mp4" --audio "./soundtrack.wav" --title "Motion study"
cd "./motion-study"
```

Without inputs, `demo-workbench init "./motion-study" --duration 3` creates a silent
neutral starter. Reference dimensions/FPS/duration are otherwise probed; preserve
aspect ratio when changing both dimensions. Only override settings for the brief
or an explained iteration budget. Init makes a local Git repo with no commit or
remote; no identity/global agent settings need changing.

**Existing:** Verify the intended project root, inspect its `demo.json`,
`package.json`, `.workbench/package.json` and working changes. Never run init over
it. Read its local help/version with `node .workbench/bin/cli.js --help` and
`--version`, and diagnose with `node .workbench/bin/cli.js doctor` (optional
`--tailnet` only on request). The global initializer may be absent; a compatible
self-contained project does not require reinstalling it. For older/unknown
runtimes, check their actual docs/contracts before acting; do not migrate them.
If adding/replacing inputs, follow that project's README, copy to a new
project-relative input path without overwriting originals, update configuration,
and render a new version.

**Both:** Read the generated `CLAUDE.md`, `README.md` and `demo.json` before editing.
Work creatively in `src/scene.js`, `src/render.js`, `assets/` and relevant config:
implement the requested composition, motion, timing and typography, not just the
starter. Keep `site/`, `.workbench/`, generator/runtime metadata and earlier runs
intact. Use trusted local code; renderers execute code, not a sandbox. Follow the
local renderer-to-MP4 contract; the CLI, not scene code, muxes optional audio.
Keep source/assets self-contained for provenance; approve new dependencies first.

## 3. Render, inspect, iterate

Use project-local scripts from now on, never a newer global runtime:

```sh
npm run demo:render -- --note "Describe the actual scene change"
npm run demo:compare -- v001
```

Use the **actual** version printed by render, not necessarily `v001`. Each render
allocates the next immutable number; do not overwrite old media, manifests,
reviews or hashes. Comparison is generated with a reference; without one, report
that reference comparison is unavailable. Inspect actual output and aligned
packet/frames when supported by the host; disclose any inability to view video.
A render failure is not a finished video: read retained diagnostics, fix the
source and retry without deleting evidence or evading locks/integrity checks.

For requested reviews, use the user's rubric/critics and a bounded round budget;
if no budget was supplied, do one render/inspection pass, not an automatic critic
loop. Do not launch paid agents without approval or invent scores to fill the
gallery. If genuine review evidence exists, read the **local README's review JSON
schema**, use that
run's exact `outputSha256` and `packetSha256` from `runs/VERSION/manifest.json`
(JSON null packet hash without a reference), record the actual critic identity,
findings and score, then import:

```sh
npm run demo:review -- v001 --file "./review.json"
```

Import is one-time and hash-checked; never bypass rejection. Without a real review,
leave **not judged yet**. Changes to scene, reference, offsets or settings require
a new render, not regrading old evidence. Notes/findings are visible in the gallery;
exclude secrets, private logs and conversations. Only archive if requested, using
`npm run demo:archive -- VERSION NEW-DESTINATION`; bundles contain private inputs
and source, and are not public-share artifacts.

## 4. Serve and stop the existing gallery

When asked to view/serve, run `npm run demo:serve` (optional `-- --port PORT`)
through the host agent's supported **tracked foreground/session process tool**.
Record the project cwd, process/session handle, printed URL and cleanup ownership.
Do not use untracked `&`, `nohup`, detached shells or a new daemon. If the host
cannot keep and control a server session, explain the limitation and offer the
user a foreground command rather than pretending a persistent service exists.

Localhost is the default. Only an **explicit tailnet request** permits
`npm run demo:serve -- --tailnet`. Use only the printed, verified URL, never an
inferred hostname/IP. No public Funnel, wildcard bind, firewall/WSL repairs or
replacement of occupied ports/mappings. Diagnose a conflict; choose a free port
within the requested scope, or ask if the port matters. The same-machine route
probe is **not second-device verification**: ask for a check on the intended
device before claiming remote playback/ACL success.

Stop the owned process with normal Ctrl-C/SIGINT or supported graceful SIGTERM;
wait for exit and inspect cleanup results. After a crash or refused tailnet
cleanup, from the **exact owning project**, run:

```sh
npm run demo:serve -- --stop-tailnet
```

Use the original `--tailscale PATH` only if needed. This removes that project's
recorded owned mapping, not a still-running local process. Never use
`tailscale serve reset`, delete ownership records/active locks, kill unrelated
processes or clean another project's resources. If ownership checks refuse,
report the diagnostic and leave shared configuration untouched. Cleanup means
stopping owned serving, not deleting projects, inputs or run history.

## Handoff

Report actual project/output paths, rendered versions, comparison/review status,
verified URL and whether the owned server is running or stopped. State its real
session lifetime (not permanent hosting), how to stop it, failures and remaining
visual/audio/second-device validation. Never claim a render or review you did not
perform. Do not publish, upload, commit, push or merge a generated project unless
separately requested.
