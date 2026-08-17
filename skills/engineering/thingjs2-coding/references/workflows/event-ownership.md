# ThingJS 2.0 event-ownership workflow

Load this child workflow when event binding, unbinding, repeated listeners, or
owner teardown is part of the request.

- Bind on the object or App that owns the behavior.
- Use an explicit tag for long-lived or replaceable behavior.
- Unbind with the same owner, event type, condition, and tag at teardown.
- Prefer `once` for one-shot lifecycle signals.
- Do not leave an `update` handler attached after the behavior ends.

This workflow governs ownership and cleanup only. It does not establish an
event signature or authorize an event member without exact Contract evidence.
