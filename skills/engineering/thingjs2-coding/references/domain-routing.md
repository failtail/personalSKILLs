# ThingJS 2.0 task and domain router

Read this file immediately after the Skill activates. Select one task-mode row and,
when a concrete ThingJS capability is involved, one primary domain row. Maintenance,
evidence-promotion, and an otherwise unspecified member-verification task may set
`domain: null`; do not invent a runtime domain just to satisfy the trace schema.
Deduplicate required references and load nothing else until a conditional gate is met.

## Loading rules

- `Required` means read before acting on that mode or domain.
- `Conditional` means read only when the condition after the arrow is true.
- Start with one mode. Add one primary domain only when the request has a concrete
  ThingJS capability. A lifecycle qualifier such as scene replacement does not create
  a second domain label; load its child workflow conditionally only when the primary
  bundle cannot cover the separate cancellation or late-result boundary.
- Record `mode`, `domain`, `references_loaded`, and a one-line reason for each
  conditional load in the local evaluation trace.
- Stop when the smallest sufficient evidence set is reached. Unknown existence,
  owner, signature, version, lifecycle, or runtime compatibility blocks the call;
  it does not justify bulk-loading every reference or the engineer corpus.
- For `verify` requests that name no concrete capability beyond an unknown member,
  keep `domain: null` and use the mode's retrieval/policy references; the gotcha row
  is for a concrete review finding, not a generic substitute for missing evidence.

## Select one task mode

| Task mode | Required | Conditional |
| --- | --- | --- |
| Implement or refactor ThingJS code | `coding-standards.md` | `project-overlay.md` -> target-SDK support or a real project is under discussion; `knowledge-retrieval.md` -> any member is missing or unverified; `source-policy.md` -> a new official fact, source conflict, or provenance decision is needed; `context7-official-sources.md` -> Context7 is callable and provenance must be checked; `gotchas.md` -> a known conflict shape appears |
| Debug runtime or lifecycle behavior | `coding-standards.md`, `project-overlay.md` | `gotchas.md` -> compatibility, wrong owner, late completion, or teardown is suspected; `knowledge-retrieval.md` -> the expected API behavior is not already verified |
| Review ThingJS code | `coding-standards.md`, `gotchas.md` | `knowledge-retrieval.md` -> the diff contains an uncached or disputed member; `source-policy.md` -> a new official fact or source conflict is examined; `context7-official-sources.md` -> Context7 is callable and provenance must be checked; `project-overlay.md` -> the review claims target-SDK support |
| Verify a specific API or example before use | `knowledge-retrieval.md`, `source-policy.md` | `context7-official-sources.md` -> Context7 is callable and its runtime state must be evaluated; `project-overlay.md` -> deciding usability for a target SDK |
| Convert engineer material into reusable knowledge | `practice-workflows.md`, `evidence-model.md` | `knowledge-schema.md` -> writing a structured record; `source-policy.md` -> promoting an API fact candidate |
| Promote or change registry evidence | `evidence-model.md`, `knowledge-schema.md`, `source-policy.md` | `project-overlay.md` -> changing project support status |
| Build or validate a versioned Contract | `contract-pipeline.md`, `evidence-model.md`, `knowledge-schema.md`, `project-overlay.md` | `source-policy.md` -> controlled official evidence changes; `evaluation.md` -> release-gate behavior changes |
| Maintain or evaluate this Skill | `evaluation.md`, `hybrid-policy.md` | `domain: null` by default; `contract-pipeline.md` -> Contract, Runtime/Usage Surface, allowlist, or CI changes; other references -> only the changed route or assertion depends on them |

## Select the smallest domain bundle

| Domain | Required | Conditional local evidence |
| --- | --- | --- |
| App bootstrap or scene loading | `workflows/scene-loading.md` | App/scene Recipe -> implementation or runtime task; loading Incident -> signature, cancellation, or replacement conflict |
| Entity/object creation, readiness, or destroy | `workflows/entity-lifecycle.md` | Entity Recipe -> readiness or teardown task; destroy Incident -> stale reference or wrong owner |
| Event binding/unbinding | `workflows/event-ownership.md` | Event Recipe/Incident -> tag, condition, repeated listener, or owner cleanup matters |
| Camera or animation | `workflows/camera-animation.md` | Camera Recipe -> target readiness/order matters; timing conflict -> `duration/onComplete` versus `time/complete` appears |
| Scene replacement or loading cancellation | `workflows/scene-loading.md`, `gotchas.md` | Scene-replacement Recipe/Incident -> generation token, rollback, late result, or cleanup must be implemented |
| Query, campus, Earth, style, or rendering | `knowledge-retrieval.md` | `contract-pipeline.md` -> claiming support in a target Artifact Set; matching domain candidate -> only after exact owner, signature, version, and source checks |
| Hallucination, private member, compatibility, or wrong-owner review | `gotchas.md` | Incident record -> only for the exact matching failure pattern; select this row only when the task is a concrete review finding |

## Stop and escalation conditions

Stop reference loading and report the gap when:

- no exact official ThingJS 2.0 owner/signature supports a requested member;
- the target SDK is unknown or has an unresolved runtime conflict;
- the required local Recipe or Incident does not exist;
- a Context7 result lacks an original official URL, exact owner, public member,
  complete signature, or 2.0 scope;
- the task has left the ThingJS boundary and only host-framework work remains.

The supplied engineer corpus stays in the user workspace. Use its manifest or domain
index to locate a small candidate slice; never load all source documents or copy
private project material into the public Skill.

The child workflow paths above are the physical loading boundary. Do not create
one file per API or a second `domains/` tree: add a child workflow only when its
content has a separate route gate and can be loaded without reading an adjacent
capability. A domain label may remain a router label until it has an independent
public evidence bundle.
