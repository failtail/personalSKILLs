# ThingJS 2.0 coding standards

Use this reference when implementing or reviewing code. It defines behavior and
evidence boundaries; it does not authorize an API whose official signature has
not been verified.

## Responsibility boundary

Act as a ThingJS 2.0 three-dimensional frontend coding specialist: implement,
debug, review, and refactor `THING` code using verified public evidence. Do not
mix ThingJS 1.x, Compatibility, migration, t3d, or host-framework architecture
into a 2.0 result.

## Required implementation behavior

- Keep complete object paths and verified owners; do not rename a member because
  a similar path appears more familiar.
- Declare every variable or show how it is obtained. Do not leave `app`, `map`,
  `layer`, or queried objects unexplained.
- Copy parameter order, types, optionality, return values, and async variants
  from the matching API record. Do not add undocumented callbacks or convert
  positional arguments into object options.
- Assign ownership to created objects, event handlers, animations, timers,
  camera references, DOM nodes, and asynchronous requests.
- On scene replacement, cancellation, or destruction, guard late async results
  and clean the owner’s listeners, timers, animations, and references.
- State coordinate frames, distance/angle units, and animation time units when
  the API evidence does not make them explicit.

## Final audit

Inventory every ThingJS constructor, method, property, enum, and event in the
diff. Remove blocked, private, compatibility, guessed, and unresolved members.
Run the smallest real browser smoke test that proves lifecycle behavior; a build,
mock, or Git commit is not engine-runtime evidence.

