# Behavior Test Schema Implementation

## Scope

This checkpoint adds a deterministic validator for independent lifecycle
evidence. It is a harness boundary, not a ThingJS runtime runner and not a
Contract promotion shortcut.

## Required evidence

Each record binds one exact Artifact Set, canonical Contract references, a
scenario and stimulus, ordered trace events, resource/listener ledgers, effects,
machine assertions, cleanup results, and an evidence reference. Ownership is
explicit on resources, listeners, effects, and operations.

## Invariants

- Trace sequence values are positive and unique.
- Resource release and listener unbind follow creation/bind.
- A cancelled operation cannot produce an accepted effect.
- A passed result has only passed assertions, no cleanup residuals, and
  idempotent cleanup.
- The schema keeps late completion observable even when the underlying async
  operation settles successfully; acceptance is a separate field.

## Validation boundary

`test_behavior_test_schema.py` uses a fake scene-replacement trace and a
negative stale-effect mutation. Passing this test proves the validator catches
the modeled invariants only. Real browser lifecycle tests are still required for
`App.load`, Entity readiness, scene replacement, and App teardown, and their
results must remain separate from API owner/signature evidence.
