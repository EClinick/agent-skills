---
name: video-replication
description: Faithfully reconstruct a reference video from scratch with measured frame and timing studies, soundtrack, bounded fidelity reviews, and an audible side-by-side comparison. Use when asked to replicate, recreate or match a reference video, animation or motion design using demo-workbench.
---

# Video replication

Rebuild the reference independently, as close to identical as achievable—not a
loosely inspired redesign. Run the work, not merely a prompt-writing exercise.
Use the existing **demo-workbench** skill and separately installed CLI for project
creation, rendering, immutable evidence, review import and gallery serving. Do not
clone its runtime or build another gallery. This skill supplies the replication
method and stricter audio acceptance gates, not an application bundle.

Read the companion [demo-workbench instructions](../demo-workbench/SKILL.md)
(in this repository); if installed separately, locate the installed skill by name.
If absent, obtain those instructions through an approved installation/access route
before proceeding. The [CLI repository](https://github.com/EClinick/demo-workbench)
is public; installing this skill does not install the CLI. Follow installed help
and the generated-project README, not assumptions about the moving `main` branch.

## 1. Establish the brief and capability gate

Use the reference, soundtrack, destination and constraints already supplied. Ask
only for missing essentials or concrete blockers; do not start a large questionnaire.
A reference MP4 or accessible source URL is essential for a fidelity claim. Verify
permission/access before downloading; preserve originals and never bypass access
controls. Record input SHA-256 hashes, dimensions, rational FPS, duration and audio
facts. Identify variable frame rates and decoding/timebase uncertainty.

Faithfully recreate text, UI copy, layout, people, photos, products, icons,
materials, lighting, camera, typography, motion and transitions. “From scratch”
means independently authored scene/assets, not tracing success by playing source
frames in the candidate. Use the closest achievable look-alike assets, generated
where needed and authorized. Do not replace content with unrelated people, copy
or imagery. When rights, access or an asset constraint blocks a specific element,
name it and offer options for approval. Do not silently lower the fidelity goal.

Before work, record a compact plan: inputs, renderer/assets, audio source, target,
rubric/model, budget, destination and delivery scope. Preserve any user-approved
rubric, critic identities, aggregation and target. Absent overrides, propose three
**Sonnet 5.5** critics—Motion, Visual and Typography—scoring reference fidelity
0–10, with an arithmetic mean target of **8.0**. Verify that exact model is available
through the actual review provider; a model label is not proof. If unavailable,
report it and ask before substituting. Do not invent a model ID or silently change
the rubric. Separating design fidelity from approved identity differences is only
an optional proposal requiring approval.

Confirm approval for paid critic calls, asset generation and a finite judged-round
budget **N**, including the calibration cost, before spending. If no review budget
is approved, do one build/self-inspection pass only, leaving it **not judged yet**.
A request to replicate is not permission for unlimited paid review. Confirm missing
review approvals together in one short question; do not block free input analysis.

### Runtime compatibility is a delivery gate

Follow demo-workbench's environment checks: installed version/help/doctor for a new
project, local `.workbench` version/help/doctor for an existing one. Record generator
and frozen runtime versions. No automatic install, upgrade, dependency download or
reinstall; obtain approval and preserve provenance for any supported transition.
Never patch frozen `.workbench/`, gallery templates or historical runs in place.

**Known baseline: demo-workbench 0.2.0 makes silent comparison MP4s**, even when the
candidate render has audio. A shared comparison-audio fix is under development;
do not assume it is released or installed, or invent a minimum fixed version.
Check the actual runtime documentation/capability and generated output. Require a
supported runtime that muxes the chosen soundtrack into the actual side-by-side
MP4 and serves that exact artifact in its comparison player. If unavailable,
report the concrete version/capability limitation and seek an approved supported
upgrade/new-project path, or hand off explicitly incomplete work. No switching to
Render, “silent” labels, or inaccessible local audible copies as completion.

## 2. Resolve and prepare audio

1. Honor the user's supplied soundtrack first. Verify it decodes, is non-silent,
   and has the intended duration/content. Default sync begins at 0 s unless the
   brief specifies otherwise. Do not replace it with a preferred track.
2. If the user explicitly requests audio extracted from the reference, extract it
   where permitted, retain the source/hash and document the extraction. Reference
   audio is not implicitly adopted by the CLI or by this skill.
3. When audio is needed and none was provided, **search api.openverse.org** for
   fitting music/effects. Compare a small set against the reference's mood, tempo,
   pacing and transitions; select fitting options for tasteful sound design.
   Consult [current Openverse API docs](https://api.openverse.org/v1/) before
   prescribing exact endpoints or authentication. Never embed API credentials.
   Verify each asset at its source: creator, source/download URL, license name and
   version, allowed adaptations/use, and required attribution. Licenses differ;
   an Openverse result is discovery, not blanket clearance. Keep an asset/license
   ledger and deliver required credits. If rights or access cannot be verified,
   choose a verifiable alternative or report the blocker—never silently omit audio.

Keep music/effects restrained and reference-led, not a new creative direction.
Document trims, fades, levels, effect cues and any approved edits. Save a lossless
expected soundtrack/mix for validation, with its hash. Respect the local renderer
contract: the 0.2.x renderer writes silent video and the CLI muxes configured audio;
do not evade the contract by embedding audio in scene output. Use supported input
configuration for the prepared mix and verify the final mux, not just the input.

## 3. Measure before rendering

- Decode frame strips at the source FPS around **every transition**, including
  starts/ends, holds, overlaps and camera moves. Record frame indices, timestamps,
  crops and nominal versus decoded time for variable-rate sources. Sparse gallery
  samples alone are not a transition study.
- Build a timing map: each beat's start/end, duration, easing, trajectory, scale,
  rotation, occlusion and opacity. Measure layout bounds, spacing, baselines,
  font characteristics, colors, material and lighting cues. Mark uncertainty.
- Write an asset/render strategy table: element, reference frame/crop, required
  asset (vector/photo/generated/3D), renderer/technique, rationale, rights/source,
  fidelity risk and any approved deviation. Choose the approach before render 1;
  do not spend rounds polishing a renderer that cannot express the reference.
- Keep scene/source/assets self-contained and versioned. Preserve input, tool and
  dependency provenance. Follow the companion skill for new versus existing
  projects and project-local render commands; never reinitialize an existing one.

## 4. Build and review bounded, meaningful iterations

When paid review is approved, run the same critic setup once on a **labelled blurred
near-copy control** of the reference. Keep it separate from independently rebuilt
candidates, subject to source rights and the agreed budget. Report its calibration
ceiling; it never counts as the result. If calibration cannot run, disclose why;
do not fabricate a ceiling or treat candidates as calibrated.

For each candidate:

1. Make reference-backed changes. Log `change → frame/crop/time → expected effect`.
   Before spending on a judged round, inspect reference | previous | new crops at
   the cited timestamps and full-motion playback. Drop regressions; record actual
   effects and unresolved gaps. Use a new numbered render for every changed output,
   input, alignment or setting; never overwrite runs, manifests or reviews.
2. Freeze evidence before judging: full reference, full candidate, audible
   side-by-side, aligned frame indices/crops and timing/asset notes. All three
   critics see **the identical packet**, rubric and approved deviations. Fix the
   sampling scheme across rounds; do not cherry-pick a different sample per critic.
   Record actual model/provider IDs, rubric, output/packet hashes and comparison
   hash. If extra evidence is outside the CLI packet, hash and record it separately;
   do not mutate the archived packet or pretend its hash covers external files.
3. Ask Motion to assess timing/easing/transitions/camera, Visual to assess
   composition/assets/materials/lighting, and Typography to assess copy/font/layout
   and text motion, unless the approved rubric says otherwise. Require timestamped,
   reference-backed findings. Verify every suggestion against the reference before
   acting; critics can be wrong. Disclose modalities a critic cannot inspect.
4. Import only genuine exact-output reviews using the **local README's schema** and
   manifest `outputSha256` / `packetSha256`. The CLI stores/imports reviews; it does
   not run critics. No invented, reused or selectively discarded scores, no altered
   aggregation to pass. Failed/incomplete calls are not successful reviews; account
   for their cost and do not retry outside the approved budget.
5. Stop at the approved target only if delivery checks also pass. Stop at **N**
   judged rounds, or if three consecutive judged means span no more than **0.6**
   points (within ±0.3 of their midpoint). Report a plateau rather than polishing
   inside judge noise. No reruns solely to fish for a higher score. More rounds,
   changed rubric/model or a different renderer need renewed approval.

## 5. Acceptance: test the exact served comparison

A score alone is not delivery. Preserve evidence for these checks:

- **Both the final/render MP4 and the actual side-by-side comparison MP4 embed the
  intended soundtrack.** Probe streams and decode audio to confirm non-silence,
  duration, levels and sync; no duplicate/reference-track mixing unless requested.
  Compare decoded PCM on a common sample rate/channel layout: correlation **≥0.98
  at zero lag** against the expected soundtrack after documented trim/pad/mix.
  For nonzero candidate comparison offsets, use that exact expected audio segment;
  do not shift arbitrarily to hide sync errors. Exclude documented silence padding
  from correlation, test audible regions, and report failed/undefined measurements.
- Serve the existing gallery with a tracked process following demo-workbench's
  serving/cleanup ownership rules. Default to localhost; tailnet requires explicit
  user intent. Public publication/upload requires separate approval. Never create
  public exposure or repair shared network configuration as a shortcut.
- In a real browser, open the **printed served URL**, select the delivered version
  and actual Side-by-side player, record its media URL and verify it corresponds to
  the tested comparison artifact/hash. Test first/default playback, user-gesture
  play/unmute, volume, audible/decoded audio, pause/resume, restart and seeks near
  start/middle/end. Verify timing after seeks and absence of drift through the end.
  Confirm both panels remain aligned with soundtrack cues. Check range/seek fetch
  failures and browser errors, not just a successful page load.
- Stream metadata, a Render-tab test, labels or a download link alone do **not**
  satisfy comparison playback. Browser decoding evidence is not proof of sound at
  speakers. If browser tools, audio output or the intended device are unavailable,
  say exactly which checks remain untested; request a listening check and do not
  claim full acceptance. Same-machine tailnet access is not second-device proof.

Do not alter old media/public copies to make these checks pass. Fix editable source
or use an approved supported runtime path and generate new immutable evidence.

## Handoff

Report the best actual version and real mean (or **not judged yet**), critic IDs,
control ceiling (or not run), budget used, whether the 8.0/default or overridden
target was reached, remaining visual gaps, plateau and next options. Do not claim
“identical” without both review and reference evidence supporting it.

Include output/comparison paths and hashes, runtime versions, asset/license credits,
change-to-evidence log, exact served URL, comparison audio/seek/sync results and
untested browser/device checks. State the server's actual lifetime, owner and stop
method. Keep private input paths/logs out of published gallery notes. No publishing,
committing or uploading the generated project without separate user approval.
