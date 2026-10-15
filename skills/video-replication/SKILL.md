---
name: video-replication
description: Recreate a reference video faithfully from scratch using demo-workbench, measured frame studies, a soundtrack, bounded model-agnostic reviews and an audible side-by-side comparison. Use for /video-replication or requests to replicate a video or motion design.
---

# /video-replication

Recreate the supplied reference using the companion [demo-workbench skill](../demo-workbench/SKILL.md)
(or locate it by name when installed separately). Follow it for CLI setup, immutable
runs/reviews and gallery lifecycle; do not clone the runtime or rebuild the gallery.

The [CLI repository](https://github.com/EClinick/demo-workbench) is public;
installing this skill does not install the CLI. Follow installed help and the
project's README, not assumptions about the moving `main` branch.

Arguments: `--judge <model-id>` selects the review model, not the builder model.
These are instructions interpreted by the agent, not a universal CLI parser.
Explicit flag or natural-language judge selection wins over an explicitly stated
user default. If selections conflict, clarify; if neither exists, ask one concise
question. Verify availability before paid calls; never silently substitute a model.
Use the supplied rubric, target and round budget; otherwise propose target **8.0**
and ask approval for the rubric and a finite budget before spending.

```text
/video-replication --judge <model-id> Recreate ./reference.mp4 with ./soundtrack.wav.
Use /video-replication with judges using model X to recreate my reference video.
```

## User intent

Recreate the reference from scratch as close to identical as achievable: the same
motion, timing, transitions, typography, icons, materials and camera, frame for frame.
Independently rebuild the scene, rather than reusing reference frames as the result.
Faithfully recreate text, UI copy, layout, people, photos and products. Use the closest
achievable look-alike assets (generated where needed and approved), not unrelated
content. Ask only when a concrete rights, access or asset constraint blocks a specific
element; name it and the options. Otherwise do not substitute or impose a questionnaire.
Keep the user's rubric unchanged; separating design fidelity from approved identity
differences is only an optional proposal for approval.

Use the supplied soundtrack in sync from 0 s unless instructed otherwise. Extract
reference audio only when explicitly requested and permitted. If needed audio was
not provided, search **api.openverse.org** for fitting music/effects and use tasteful
sound design. Check current API docs before prescribing endpoints; verify each
asset's source, license and required attribution, retain credits, and never embed
credentials or assume all assets share a license.

## Execution plan

1. **Inputs and capability:** verify/download permitted inputs; record duration,
   FPS, dimensions and hashes. Confirm non-silent audio. Record installed and
   project-local runtime versions and read their actual contracts. **demo-workbench
   0.2.0 produces silent comparisons**; the shared audio fix is not assumed released.
   Require supported capability for audio in the actual comparison player, or report
   the concrete limitation and seek an approved upgrade/new-project path. Never
   auto-reinstall, patch frozen runtimes/gallery files or rewrite historical runs.
2. **Study before rendering:** build aligned frame strips at source FPS around every
   transition. Measure timing, easing, layout and camera; note variable-rate/timebase
   uncertainty. Make an asset/render strategy table: element, reference frame/crop,
   photo/vector/generated/3D needs, renderer, rationale and source/license constraints.
3. **Calibrate:** with approval, run the same critic setup once on a labelled blurred
   near-copy of the reference, separate from candidates. Report its ceiling; it never
   counts as a result. Include its paid cost in the approved scope. If not run, say so.
4. **Build:** use a demo-workbench project and local render commands. Every change
   cites its reference frame/crop. Before each judged round, compare reference |
   previous | new crops at those timestamps and inspect motion; drop regressions.
   Keep source/assets and provenance; every change to output, inputs or alignment
   gets a new immutable version, never an overwrite of media, hashes or reviews.
5. **Judge:** use three critics—Motion, Visual, Typography—with the selected model
   and approved rubric. Each sees the same fixed packet: identical frame indices,
   reference, full render and audible side-by-side. Keep the sampling scheme fixed
   across rounds. Record actual model IDs and exact output/packet hashes; hash any
   supplemental evidence separately. Verify suggestions against reference frames
   before acting. Import only genuine reviews using the local schema; no fabricated,
   reused or cherry-picked scores. Disclose unsupported critic modalities.
6. **Budget:** obtain approval for paid reviews/generation and at most **N** judged
   rounds, including calibration scope. Without approval, do one build/inspection
   pass, **not judged yet**, rather than launching critics. Use the three-score mean
   unless the user approved another aggregation. Stop if three consecutive means
   stay within ±0.3 (span ≤0.6), or the budget runs out below the target. Report the
   best version, remaining gaps and options: better assets, renderer or more rounds.
   No polishing inside noise, retries beyond budget or success from a score alone.
7. **Gallery:** serve the existing gallery on localhost with its verified printed
   URL and tracked process. Tailnet requires explicit intent; public publication
   requires separate approval. The first video a viewer plays must have sound.

## Acceptance tests and handoff

- The final/render MP4 **and the actual side-by-side comparison MP4 embed the
  soundtrack**. Decode and check non-silence, duration and sync. Against the expected
  soundtrack/mix, require correlation ≥0.98 at zero lag after documented trim/pad,
  with common sample rate/channels. For comparison offsets, test the corresponding
  audio segment; exclude silence padding and disclose undefined/failed measurements.
- Test the **exact served comparison player** in a real browser: identify its media
  URL/artifact, play/unmute, pause/resume, restart and seek near start/middle/end.
  Check audio decoding/listening, both panels' alignment and cue sync through the end.
  Metadata, the Render tab, a silent label or inaccessible local audible copies do
  not satisfy delivery. Do not switch away from a silent comparison as a workaround.
- Every judged version uses the same packet format and exact output/packet hashes.
  Keep a written change → reference evidence → effect log and asset/license credits.
- Report best real mean, model, control ceiling (or not run), budget used, remaining
  visual gaps and whether the target was reached. Do not call it identical without
  both critic and reference evidence. Include version/output paths, hashes, runtime
  versions, verified URL, server lifetime/stop method and actual audio/seek/sync results.
- Disclose unavailable browser/audio checks; decoding is not proof of audible speakers.
  Intended-device audibility remains untested until someone listens, and same-machine
  reachability is not second-device verification. Incomplete checks mean incomplete
  acceptance. Keep private logs out of gallery notes; no unapproved publication.
