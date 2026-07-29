# Commenting Examples

Use these examples to explain a decision, boundary, unit, or lifecycle rule. Keep comments shorter than the examples when the local code needs less context.

## Good And Bad Comments

Bad: repeats syntax and becomes stale without helping a maintainer.

```js
// Set the speed to 8.
const DRIVING_SPEED = 8

// Move the car.
moveCar(start, end, progress)
```

Good: records the unit and the visible behavior that depends on it.

```js
// Keep approach and gate-crossing speed equal (meters/second) so the vehicle
// does not appear to accelerate when the gate animation finishes.
const DRIVING_SPEED = 8
```

Bad: describes a loop but hides the ownership requirement.

```js
// Clear the timer.
clearInterval(timer)
```

Good: protects the actual lifecycle invariant.

```js
// The demo owns this timer; release it before rebuilding the scene so a stale
// callback cannot move a destroyed vehicle.
clearInterval(demoTimer)
```

Bad: says what an obvious branch does.

```js
if (!slot) {
  return
}
```

Good: records an ordering rule that is not visible in the condition.

```js
// Allocate the first matching free slot, not a random one, so the route target
// remains stable from assignment through final visual alignment.
if (!slot) {
  return
}
```

## Change-Tier Examples

| Tier | Example | Appropriate annotation |
| --- | --- | --- |
| `S` | Correct a one-off UI label or a local default value | Explain only a surprising business meaning or unit; no separate document. |
| `M` | Add a moving vehicle flow across a scene system and a menu controller | Comment state transitions, route-coordinate conventions, cleanup ownership, and non-obvious timing decisions; summarize the flow in the handoff. |
| `L` | Replace a shared authentication contract or introduce a persisted job workflow | Document public behavior, state/data flow, failure handling, compatibility, and the design decision in the repository's implementation document. |

## Project-Scale Examples

For a one-file tool, a comment next to a retry limit can be enough:

```python
# Cap retries at 3 to keep a failed CLI command under the caller's 30-second timeout.
MAX_RETRIES = 3
```

For a product feature spanning scene objects and menu state, document the boundary where the menu activates the system and the system owns created entities. For a public SDK, add concise API documentation describing error semantics and compatibility, not internal line-by-line implementation details.

## Urgent-Fix Example

An urgent cleanup fix can stay small while preserving the key safety fact:

```ts
// Cancel the previous request before replacing it; late responses must not
// overwrite the newly selected account.
activeRequest?.abort()
```

The handoff should state the behavior fixed, validation performed, residual risk, and a follow-up location if broader design documentation remains necessary.
