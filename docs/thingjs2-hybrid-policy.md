# ThingJS 2.0 Hybrid Policy

This is the active public policy for the `thingjs2-coding` Skill. It is a
small workflow contract, not a mirror of the ThingJS API website and not a
replacement for the user's private project knowledge workspace.

## Source roles

| Source or layer | Responsibility | Can define general API truth? |
| --- | --- | --- |
| Official ThingJS 2.0 API, documentation, examples | Existence, signatures, public behavior, composition and ordering | Yes |
| Context7 S4/S5 | On-demand retrieval channel for the two approved first-party ThingJS corpora | Yes, only after exact source/owner/member/signature and 2.0-scope checks; retain the original source URL |
| Engineer-maintained corpus supplied by the user | Real recipes, repeated patterns, incidents and practical constraints | No; classify before promotion |
| Internal/project knowledge | Private environment behavior, project compatibility and verified recipes | No; may block a project API |
| Current project runtime | SDK fingerprint and real behavior in one project | No; cannot redefine the public API |

The user-provided engineer corpus is especially valuable because it contains
working examples. A document with a ThingJS 2.0 marker and an official example
URL is still classified as an engineering example until the corresponding
official fact and signature are confirmed. This prevents a useful recipe from
silently becoming a universal API claim.

## Retrieval workflow

```text
Project profile / Overlay
        ↓
Local Verified Recipe (candidate only)
        ↓
Context7, only when runtime = active
        ↓
Official web fallback when Context7 is unavailable or incomplete
        ↓
Internal/project knowledge for private constraints and conflicts
        ↓
Code generation
        ↓
API evidence audit
        ↓
Lifecycle, async, event and cleanup audit
        ↓
Runtime validation and knowledge feedback
```

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
only when the task needs source trust or engineer-pattern mapping; this keeps the
main Skill progressively disclosed.

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

## Lightweight local knowledge

The private workspace may contain:

```text
knowledge/
├── verified/       # public-safe facts or project behavior with evidence
├── api-cache/      # used, frequent, high-risk, conflicting or hallucination-prone APIs
├── internal/       # private material; never copied to this repository
├── recipes/        # project compositions and preconditions
└── troubleshooting/ # failures, fixes and residual risks
```

The API cache is not a complete encyclopedia. Every cache record should retain
the reason for inclusion, retrieval channel, original source URL, version scope,
project status and last verification. Context7 alone cannot earn an
`official_verified` label.

## Evaluation boundary

Use five active smoke tests: API retrieval, official example, a simple business
composition, a hallucination trap, and local-knowledge retrieval. Record only
`PASS`, `PARTIAL`, or `FAIL`, plus the retrieval channels, unknown API status,
version pollution, runtime result and notes. Keep private prompts, project
runtime output and internal knowledge in the user's local workspace.

The former full-site inventory, complete public API mirror, large benchmark
matrix and heavy RAG pipeline are historical V1 design ideas. Preserve their
lessons in the process record, but do not make them completion gates for this
Skill.

## Security boundary

Do not commit the supplied ZIP, internal URLs, private documents, absolute local
paths, project SDK hashes, project overlays, or raw smoke-test/runtime output.
Use a local workspace and a sanitized summary when a fact is genuinely reusable.
