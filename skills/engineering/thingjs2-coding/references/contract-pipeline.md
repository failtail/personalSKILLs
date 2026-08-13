# ThingJS versioned Contract pipeline

Use this reference when a task must prove that project code is compatible with a
specific local ThingJS SDK artifact set. The Contract is the only machine-consumption
entry for Skill, Validator, CI, and generated declarations. It is not the only raw
fact source.

## Evidence flow

```text
Controlled official evidence ──→ owner, signature, parameters, returns, semantics
                                      │
SDK Artifact Set ─→ Browser Runtime Surface ─→ member existence
                                      │
                                      ▼
                         Versioned JSON Contract
                                      │
                ┌─────────────────────┼─────────────────────┐
                ▼                     ▼                     ▼
              Skill               Validator              .d.ts
                                      │
                                      ▼
                    Project ThingJS Usage Surface
                                      │
                                      ▼
                                     CI
```

Official evidence and Runtime Surface are independent inputs. Descriptor inspection
cannot define signatures or behavior. Official documentation cannot prove that a
member is shipped in the target project's exact artifact set.

## Canonical terms

- **SDK Artifact Set**: ordered roles and immutable SHA-256 fingerprints for the
  core SDK and loaded plugins. Identity sorting is deterministic; browser execution
  order remains `core` before dependent plugins.
- **Controlled official evidence**: an exact official source record with retrieval
  time, original URL, version relation, and a content SHA-256 snapshot for
  `exact`/`compatible_range` claims.
- **Runtime Surface**: browser descriptor evidence that a namespace, constructor,
  static member, prototype member, or inheritance edge exists.
- **Runtime Behavior Test**: an independent test that exercises required scene,
  lifecycle, ordering, cleanup, rendering, or failure behavior.
- **Versioned JSON Contract**: normalized and deduplicated records bound to one
  SDK Artifact Set.
- **Project ThingJS Usage Surface**: AST-derived, source-traceable ThingJS usage
  entities reachable from configured production entries.

## Evidence states

Use the following Contract states without collapsing their meanings:

| State | Required evidence |
| --- | --- |
| `documented` | Controlled official API semantics; target existence not observed |
| `existence_verified` | `documented` plus matching Browser Runtime Surface |
| `behavior_verified` | `existence_verified` plus a recorded Runtime Behavior Test |
| `blocked` | A version conflict, missing required member, failed behavior, or explicit project block |

An unversioned latest official page may trigger `stale_review`; it must not directly
invalidate a Contract pinned to another SDK build. Only evidence controlled for the
target SDK version can produce a blocking semantic mismatch.

## Runtime Surface rules

Run `runtime_surface_probe.js` inside a real browser after loading the exact local
artifacts in dependency order. Attach the SDK version, artifact roles, paths and
SHA-256 values to the result. Keep the result in the user-level Project Overlay.

The probe:

- reads property descriptors without invoking constructors, getters or methods;
- records constructors, namespace/static members, direct prototype members and
  inheritance edges;
- excludes underscore-prefixed members from the active public candidate surface;
- proves existence only;
- does not prove a signature, parameter type, return value, readiness, scene
  behavior, cleanup, rendering result, or API support promise.

If any artifact throws while loading, the capture fails. Do not attach all Artifact
Set hashes to a partial Surface.

## Project Usage Surface rules

Generate Usage Surface with `extract_usage_surface.mjs`.

- JavaScript and TypeScript use @babel/parser.
- Vue files use @vue/compiler-sfc to extract `<script>` and `<script setup>`,
  then use the same Babel analysis and Usage Entity schema.
- Resolve direct `THING` paths, local aliases, destructuring, constructor instances,
  and statically evaluable computed properties.
- Use a static module import graph for initial production reachability.
- Resolve relative, project-root, `@/`-to-`src`, and `~/`-to-root import forms.
  A production-reachable unresolved local or dynamic import is a blocking
  reachability gap; projects with other aliases must pass explicit entries or
  extend the resolver before relying on non-production classification.
