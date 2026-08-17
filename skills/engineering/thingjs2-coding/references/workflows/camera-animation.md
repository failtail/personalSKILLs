# ThingJS 2.0 camera-animation workflow

Load this child workflow when camera movement, fitting, animation, or timing
fields are part of the request.

## Readiness and ownership

- Access the camera through its documented owner path, such as `app.camera`.
- Wait for the target scene/object readiness before fitting or flying.
- Assign ownership for camera requests and stop or invalidate them at teardown
  when the target scene is replaced.

## Timing conflict boundary

- Keep camera duration/time and completion field names tied to their exact
  official source.
- Treat `duration/onComplete` and `time/complete` as a module or overload
  conflict; never merge them from memory or from a different owner.
- State animation time units when the API source does not make them explicit.

The bundle provides ordering and risk checks only. It does not promote a
camera or animation member into the Contract.
