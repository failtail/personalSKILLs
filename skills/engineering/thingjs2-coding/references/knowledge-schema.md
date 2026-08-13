# Versioned ThingJS 2.0 Contract schema

The versioned JSON Contract is the only machine-consumption entry for the Skill,
Validator, CI, and generated TypeScript declarations. It is not the only raw fact
source. Controlled official evidence and exact-SDK Runtime Surface evidence remain
independent upstream inputs; Recipes and Incidents remain downstream knowledge.

The Contract is selective and usage-driven. Do not turn it into a complete website
mirror. Add APIs required by Project ThingJS Usage Surface, frequent or high-risk
workflows, conflicts, and deliberate reusable coverage.

## Canonical identity

Use `kind + fully qualified owner + member name` as the canonical key. Store
overloads inside one record. Keep same-name members on different owners separate.
Add aliases only when controlled official evidence explicitly declares them.

Recommended ID:

```text
thingjs2.api.<fully-qualified-owner>.<member>
```

Do not infer an owner from a display heading, engineer example, runtime instance,
or same-name member on another class.

## Root shape

Schema version 2 binds every record to one immutable SDK Artifact Set:

```json
{
  "schema_version": 2,
  "contract_id": "thingjs-<sdk-version>-<artifact-set-prefix>",
  "sdk_version": "2.0.13",
  "sdk_binding": {
    "artifact_set_id": "sha256:<digest-of-normalized-role-path-hash-list>",
    "artifacts": [
      {
        "role": "core",
        "relative_path": "path/inside/project/thing.min.js",
        "sha256": "<artifact-sha256>"
      },
      {
        "role": "campus",
        "relative_path": "path/inside/project/thing.campus.min.js",
        "sha256": "<artifact-sha256>"
      }
    ]
  },
  "evidence_policy": {
    "latest_official_change": "stale_review",
    "controlled_target_mismatch": "block",
    "runtime_surface_scope": "existence_only"
  },
  "apis": []
}
```

Paths above are placeholders. Keep real local paths and hashes only in authorized
user/project storage.

## API record shape

```json
{
  "id": "thingjs2.api.THING.App.load",
  "canonical_key": "method|THING.App|load",
  "kind": "method",
  "owner": "THING.App",
  "name": "load",
  "version_scope": "2.0.13",
  "contract_state": "documented",
  "usage_state": "conditional",
  "summary": "One-sentence controlled purpose.",
  "signatures": [
    {
      "text": "exact controlled signature",
      "parameters": [],
      "return_type": null,
      "source_refs": ["official-api-page-id"]
    }
  ],
  "sources": [
    {
      "ref": "official-api-page-id",
      "source_type": "official_api",
      "retrieval_channel": "official_web",
      "url": "exact supporting URL",
      "retrieved_at": "YYYY-MM-DD",
      "version_relation": "exact | compatible_range | unversioned_latest",
      "content_sha256": "required for exact/compatible_range; null for unversioned_latest"
    }
  ],
  "existence_evidence": [
    {
      "artifact_set_id": "sha256:<artifact-set-id>",
      "surface_ref": "runtime-surface.json",
      "status": "present"
    }
  ],
  "evidence_conflicts": [
    {
      "status": "mismatch",
      "version_relation": "exact | compatible_range | unversioned_latest",
      "evidence_ref": "controlled-comparison-record"
    }
  ],
  "behavior_evidence": [
    {
      "artifact_set_id": "sha256:<artifact-set-id>",
      "test_ref": "behavior-tests/<case>.json",
      "status": "passed",
      "scenario": "specific lifecycle or rendering behavior"
    }
  ],
  "constraints": [],
  "lifecycle": [],
  "example_refs": [],
  "recipe_refs": [],
  "notes": []
}
```

The example shows structure, not a verified `App.load` signature. Never promote
placeholder fields into executable knowledge.

## Contract states

| State | Minimum evidence | Allowed claim |
| --- | --- | --- |
| `documented` | Controlled official owner/signature/semantics | Documented API; target existence unknown |
| `existence_verified` | `documented` plus matching Runtime Surface | Member exists in the exact Artifact Set |
| `behavior_verified` | `existence_verified` plus passing behavior test | Only the tested behavior and preconditions |
| `blocked` | Controlled mismatch, absent required member, failed behavior, or explicit project decision | No executable use for that scope |

Runtime Surface cannot supply parameter or return types. A behavior test cannot
repair a missing official owner/signature. An unversioned latest official change
adds `stale_review`; only controlled evidence for the target SDK can create a
blocking semantic mismatch.

## Required fields and promotion

Every record requires canonical identity, version scope, Contract and usage state,
summary, controlled source records, and signature text. A record cannot become:

- `existence_verified` without matching `artifact_set_id` Runtime Surface evidence;
- `behavior_verified` without a separate exact-Artifact-Set behavior record;
- executable when `usage_state` is `blocked`;
- a structured `.d.ts` input while parameter or return types remain unresolved.

Context7 is a retrieval channel, not an automatic evidence label. Retain its
approved library ID and the original official URL. Accept a result only after exact
public owner/member/signature and ThingJS 2.0 scope checks.

## Derived outputs

Generate human-readable Markdown and `.d.ts` only from the Contract. Generated
declarations are disposable outputs: verify their source Contract ID/hash and never
ingest them back into the Contract. Omit text-only or unresolved signatures rather
than inventing types.

## Deduplication

- Merge matching canonical keys.
- Keep overloads under one entity.
- Preserve all controlled source and version-relation records.
- Never merge same-name members from different owners.
- Keep existence and behavior evidence separate.
- Deduplicate Examples by normalized code, goal, API set, ordering, scene context,
  and outcome.
- Keep semantically different Recipes separate even when they use the same API set.

## Knowledge outside the Contract

Engineer/project documents do not define APIs. Store reusable compositions as
Recipes, failures and ambiguity as Incidents/Troubleshooting, and frequently asked
operational answers as FAQ. Each may reference Contract API IDs, but none may mutate
an owner, signature, parameter, return type, or Contract state without controlled
evidence and the promotion workflow.
