---
name: thingjs2-coding
description: Implement, debug, review, and refactor ThingJS 2.0 code using verified official API evidence, project runtime fingerprints, and project-specific recipes. Use for ThingJS 2.0 scene, object, query, event, camera, animation, loading, rendering, and lifecycle tasks, or whenever a codebase uses the global THING API. Exclude ThingJS 1.x, compatibility or migration APIs, t3d assumptions, and unverified third-party API claims. Do not prescribe Vue or another host-framework architecture.
---

# ThingJS 2.0 Coding

Use official ThingJS 2.0 facts and explicit project evidence instead of model memory. Keep API facts, official examples, project recipes, and failed historical attempts in separate evidence classes.

## Apply the non-negotiable rules

- Generate only ThingJS 2.0 code.
- Treat official ThingJS 2.0 API and documentation as the normative source.
- Use internal documentation as supplementary project evidence, never as a silent replacement for conflicting official facts.
- Record the project's exact SDK fingerprint when a local artifact is available.
- Block an API for the current project when its runtime conflicts with the official description; preserve the conflict instead of rewriting official truth.
- Reject ThingJS 1.x, compatibility, migration, t3d-derived guesses, model-memory guesses, and unknown-version snippets.
- Keep host-framework implementation rules outside this skill. Follow the repository's own framework conventions.

Read [source-policy.md](references/source-policy.md) before accepting a new source or resolving a conflict. Read [evidence-model.md](references/evidence-model.md) before promoting any API, example, recipe, or incident to a stronger evidence state.

## Follow the coding workflow

### 1. Establish the project boundary

1. Inspect repository instructions and existing changes.
2. Resolve the user-level Overlay for the target project from `<codex-home>/thingjs2-ai/project-index.json`.
3. If the profile is absent or stale, run:

```text
python scripts/preflight.py --project-root <project-root> --output <codex-home>/thingjs2-ai/project-overlays/<project-id>/project-profile.json
```

4. Confirm that the project is ThingJS 2.0. If the version remains unknown, stop API implementation and report the missing evidence.
5. Load only the user-level project Overlay relevant to the task. Do not create Skill or Knowledge files in the target application repository. Read [project-overlay.md](references/project-overlay.md) for location, precedence, and security rules.

### 2. Decompose the request into ThingJS capabilities

List the required domains before selecting APIs, such as App initialization, loading, object creation, query, events, hierarchy, camera, animation, rendering, or cleanup. Separate ThingJS behavior from business utilities and host-framework state.

### 3. Retrieve the smallest sufficient evidence set

1. Search the project's approved API registry and relevant project recipes.
2. Load only the matching API domain or class records.
3. If facts are missing, query approved official sources for the exact capability.
4. Use official examples to learn composition and ordering, not to redefine an API signature.
5. Use Context7 only as a retrieval aid. Confirm its underlying source before accepting any result.
6. Treat repository code as a recipe candidate or incident candidate until its API calls and real runtime behavior are verified.

Use [knowledge-schema.md](references/knowledge-schema.md) when adding or updating canonical API records.

### 4. Decide whether each API is usable

Allow an API only when all of the following are true:

- an official ThingJS 2.0 source supports its existence and required signature;
- the record is not marked `runtime_conflict` or `project_unsupported` for the target project;
- the code uses an exact verified signature rather than trying multiple historical variants;
- required lifecycle and failure behavior are known well enough to implement safely.

When any condition fails, keep the API out of final code. Report the missing official page, signature, runtime probe, or cleanup rule that is needed.

### 5. Implement within explicit ownership boundaries

- Reuse verified project recipes only when their preconditions match.
- Define who owns every created ThingJS object, event binding, animation, timer, render camera, DOM node, and asynchronous request.
- Handle late async completion after cancellation or scene replacement.
- State coordinate frames and units when positions, rotations, camera offsets, animation time, or distances are not evident.
- Avoid fallback branches that try 1.x signatures after a 2.0 call fails.
- Preserve unrelated user changes and repository conventions.

### 6. Audit the result

Before handing off code:

1. Inventory every ThingJS constructor, method, property, enum, and event used by the final diff.
2. Resolve each item to a canonical API record or an approved official source.
3. Verify that no blocked or unknown API remains.
4. Check creation, async completion, event unbinding, animation stop, object destruction, scene change, and component or application teardown.
5. Run repository tests and the smallest real browser smoke test capable of proving ThingJS behavior.
6. Distinguish unit-test evidence from actual engine-runtime evidence.
7. Record reusable success as a project Recipe and failures or reversions as Incidents.

Read [evaluation.md](references/evaluation.md) when measuring whether this skill improves task completion rather than merely increasing documentation coverage.

## Route new findings correctly

| Finding | Destination |
| --- | --- |
| Official existence, signature, parameters, returns, or constraints | Canonical API record |
| Official code demonstrating ordering or composition | Example |
| Project code that passed real runtime acceptance | Project Recipe |
| Failed, reverted, paused, or compatibility-based implementation | Incident |
| Internal behavior not confirmed by official sources | Project Overlay with an unresolved evidence state |
| Official/runtime disagreement | Conflict report plus project block |

Never promote a Git commit, mock-based unit test, or successful build into an official API fact.

## Use the bundled tools

- Run `scripts/preflight.py` to fingerprint local ThingJS SDK artifacts and inventory explicit `THING.*` tokens without claiming they are valid APIs.
- Run `scripts/validate_registry.py <registry.json>` before accepting registry changes. Fix duplicate canonical keys, missing official evidence, invalid usage states, and runtime-conflict leaks.

Both scripts emit machine-readable JSON and return non-zero for validation failures.

## Report the evidence boundary

In the final response, state:

- the target ThingJS version or why it remains unknown;
- the official sources used;
- project Overlay evidence used;
- all ThingJS APIs added or changed;
- runtime validation performed;
- unresolved conflicts, unknown APIs, and unverified visual behavior.