- Exclude dependency, build, coverage, VCS, agent, and generated reference-worktree
  directories from the source inventory; these are evidence/tooling inputs, not
  application source.
- Do not claim complete cross-module value flow or runtime call-graph analysis.
- Keep lexical flow conservative: conflicting local aliases become `ambiguous`,
  and imported values do not inherit a ThingJS owner without local provenance.

Each Usage Entity records canonical owner/member when resolved, access type,
argument shape, source location, alias/destructuring provenance, resolution status,
and production reachability.

Resolution states are:

- `resolved`
- `resolved_inherited`
- `ambiguous`
- `dynamic_unresolved`
- `parse_failed`

Regex output is stored only under `discovery_findings`. It cannot create a verified
Usage Entity and cannot override AST output.

## Allowlist boundary

A production-reachable `dynamic_unresolved`, `ambiguous`, or `parse_failed` result
blocks CI by default. An exception must bind:

- the exact `artifact_set_id`;
- one or more exact Usage IDs;
- the exact normalized dynamic expression;
- a reason and evidence references;
- active status.

Never bulk-allow unresolved files merely to make CI green.

## CI sequence

Use `run_contract_ci.py` after a Contract and Runtime Surface have been reviewed:

```powershell
python scripts/run_contract_ci.py `
  --project-root <project-root> `
  --entry <optional-production-entry> `
  --parser-root <node-project-with-parsers> `
  --contract <versioned-contract.json> `
  --runtime-surface <runtime-surface.json> `
  --allowlist <optional-allowlist.json> `
  --output-dir <ci-evidence-dir>
```

The command:

1. fingerprints the current core/plugin Artifact Set;
2. regenerates the AST Usage Surface;
3. compares current artifacts, Runtime Surface, Contract and project usage;
4. writes machine-readable reports;
5. returns non-zero on a blocking inconsistency.

Block when:

- current artifact SHA values differ from the Contract;
- Contract and Runtime Surface bind different Artifact Sets;
- an `existence_verified` or `behavior_verified` member is absent;
- production code uses an API missing from, or blocked by, the Contract;
- production unresolved usage lacks an exact allowlist;
- the production entry/import graph has an unresolved local or dynamic edge;
- a release-required Runtime Behavior Test has not passed.

Warn, but do not block solely because:

- an unversioned latest official page changed;
- Runtime Surface exposes a new member not used by the project;
- Regex found an unmodeled token outside verified AST entities;
- a parse failure or unknown usage is outside the production import graph.

## Usage Promotion Queue

Use `scripts/build_usage_promotion_queue.py` after the Usage Surface, pinned
Contract, Runtime Surface, and optional legacy API Cache are available. The
script groups only production-reachable `resolved`/`resolved_inherited` Usage
Entities whose canonical `kind|owner|member` is absent from the Contract. It
retains Usage IDs and source locations, counts files and calls, and attaches
Runtime existence, official-evidence status, domain triage, and lifecycle-risk
metadata before producing JSON and Markdown.

Regex findings, non-production tokens, ambiguous/dynamic/parse-failed entities,
and API records already covered through the Runtime inheritance graph are not
promotion candidates. The output is a deterministic review queue, not a
Contract mutation or a claim that a member is safe to execute. Runtime Surface
still proves existence only; official owner/signature evidence and independent
behavior tests remain separate gates.

## TypeScript declaration boundary

Generate `.d.ts` only from structured, verified Contract signatures. Runtime
Surface cannot supply parameter or return types. A handwritten declaration cannot
modify the Contract and must fail a generated-output hash check. Records with only
text signatures or unresolved types remain omitted until their structured official
evidence is controlled.

## Storage boundary

Commit this reusable workflow and scripts to the public Skill. Keep exact SDK
hashes, project roots, Usage Surface, Runtime Surface, allowlists, behavior logs,
private sources, and generated project declarations in the user-level workspace
or target project's authorized CI evidence storage.
