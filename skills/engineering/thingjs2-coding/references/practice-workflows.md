# Reusable ThingJS 2.0 practice workflows

This file maps the supplied engineer corpus to reusable workflows without
turning the corpus into an unverified API encyclopedia. Read it when a task
matches one of these workflows. Keep exact signatures in the official API
source or the lightweight API Cache.

## Workflow contract

Every promoted workflow records:

- preconditions and the required ThingJS 2.0 runtime scope;
- exact API owners and source URLs;
- object, event, DOM and asynchronous-request ownership;
- readiness, cancellation and late-completion behavior;
- cleanup, rollback and failure checks;
- project/SDK/runtime evidence before `project_verified` promotion.

## Corpus-to-workflow mapping

| Engineer corpus pattern | Reusable workflow | Promotion gate |
| --- | --- | --- |
| `开发示例/scene-scene.md` | App bootstrap and scene load | Official `THING.App` constructor/load evidence plus runtime load result |
| `开发示例/object-create.md` | Entity creation and readiness | Exact constructor signature and completion/wait evidence |
| `开发示例/event-event-control.md` | Tagged event ownership | Matching `on`/`off` owner, type, condition and tag |
| `开发示例/object-destroy.md` | Destroy then clear reference | Destroy return/lifecycle evidence and no stale owner use |
| `开发示例/camera-fly.md` | Camera operation after scene readiness | Camera owner path and version-specific callback/duration evidence |
| `开发示例/scene-campus-dynamic-loading.md` | Scene replacement | Generation token, reject/rollback/finally and late-result cleanup |

## Workflow 1: App bootstrap and load

- Create the App through the native 2.0 constructor.
- Keep the App as the owner of scene listeners and loaded resources.
- Await the documented load Promise or use the documented completion callback;
  do not mix historical callback names without evidence.
- On failure, surface the error and restore loading state in `finally`.
- Dispose the App only from its owner boundary.

## Workflow 2: Entity readiness

- Create the Entity with the documented resource URL and options.
- Treat the instance as not ready until the documented completion signal or
  `waitForComplete()` Promise resolves.
- Do not read animation, bounds or child resources before readiness.
- If the owning scene is replaced first, destroy or detach the late object and
  ignore its completion callback.

## Workflow 3: Tagged event ownership

- Bind on the object or App that owns the behavior.
- Use an explicit tag for long-lived or replaceable behavior.
- Unbind with the same owner, event type, condition and tag at teardown.
- Prefer `once` for one-shot lifecycle signals.
- Do not leave an `update` handler attached after the behavior ends.

## Workflow 4: Destroy and clear

- Call the documented `destroy()` on the object owner.
- Immediately clear the owning reference or remove the object from the active
  collection so later code cannot use a destroyed object.
- Unbind events, stop animations and release DOM resources before or as part of
  teardown when the API requires it.

## Workflow 5: Camera after readiness

- Access the camera through its documented owner path (for example,
  `app.camera`).
- Wait for the target scene/object readiness before fitting or flying.
- Keep camera duration/time and completion field names tied to their exact
  official source; do not merge overloads from different modules.

## Workflow 6: Scene replacement

- Increment a scene generation/token before starting a replacement load.
- Capture the token in every completion path and ignore stale results.
- On replacement failure, roll back the active scene and reset loading state.
- Destroy the old scene and detach listeners only after the new scene is ready,
  unless the official lifecycle requires an earlier release.
- Always cover reject, partial success and `finally` paths.

These workflows are reusable composition rules. They do not authorize an API
whose exact official signature, version scope or runtime compatibility remains
unknown.
