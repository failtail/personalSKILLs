# Project Overlay

A Project Overlay records compatibility and verified practice for one repository without redefining general ThingJS 2.0 truth.

## User-level layout

```text
<codex-home>/thingjs2-ai/
  project-index.json
  project-overlays/
    <project-id>/
      project-profile.json
      api-overrides.json
      incidents.md
      benchmarks.json
      recipes/
```

`project-index.json` maps a normalized target project root to its Overlay ID. Keep all generated Skill and Knowledge artifacts in this user-level workspace; do not add them to the target application repository. Only create files that contain real project evidence, and do not copy the general knowledge base into every Overlay.

## Precedence

1. General official facts define the canonical API.
2. A project runtime conflict blocks that API for the project.
3. A project may add stricter constraints or required wrappers.
4. A project may not silently change an official signature. Record a conflict instead.
5. A verified project Recipe may guide composition only when all of its APIs remain eligible.
6. An Incident warns against a failed approach but does not prove the replacement is official.

## Project profile

Generate the initial profile with `scripts/preflight.py` and write it to the user-level Overlay. Keep:

- project identifier and normalized target root
- local SDK artifact paths, hashes, version, build time, and SDK commit when available
- explicit `THING.*` token inventory as candidates only
- warnings for missing or ambiguous local SDK evidence
- profile generation time and schema version

Regenerate the profile when the SDK artifact hash changes.

## Security

- Keep internal URLs, private API text, credentials, model URLs, and business identifiers in the project Overlay.
- Do not bundle internal content into the reusable Skill.
- Promote a Recipe into general knowledge only after removing project secrets and verifying that it relies solely on approved ThingJS 2.0 APIs.

## Staleness

Treat source lines, test counts, screenshots, and runtime statements as time-sensitive. Attach a Git commit or artifact hash. Recheck evidence when the repository head, SDK hash, or relevant source file changes.
