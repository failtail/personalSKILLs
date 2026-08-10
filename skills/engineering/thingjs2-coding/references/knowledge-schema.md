# Lightweight ThingJS 2.0 API cache schema

The registry is a selective cache, not a complete mirror of the public API. Add a
record only when it is used, frequent, high-risk, historically hallucinated,
conflicting, or already verified and worth preserving for future work.

## Canonical identity

Use `kind + fully qualified owner + member name` as the canonical key. Store overloads as signatures within one record. Keep same-name members on different owners separate. Add an alias only when an official source explicitly declares it.

Recommended ID:

```text
thingjs2.api.<fully-qualified-owner>.<member>
```

Do not infer a fully qualified owner from a display heading when the source does not establish it.

## Registry shape

Store build-time canonical records in JSON so validation is deterministic. Generate human-readable Markdown only after canonicalization.

```json
{
  "schema_version": 1,
  "apis": [
    {
      "id": "thingjs2.api.THING.App.load",
      "kind": "method",
      "owner": "THING.App",
      "name": "load",
      "version_scope": "2.x",
      "inclusion_reason": ["used", "verified"],
      "evidence_labels": ["official_verified"],
      "usage_state": "allowed",
      "retrieval_channels": ["official_web"],
      "project_status": "not_tested",
      "last_verified": "YYYY-MM-DD",
      "summary": "One-sentence verified purpose.",
      "signatures": [
        {
          "text": "exact verified signature",
          "source_refs": ["official-api-page-id"]
        }
      ],
      "sources": [
        {
          "ref": "official-api-page-id",
          "source_id": "S1",
          "source_type": "official_api",
          "retrieval_channel": "official_web",
          "url": "exact supporting URL",
          "retrieved_at": "YYYY-MM-DD",
          "version_evidence": "ThingJS 2.0"
        },
        {
          "ref": "context7-retrieval-id",
          "source_id": "S4",
          "source_type": "context7_retrieval",
          "retrieval_channel": "context7",
          "context7_library_id": "/websites/cdn_uino_cn_thingjs_apidocs",
          "url": "https://cdn.uino.cn/thingjs/APIdocs",
          "original_source_url": "exact official URL returned by Context7",
          "provenance_checked": true,
          "retrieved_at": "YYYY-MM-DD",
          "version_evidence": "ThingJS 2.0"
        }
      ],
      "runtime_verifications": [
        {
          "sdk_version": "2.0.13",
          "artifact_sha256": "sha256",
          "status": "supported",
          "evidence_ref": "probe or test artifact"
        }
      ],
      "constraints": [],
      "lifecycle": [],
      "example_refs": [],
      "recipe_refs": [],
      "notes": []
    }
  ]
}
```

The example shows structure, not a verified `App.load` signature. Do not copy placeholder text into usable knowledge.

## Required fields

Every API record requires:

- `id`, `kind`, `owner`, `name`, and `version_scope`
- `inclusion_reason`: one or more of `used`, `frequent`, `high_risk`,
  `hallucination_history`, `conflict`, or `verified`
- at least one evidence label
- `usage_state`: `allowed`, `conditional`, or `blocked`
- `retrieval_channels`, `project_status`, and `last_verified`
- a concise summary
- exact source records
- at least one verified signature before `usage_state` becomes `allowed`
- lifecycle or constraint records when they affect safe implementation

An `allowed` record must contain an official API or official documentation source and must not contain `runtime_conflict`.

Context7 is recorded as a retrieval channel. A Context7 source must retain the
underlying `original_source_url` and the allowlisted library ID. For the approved
ThingJS libraries, a result may satisfy `official_verified` only after the exact
public owner/member/signature and ThingJS 2.0 scope checks pass. Source identity,
reputation or a matching host alone cannot satisfy the label.
Set `provenance_checked: true` only after those checks pass; the validator rejects
Context7-backed `official_verified` records without it.

## Runtime verification states

- `supported`: the identified SDK passed the probe.
- `conflict`: the identified SDK disagreed with the official claim.
- `not_tested`: no runtime conclusion.
- `inconclusive`: the probe could not distinguish support from environment failure.

If any target-project verification is `conflict`, the project Overlay must block that API even when the canonical record remains officially valid.

## Generated Markdown

Group API records by stable class or domain. For each member include:

- conclusion
- exact signature
- parameters and returns
- behavior and constraints
- lifecycle and cleanup
- sources
- referenced Examples and Recipes
- runtime compatibility notes

Do not create one tiny file per API and do not build a single all-API Markdown file.
Do not use cache size or coverage as a completion criterion.

## Deduplication

- Merge matching canonical keys.
- Keep overloads under one entity.
- Preserve all supporting source references.
- Never merge same-name members from different owners.
- Deduplicate examples separately using normalized code plus goal, API set, ordering, scene context, and outcome.
- Keep semantically different workflows as separate Recipes even when they use the same API set.
