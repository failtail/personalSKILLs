# Project Overlay

A Project Overlay records compatibility and verified practice for one repository without redefining general ThingJS 2.0 truth.

## User-level layout

```text
<codex-home>/thingjs2-ai/
  project-index.json
  CURRENT_STATE.md
  contracts/
    <sdk-version>/
      contract.json
  CONTEXT7_SOURCES.md
  knowledge/
    verified/
    api-cache/
    internal/
    recipes/
    troubleshooting/
  project-overlays/
    <project-id>/
      project-profile.json
      runtime-surface.json
      usage-surface.json
      dynamic-usage-allowlist.json
      contract-validation.json
      api-overrides.json
      incidents.md
      behavior-tests/
      benchmarks.json
      recipes/
```

The local workspace is the active runtime state layer. The versioned Contract is
the only machine-consumption entry for Skill, Validator, CI, and generated `.d.ts`;
official snapshots and runtime evidence remain independent upstream sources. Keep public source policy
and workflow rules in this Skill repository; keep Context7 availability, private
sources, supplied engineer documents, SDK fingerprints, Recipes, Incidents and
runtime results in the user-level workspace. Do not mirror the complete public API
or commit the local workspace to a Skill collection.

`project-index.json` maps a normalized target project root to its Overlay ID. Keep all generated Skill and Knowledge artifacts in this user-level workspace; do not add them to the target application repository. Only create files that contain real project evidence, and do not copy the general knowledge base into every Overlay.

## Precedence

1. General official facts define the canonical API.
2. A project runtime conflict blocks that API for the project.
3. Runtime Surface may prove member existence only. Behavior-dependent claims need
   an independent Runtime Behavior Test for the same Artifact Set.
4. A project may add stricter constraints or required wrappers.
5. A project may not silently change an official signature. Record a conflict instead.
6. A verified project Recipe may guide composition only when all of its APIs remain eligible;
   an engineer document or unverified “verified” claim remains a Recipe candidate.
7. An Incident warns against a failed approach but does not prove the replacement is official.

## Project profile

Generate the initial profile with `scripts/preflight.py` and write it to the user-level Overlay. Keep:

- project identifier and normalized target root
- local SDK artifact paths, roles, hashes, version, build time, and SDK commit when available
- explicit `THING.*` token inventory as candidates only
- warnings for missing or ambiguous local SDK evidence
- profile generation time and schema version

Regenerate the profile when any core, campus, Earth, or plugin artifact hash changes.
The complete role-and-hash set determines `artifact_set_id`; a core-only hash cannot
stand in for an application that loads plugins.

## Generated project evidence

- Generate Runtime Surface in a real browser after loading exact artifacts in
  dependency order. Discard a capture when any artifact load throws.
- Generate Project ThingJS Usage Surface primarily through AST analysis for
  JavaScript, TypeScript, and Vue script blocks. Use Regex only for discovery after
  parse failure or an unknown pattern.
- Mark production reachability using configured entries and a static import graph.
  Treat it as an explicit initial approximation, not a complete runtime call graph.
- Block unresolved imports reachable from a production entry. Configure explicit
  entries or extend project alias resolution before treating disconnected files as
  non-production.
- Block production-reachable unresolved usage unless an active allowlist entry is
  limited to exact Usage IDs, matches the recorded expression,
  is evidence-backed, and binds the exact `artifact_set_id`.

## Security

- Keep internal URLs, private API text, credentials, model URLs, and business identifiers in the project Overlay.
- Do not bundle internal content into the reusable Skill.
- Promote a Recipe into general knowledge only after removing project secrets and verifying that it relies solely on approved ThingJS 2.0 APIs.

## Staleness

Treat source lines, test counts, screenshots, and runtime statements as time-sensitive. Attach a Git commit or artifact hash. Recheck evidence when the repository head, SDK hash, or relevant source file changes.
