# Resolver v2 Implementation

Status: `IN_PROGRESS`
Tier: `L`
Updated: 2026-08-14

## Purpose

`extract_usage_surface.mjs` produces the AST-derived Project ThingJS Usage
Surface used by Contract validation. Resolver v2 adds a deliberately bounded
module-value pass. It improves traceability for ordinary ESM composition while
keeping uncertain values visible as `ambiguous`, `dynamic_unresolved`, or a
blocking reachability gap.

## Supported value flow

The resolver builds a static import graph and a module export table. Within the
supported boundary it can propagate:

- named imports and exports;
- default imports and default exports;
- namespace imports and namespace member access;
- explicit re-exports (`export { ... } from`) and star re-exports;
- constructor or instance references whose ThingJS owner is already proven by
  local AST evidence or a schema-3 structured Contract return type;
- configured aliases supplied as explicit JSON for `compilerOptions.paths`,
  `resolve.alias`, or `aliases`.

The resolver does not execute Vite/TypeScript configuration, infer types from
Runtime Surface member names, or treat an engineer example as a signature.

## Fixed-point and failure behavior

Export propagation runs for a fixed maximum of eight passes. The output records
`resolver.module_flow_converged`. A stable table sets this flag to `true`; a
cycle or propagation chain that still changes at the boundary sets it to
`false` and adds a production `cross_module_resolution_incomplete` gap. This is
fail-closed: the unresolved graph cannot become a verified ThingJS alias by
reaching the pass limit.

Conflicting exports merge to an ambiguous reference. Factory and callback
returns are not followed because the resolver cannot prove which value was
returned at a call site. Static `await import()` member use is also retained as
ambiguous. Dynamic constructor class maps remain unresolved. These cases are
intentional evidence boundaries, not parser errors.

## Review-only delta mode

`--changed-files <json>` validates the changed-file list, computes the reverse
static dependency closure, and emits entities from that closure. The extractor
still parses the full source inventory to build the module graph; it does not
yet provide content hashing, persisted symbol indexes, or cache invalidation.
Therefore the output marks:

```json
{
  "incremental": {
    "enabled": true,
    "complete_surface": false,
    "restriction": "Delta output is review metadata only; run a full extraction before Contract CI."
  }
}
```

`validate_contract.py` rejects this output with
`incremental_surface_incomplete`. A full extraction remains mandatory for a
Contract release. This distinction preserves correctness while leaving room
for a future hash/cache implementation.

## Deliberate non-goals

The current slice does not implement:

- content-hash or persistent cache incremental builds;
- native Vite/TypeScript config execution or every alias plugin convention;
- general interprocedural call-graph analysis;
- dynamic constructor-to-class maps;
- runtime behavior or lifecycle verification.

The last item remains owned by the independent Behavior Test schema and real
browser runner. Resolver success never changes `behavior_verified`.

## Validation

The synthetic regression covers direct aliases, destructuring, structured
Contract nested owners, named/default/namespace imports, explicit and star
re-exports, conflicting exports, factory returns, static dynamic imports,
non-converged propagation, reverse-dependency delta output, and rejection of an
incomplete delta by Contract validation.

The target ThingJS 2.0.13 project must be re-extracted after this slice. Its
existing release gate remains authoritative: improved resolution may reduce
ambiguity, but it cannot waive missing Contract entries, production unresolved
usage, Artifact Set mismatch, or missing behavior evidence.
