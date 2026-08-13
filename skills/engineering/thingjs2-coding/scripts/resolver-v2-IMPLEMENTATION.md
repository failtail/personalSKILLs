# Resolver v2 Implementation

## Scope

This checkpoint implements the first safe B3 slice: nested instance owner
resolution driven by schema-3 structured Contract return types, plus explicit
JSON alias profiles for project reachability. It does not infer types from
Runtime Surface or execute arbitrary Vite/TypeScript configuration.

## Boundary

- `extract_usage_surface.mjs --contract` indexes only `existence_verified` or
  `behavior_verified` method/property records with structured return types.
- Only `reference` and `promise(value=reference)` descriptors whose names are
  qualified `THING.*` owners can promote a nested instance owner.
- Schema-2 and legacy text signatures produce an empty Contract type index; the
  existing conservative ambiguity behavior remains active.
- `--alias-config` accepts JSON profiles containing `compilerOptions.paths`,
  `resolve.alias`, or `aliases`. The extractor resolves the longest matching
  prefix and never evaluates JavaScript configuration.

## Flow

1. Load the pinned Contract and build a verified structured-return index.
2. Resolve local aliases and constructor instances as before.
3. When a property or method return is a controlled `THING.*` reference, carry
   that owner into the next member access or call result.
4. Resolve configured aliases in the static import graph and retain unresolved
   production edges as blocking reachability gaps.
5. Keep the existing source-location/expression-based Usage ID stable and report
   resolver mode and limitations in the Usage Surface.

## Validation

`test_contract_pipeline.py` covers `entity.scene.load()`,
`entity.getScene().load()`, configured alias reachability, dynamic blocking,
and legacy behavior. The test uses a synthetic schema-3 Contract and does not
promote the fixture into user knowledge.

## Remaining B3 work

Bounded cross-module value flow, re-export/factory/callback propagation, direct
Vite/TS config adapters, changed-files incremental extraction, and explicit
dynamic-constructor class maps remain open. They require separate evidence and
must not be approximated by broad aliasing.
