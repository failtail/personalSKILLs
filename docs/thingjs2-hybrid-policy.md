# ThingJS 2.0 Hybrid Policy

This is the active public policy for the `thingjs2-coding` Skill. It is a
small workflow contract, not a mirror of the ThingJS API website and not a
replacement for the user's private project knowledge workspace.

## Source roles

| Source or layer | Responsibility | Can define general API truth? |
| --- | --- | --- |
| Controlled official ThingJS 2.0 API/documentation snapshot | Owner, signature, parameters, returns and semantics | Yes, for its controlled version relation |
| Context7 S4/S5 | On-demand retrieval channel for the two approved first-party ThingJS corpora | Yes, only after exact source/owner/member/signature and 2.0-scope checks; retain the original source URL |
| Engineer-maintained corpus supplied by the user | Real recipes, repeated patterns, incidents and practical constraints | No; classify before promotion |
| Internal/project knowledge | Private environment behavior, project compatibility and verified recipes | No; may block a project API |
| Browser Runtime Surface | Descriptor-observed member existence in an exact SDK Artifact Set | Existence only |
| Runtime Behavior Test | One lifecycle, ordering, rendering, readiness, cleanup, or failure scenario | Project behavior only |
| Versioned JSON Contract | Normalized, deduplicated, Artifact-Set-bound machine entry | Derived from controlled evidence; not a raw source |
| Project ThingJS Usage Surface | AST-derived project usage with provenance and resolution status | No; defines validation demand |

The user-provided engineer corpus is especially valuable because it contains
working examples. A document with a ThingJS 2.0 marker and an official example
URL is still classified as an engineering example until the corresponding
official fact and signature are confirmed. This prevents a useful recipe from
silently becoming a universal API claim.

## Retrieval workflow

```text
SDK Artifact Set
        ↓
Browser Runtime Surface (existence only)
        ↓
Controlled official evidence ──→ Versioned JSON Contract
        ↓
Project source ──→ AST Usage Surface ──→ Contract Validator / CI
        ↓
Skill / generated .d.ts / project code
        ↓
Runtime Behavior Tests and Recipe/Incident feedback
```

The Contract is the only machine-consumption entry for the Skill, Validator, CI,
and generated `.d.ts`; it is not the only original fact source. TypeScript
declarations are one-way generated output and never define Contract truth.

Context7 runtime states are `active`, `partial`, `waiting`, `unavailable`, and
`rejected`. The approved libraries are `/websites/thingjs_new` mapped to
`https://docs.thingjs.com/new/documentation/` and
`/websites/cdn_uino_cn_thingjs_apidocs` mapped to
`https://cdn.uino.cn/thingjs/APIdocs/`. A configured library is not automatically
active. A callable result can be promoted to official evidence only when it
preserves the exact first-party URL, public owner/member/signature and ThingJS 2.0
scope. Wrong-owner, `thing_src_*`, private, compatibility and `/uinosoft/t3d.js`
results are blocked. The agent must not claim a Context7 query occurred unless a
callable tool actually returned a result. When the state is anything other than
`active`, use the official web sources and local evidence directly.

Load the Skill's [context7-official-sources.md](../skills/engineering/thingjs2-coding/references/context7-official-sources.md)
and [practice-workflows.md](../skills/engineering/thingjs2-coding/references/practice-workflows.md)
only when the task needs source trust or engineer-pattern mapping; load a matching
child workflow under `references/workflows/` only for a concrete capability. This
keeps the main Skill progressively disclosed without creating a second router.

Trigger official web fallback when Context7 has no result, an incomplete or
truncated result, no original source URL, an ambiguous version, a conflict, or
insufficient context for safe implementation. Official examples demonstrate
composition and ordering but do not silently replace a missing signature.

## Engineer corpus promotion

Classify each supplied document before using it:

- **API fact candidate**: a named member or signature that still needs official
  2.0 confirmation.
