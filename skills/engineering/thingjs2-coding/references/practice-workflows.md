# Reusable ThingJS 2.0 practice workflows

This conversion index is for engineer-maintained material. Read it for `convert`
or `promote`; otherwise load only the matching child workflow under `workflows/`.

## Workflow contract

Every promoted workflow records:

- preconditions, required ThingJS 2.0 runtime scope, exact API owners and sources;
- object, event, DOM and request ownership, plus readiness and cancellation;
- late completion, cleanup, rollback, failure, and project/runtime evidence.

## Corpus-to-workflow index

| Engineer corpus pattern | Child workflow | Promotion gate |
| --- | --- | --- |
| `开发示例/scene-scene.md`, `scene-campus-dynamic-loading.md` | `workflows/scene-loading.md` | Official App/scene evidence plus load, replacement, and failure behavior |
| `开发示例/object-create.md`, `object-destroy.md` | `workflows/entity-lifecycle.md` | Exact constructor/readiness and destroy/lifecycle evidence |
| `开发示例/event-event-control.md` | `workflows/event-ownership.md` | Matching owner, type, condition, tag, and teardown evidence |
| `开发示例/camera-fly.md` | `workflows/camera-animation.md` | Camera owner, readiness order, and version-specific timing evidence |

## Conversion boundary

Classify each source as an API fact candidate, Example, Recipe, Incident, or rejected
record before writing a derivative. Examples are composition/ordering candidates,
never silent signatures; keep fingerprints and private content in the user workspace.

These workflows do not authorize an API whose exact official signature, version
scope, or runtime compatibility remains unknown.

## Minimal conversion ledger contract

The conversion index is a compact, machine-readable ledger rather than a copy of the engineer corpus. Every row carries these minimum fields:

| Field | Minimum meaning |
| --- | --- |
| `source_ref` / `sha256` | Snapshot identity and content fingerprint; require `sources/engineer-corpus/<snapshot_id>/raw/<normalized source_path>` plus matching source identity refs. |
| `domain` | Non-empty corpus semantic classification. When no concrete runtime capability applies, use a governance or review domain; `domain: null` is reserved for task load traces, and an API domain must not be invented. |
| `evidence_class` / `primary_class` | Preserved engineer/project provenance class such as `engineer_example`, `project_practice`, `troubleshooting_incident`, or `review_only`; it is not proof of an API fact. |
| `risk_flags` | Preserved snapshot risk labels; conversion may not clear or replace them from raw content. |
| `semantic_status` | Semantic reading of the source: `candidate`, `incident`, `needs_review`, or `rejected`. |
| `semantic_reason_codes` | Stable reasons for that semantic reading; do not encode a guessed API signature as a reason. |
| `next_evidence_gate` | The smallest missing official, Artifact-Set, Contract, project, or Behavior gate required for reuse. |
| `direct_promotion_decision` | Direct destination decision: `candidate`, `incident`, or `rejected`; `candidate` is not active executable knowledge. |
| `materialization_plan` | `ledger_only` or a narrowly selected dossier plan; materialization never changes evidence authority. |
| binding fields | `version_binding`, `preconditions`, `contract_ids`, `evidence_refs`, `test_refs`, and `binding_state`; source-only rows cannot imply verification. |

For an indexed source, normalize its relative path and require exactly one
manifest/ledger row matching path and SHA-256. Read only that row, preserve its
governance fields, and never infer a domain or overwrite them from content or a
file name. New material is candidate-only and records an explicit admission gate.

In schema 3, derive `version_binding` only from `version_clues` (`clue_only` or
`unbound`). Until a reviewed derivative exists, `preconditions`, `contract_ids`,
and `test_refs` stay empty; `evidence_refs` must uniquely and stably include the
matching source identity (`source_ref` and source SHA), and `binding_state` is
`blocked`, `source-only`, or `rejected`. The immutable-manifest
`promotion_state` allowlist is `indexed_not_promoted`, `excluded_pending_review`,
`needs_split`, or `rejected`; `derived_state` remains exactly `candidate_only`.

Apply the fail-closed mapping: `candidate`→`candidate`, `incident`→`incident`,
and `needs_review`/`rejected`→`rejected`. A `needs_review` source returns only
through a reviewed derivative; `ledger_only` never relaxes this mapping.

`candidate`, `Recipe`, `Incident`, and `rejected` remain separate outcomes;
`Recipe` is not a direct-promotion value. A reusable Recipe/Incident requires a
reviewed derivative with non-empty `preconditions`, `contract_ids`, and
`evidence_refs`; these bind composition/failure but never promote an API record.

`ledger_only` is valid for low-priority or not-yet-gated material: it preserves
provenance and the follow-up gate without a dossier. Do not bulk-materialize it;
it is never a Recipe, Incident recommendation, or official API/Contract fact.

For snapshot diff, compare `source_path` membership plus content, governance,
and binding fields. Added/removed are membership-only; exact `source_ref` changes
between valid snapshot IDs are not governance/binding changes, while a
`version_clues` change is a binding change even when both values are `clue_only`.
Affected knowledge/Contract/evidence/test sets come only from explicit old/new
refs; domain or API names never infer impact.

## Deterministic single-record selection

For one indexed engineer source, run:

```text
python scripts/select_knowledge_record.py --source-root <source-root> --source-file <source-file> --manifest <manifest.json> --ledger <ledger.json>
```

Provide a source root, one source file inside that root, a schema-3 manifest, and
a schema-3 promotion ledger. On success, stdout contains one compact JSON object
with exactly `valid`, `source_path`, `sha256`, `manifest_record`, and
`ledger_record`; the tool reads no adjacent corpus source and writes no file.

Treat every non-zero exit as a stop. The tool writes the stable failure code to
stderr and emits no success JSON when the source escapes the root, either JSON or
schema is invalid, the normalized POSIX path has zero or multiple exact matches,
bytes/SHA-256 drift, manifest/ledger identity or governance conflicts, required
governance is missing, or `official_api_fact` is not `false`. Do not recover by
inferring fields from the source text or by loading the full ledger into context.
