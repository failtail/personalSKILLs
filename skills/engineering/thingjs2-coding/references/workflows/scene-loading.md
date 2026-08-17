# ThingJS 2.0 scene-loading workflow

Load this child workflow when App bootstrap, scene loading, scene replacement,
or loading cancellation is part of the request.

## App bootstrap and load

- Create the App through the native 2.0 constructor.
- Keep the App as the owner of scene listeners and loaded resources.
- Await the documented load Promise or use the documented completion callback;
  do not mix historical callback names without evidence.
- On failure, surface the error and restore loading state in `finally`.
- Dispose the App only from its owner boundary.

## Scene replacement

- Increment a scene generation/token before starting a replacement load.
- Capture the token in every completion path and ignore stale results.
- On replacement failure, roll back the active scene and reset loading state.
- Destroy the old scene and detach listeners only after the new scene is ready,
  unless the official lifecycle requires an earlier release.
- Cover reject, partial success, cancellation, and `finally` paths.

These are composition rules only. Contract and independent Behavior evidence
still decide whether a concrete member may be used.
