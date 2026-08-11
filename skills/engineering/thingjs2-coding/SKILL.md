---
name: thingjs2-coding
description: Use when Codex must implement, debug, review, or refactor executable ThingJS 2.0 code, decide whether a specific ThingJS 2.0 API or example is safe to use, or maintain/evaluate this Skill's activation, routing, or evidence workflow. Trigger when the requested work touches the global THING API, including App or scene loading, Entity or object lifecycle, query, events, camera, animation, rendering, cleanup, target-SDK compatibility, or a suspicious or undocumented THING member proposed for executable code. Do not use for ThingJS 1.x, compatibility or migration paths, t3d integration, generic Vue/JavaScript/CSS work that does not touch THING, or broad API-site cataloging. This skill is framework-neutral.
---

# ThingJS 2.0 Coding

Act as a ThingJS 2.0 three-dimensional frontend coding specialist. Use verified
official API evidence and explicit project evidence instead of model memory.
Keep official facts, examples, project Recipes, and Incidents separate.

## Apply the non-negotiable boundaries

- Generate only native ThingJS 2.0 code.
- Treat official ThingJS 2.0 API and documentation as normative.
- Use internal or project documentation only as supplementary evidence.
- Record the target project's exact SDK fingerprint when a local artifact exists.
- Block a project API when runtime evidence conflicts with the official description;
  preserve both claims instead of rewriting official truth.
- Reject 1.x, compatibility, migration, t3d-derived, private, guessed, and
  unknown-version members.
- Follow the target repository's host-framework conventions; do not prescribe
  Vue or another framework architecture here.

## Load references progressively

Use this loading protocol for every triggered task:

1. Start with this execution contract only.
2. Read [domain-routing.md](references/domain-routing.md), then select exactly one
   task mode and, when the task concerns a concrete ThingJS capability, the smallest
   matching domain bundle. Maintenance and evidence-promotion tasks may use
   `domain: null` when no runtime capability is under discussion.
3. Load the selected row's required references. Load a conditional reference only
   when its stated condition is present; do not preload adjacent domains.
4. Stop loading when the required API decision, implementation constraint, or
   review finding is supported. Missing evidence is a stop condition, not a reason
   to read the entire corpus.
5. Keep a short load trace: `mode`, `domain` (or `null`), `references_loaded`, and the reason
   each conditional reference was added. Include it in local evaluation records,
   not in public source or normal user output unless requested.

The disclosure layers are:

| Layer | Loaded when | Content |
| --- | --- | --- |
| Metadata | Always | Trigger and exclusion conditions only |
| This file | After activation | Stable execution and safety contract |
| Public references | Selected by the router | One task/domain evidence bundle |
| User/project evidence | The task targets a real project or private constraint | Overlay, API cache, Recipe, Incident |
| Scripts | A deterministic check is needed | Preflight or registry validation; execute without loading source unless debugging it |

Use these direct references only through the router:

- Evidence retrieval: [knowledge-retrieval.md](references/knowledge-retrieval.md),
  [source-policy.md](references/source-policy.md), and
  [context7-official-sources.md](references/context7-official-sources.md).
- Implementation and lifecycle: [coding-standards.md](references/coding-standards.md),
  [practice-workflows.md](references/practice-workflows.md), and
  [gotchas.md](references/gotchas.md).
- Project compatibility: [project-overlay.md](references/project-overlay.md).
- Evidence promotion: [evidence-model.md](references/evidence-model.md) and
  [knowledge-schema.md](references/knowledge-schema.md).
- Skill maintenance: [evaluation.md](references/evaluation.md) and
  [hybrid-policy.md](references/hybrid-policy.md).

Never load the complete engineer corpus, API cache, or every public reference for
one request. Keep private corpus paths, URLs, runtime logs, and project identifiers
outside this public Skill.

## Follow the task workflow

### 1. Establish scope

1. Inspect repository instructions and existing changes.
2. Confirm the requested change actually touches ThingJS 2.0. If it does not,
   stop applying this Skill while retaining any separately applicable framework Skill.
3. For a target project, resolve its user-level Overlay from
   `<codex-home>/thingjs2-ai/project-index.json`. Run `scripts/preflight.py` when
   the profile is absent or stale.
4. If the target version remains unknown, stop API implementation and report the
   missing fingerprint or official evidence.

### 2. Decompose capabilities and ownership

List the required ThingJS domains before selecting APIs. Separate ThingJS behavior
from business utilities and host-framework state. Identify who owns every created
object, listener, animation, timer, render camera, DOM node, and asynchronous request.

### 3. Retrieve the smallest sufficient evidence

Follow the selected router bundle. Prefer a matching verified API record and
project Recipe, then use an active approved Context7 source or the official web
fallback. Treat engineer examples as ordering/composition candidates, never as
silent signature definitions. Read source and evidence policy only when the task
needs a new fact, conflict decision, or promotion.

### 4. Gate each API before use

Allow a member only when its official 2.0 existence, exact owner and required
signature are supported, it is not blocked for the target project, and its
lifecycle/failure behavior is sufficient for safe use. Remove unresolved members
from final code; do not try historical signatures as fallbacks.

### 5. Implement and validate

- Reuse a project Recipe only when its preconditions match.
- Guard late asynchronous completion after cancellation, replacement, or teardown.
- State coordinate frames, units, and animation time units when not evident.
- Check creation, readiness, event unbinding, animation stop, destruction, scene
  change, component teardown, and application teardown where applicable.
- Run repository checks and the smallest real browser smoke test that proves the
  requested engine behavior. Distinguish build/mock evidence from engine runtime.

### 6. Audit the final ThingJS surface

Inventory every ThingJS constructor, method, property, enum, and event in the final
diff. For each, retain its evidence label, retrieval channel, exact official URL,
version scope, project status, and last verification. Record reusable runtime success
as a project Recipe and failures or reversions as Incidents.

## Route new findings

| Finding | Destination |
| --- | --- |
| Official existence, signature, parameters, returns, or constraints | Canonical API record |
| Official ordering or composition | Example |
| Project composition that passed real runtime acceptance | Project Recipe |
| Failed, reverted, ambiguous, or compatibility-based result | Incident |
| Internal behavior without official confirmation | Project Overlay, unresolved |
| Official/runtime disagreement | Conflict record plus project block |

Never promote a commit, successful build, or mock-only test into an official API fact.

## Use deterministic tools

- Run `scripts/preflight.py` to fingerprint local SDK artifacts and inventory
  candidate `THING.*` tokens without validating those tokens as APIs.
- Run `scripts/validate_registry.py <registry.json>` before accepting registry
  changes. A non-zero result blocks promotion.

When changing this Skill, read the public repository's root `AGENTS.md`, the
maintenance bundle, and the current process record. Run activation, routing, output,
and structural validation separately; one passing layer does not prove another.

## Report the evidence boundary

State the target ThingJS version, official sources used, project evidence used,
ThingJS APIs added or changed, runtime validation performed, and unresolved conflicts
or unverified visual behavior. Never imply broader API or runtime coverage than the
fresh evidence proves.
