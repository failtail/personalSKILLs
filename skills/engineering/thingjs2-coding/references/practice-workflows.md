# Reusable ThingJS 2.0 practice workflows

This file is the conversion index for engineer-maintained material. Read it for
`convert` or `promote` work; for implementation or diagnosis, load only the
matching child workflow under `workflows/`.

## Workflow contract

Every promoted workflow records:

- preconditions and the required ThingJS 2.0 runtime scope;
- exact API owners and source URLs;
- object, event, DOM and asynchronous-request ownership;
- readiness, cancellation and late-completion behavior;
- cleanup, rollback and failure checks;
- project/SDK/runtime evidence before `project_verified` promotion.

## Corpus-to-workflow index

| Engineer corpus pattern | Child workflow | Promotion gate |
| --- | --- | --- |
| `开发示例/scene-scene.md`, `scene-campus-dynamic-loading.md` | `workflows/scene-loading.md` | Official App/scene evidence plus load, replacement, and failure behavior |
| `开发示例/object-create.md`, `object-destroy.md` | `workflows/entity-lifecycle.md` | Exact constructor/readiness and destroy/lifecycle evidence |
| `开发示例/event-event-control.md` | `workflows/event-ownership.md` | Matching owner, type, condition, tag, and teardown evidence |
| `开发示例/camera-fly.md` | `workflows/camera-animation.md` | Camera owner, readiness order, and version-specific timing evidence |

## Conversion boundary

Classify each source as an API fact candidate, Example, Recipe, Incident, or
rejected record before writing a derivative. Engineer examples are composition
and ordering candidates, never silent signature definitions. Keep source
fingerprints and private corpus content in the user workspace.

These workflows do not authorize an API whose exact official signature, version
scope, or runtime compatibility remains unknown.
