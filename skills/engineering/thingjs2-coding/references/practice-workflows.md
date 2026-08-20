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

The conversion index is a compact, machine-readable ledger rather than a copy of
the engineer corpus. Every row carries these minimum fields:

| Field | Minimum meaning |
| --- | --- |
| `source_ref` / `sha256` | Stable source reference and content fingerprint; keep raw text and private paths outside the public Skill. |
| `domain` | Non-empty corpus semantic classification. When no concrete runtime capability applies, use a governance or review domain; `domain: null` is reserved for task load traces, and an API domain must not be invented. |
| `evidence_class` / `primary_class` | Preserved engineer/project provenance class such as `engineer_example`, `project_practice`, `troubleshooting_incident`, or `review_only`; it is not proof of an API fact. |
| `risk_flags` | Preserved snapshot risk labels; conversion may not clear or replace them from raw content. |
| `semantic_status` | Semantic reading of the source: `candidate`, `incident`, `needs_review`, or `rejected`. |
| `semantic_reason_codes` | Stable reasons for that semantic reading; do not encode a guessed API signature as a reason. |
| `next_evidence_gate` | The smallest missing official, Artifact-Set, Contract, project, or Behavior gate required for reuse. |
| `direct_promotion_decision` | Direct destination decision: `candidate`, `incident`, or `rejected`; `candidate` is not active executable knowledge. |
| `materialization_plan` | `ledger_only` or a narrowly selected dossier plan; materialization never changes evidence authority. |

For a source in an indexed snapshot, normalize its relative source path and
require exactly one manifest/promotion-ledger row matching both that path and its
SHA-256. Read only that matching row, not the corpus, and preserve its `domain`,
`evidence_class`/`primary_class`, `risk_flags`, semantic/direct decision, reason
codes, next gate, and materialization plan. Do not infer a replacement domain or
overwrite governance fields from raw content or a file name. New unindexed
material may create only a candidate row and must record an explicit
manifest/index admission gate in `next_evidence_gate`.

Apply the fail-closed mapping used by conversion tooling: `candidate` maps to
direct `candidate`, `incident` maps to direct `incident`, and `needs_review` or
`rejected` maps to direct `rejected`. A `needs_review` source may return only
through a separately reviewed derivative. A `ledger_only` materialization plan
does not relax or override this mapping.

`candidate`, `Recipe`, `Incident`, and `rejected` remain separate semantic or
knowledge outcomes. `Recipe` is not a `direct_promotion_decision` value; it is a
candidate-derived knowledge type only after the additional promotion gate below.
Before a Recipe or Incident is actually promoted into reusable project knowledge,
the row or its reviewed derivative must additionally provide non-empty
`preconditions`, `contract_ids`, and `evidence_refs`. These fields bind the
composition or failure to its prerequisites, the exact Contract records it uses,
and the evidence that supports the claimed outcome; they do not promote an API
record by themselves.

`ledger_only` is a valid final result for low-priority material or material that
has not passed its next evidence gate. It preserves provenance, reasons, and the
follow-up gate without consuming context with a dossier. Do not bulk-materialize
remaining/low-priority ledger-only records merely to make the corpus appear complete;
selective materialization is a policy decision, not a coverage metric. A
ledger-only row must not be read as a Recipe, an Incident recommendation, or an
official API/Contract fact.

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
