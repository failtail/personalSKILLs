# ThingJS 2.0 entity-lifecycle workflow

Load this child workflow when Entity/object creation, readiness, destroy, or
teardown is part of the request.

## Entity readiness

- Create the Entity with the documented resource URL and options.
- Treat the instance as not ready until the documented completion signal or
  `waitForComplete()` Promise resolves.
- Do not read animation, bounds, or child resources before readiness.
- If the owning scene is replaced first, destroy or detach the late object and
  ignore its completion callback.

## Destroy and clear

- Call the documented `destroy()` on the object owner.
- Immediately clear the owning reference or remove the object from the active
  collection so later code cannot use a destroyed object.
- Unbind events, stop animations, and release DOM resources before or as part
  of teardown when the API requires it.

These patterns describe ownership and failure boundaries; Contract and
independent Behavior evidence still decide whether a concrete member may be
used.