- **Recipe**: a complete composition that an engineer used or documented.
- **Incident**: a failure, warning, compatibility note or workaround.
- **Rejected**: 1.x, compatibility, migration, t3d, unknown-version or unsafe
  material.

The corpus should be mined on demand by topic, not copied wholesale into the
public repository. Prefer small, reusable extracts for high-risk/high-frequency
workflows such as scene loading, object creation/completion, event ownership,
camera operations, and object destruction. Keep internal source paths and
business data in the user's local workspace.

The first verified examples in the supplied corpus show a useful pattern:
`THING.App` scene loading returns an asynchronous result, `THING.Entity` accepts
resource and completion options, object events are bound on the object, and
destroyed objects are cleared from the owning reference. These are recipe
signals, not permission to skip official signature and lifecycle checks. The
same corpus also documents compatibility-style `app.create`; the active policy
must not recommend that path when a native `new THING.ClassName(...)` 2.0 path
is available.

## Versioned Contract and lightweight local knowledge

The private workspace may contain:

```text
knowledge/
├── verified/       # public-safe facts or project behavior with evidence
├── api/            # controlled upstream API evidence and snapshots
├── internal/       # private material; never copied to this repository
├── recipes/        # project compositions and preconditions
└── troubleshooting/ # failures, fixes and residual risks
contracts/
└── <sdk-version>/
    └── contract.json # only machine-consumption API entry
project-overlays/
└── <project-id>/
    ├── project-profile.json
    ├── runtime-surface.json
    ├── usage-surface.json
    ├── dynamic-usage-allowlist.json
    └── behavior-tests/
```

The Contract is selective and usage-driven, not a complete encyclopedia. Every
record retains the reason for inclusion, retrieval channel, original source URL,
version relation, Artifact Set binding, state, and last verification. Context7
source identity alone cannot earn a controlled official label.

Project ThingJS Usage Surface is produced primarily through AST analysis. JavaScript,
TypeScript, and Vue `<script>`/`<script setup>` use one Usage Entity model. The
extractor resolves aliases, destructuring, constructor instances, and statically
evaluable computed properties where possible. Production-reachable
`dynamic_unresolved`, `ambiguous`, and parse-failed usage blocks unless a narrow,
evidence-backed allowlist binds the exact Artifact Set. Regex is discovery fallback
only and never creates or replaces verified AST entities.

Private-source deferral is allowed. If an internal page cannot be read in the
current session, continue the public-only track with official web evidence and
mark the private track as `deferred`. Do not infer private behavior, and do not
make internal extraction a prerequisite for public Skill validation.

## Evaluation boundary

Evaluate activation, progressive reference routing, five output-behavior smoke
tests, the Contract pipeline, Runtime Surface, and Runtime Behavior independently. A structural
validation pass cannot prove activation, a correct activation cannot prove minimal
reference loading, and a public-example smoke cannot prove target-project runtime.
Preserve before/after prompt results when changing the description, and require a
load trace for routing tests. Keep private prompts, project runtime output and
internal knowledge in the user's local workspace.

The five output tests remain API retrieval, official example, a simple business
composition, a hallucination trap, and local-knowledge retrieval. Record `PASS`,
`PARTIAL`, `FAIL`, or `NOT_RUN`, plus the retrieval channels, unknown API status,
version pollution, runtime result and notes.

The former full-site inventory, complete public API mirror, large benchmark
matrix and heavy RAG pipeline are historical V1 design ideas. Preserve their
lessons in the process record, but do not make them completion gates for this
Skill.

For target compatibility, a mismatch between the Contract and controlled evidence
for that SDK version blocks. A change seen only on an unversioned latest official
page produces `stale_review`. A newly exposed Runtime Surface member is a candidate
or warning until official identity/signature evidence is controlled; it does not
silently expand the Contract.

## Security boundary

Do not commit the supplied ZIP, internal URLs, private documents, absolute local
paths, project SDK hashes, project overlays, or raw smoke-test/runtime output.
Use a local workspace and a sanitized summary when a fact is genuinely reusable.
