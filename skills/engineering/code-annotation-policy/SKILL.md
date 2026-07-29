---
name: code-annotation-policy
description: Enforce proportionate, maintainable code comments and implementation documentation for coding work. Use whenever Codex implements a feature, fixes a bug, refactors code, or changes constants, functions, classes, types, modules, or public APIs. Classify the change as S, M, or L; choose comments and documentation by behavioral risk, project scale, and release urgency without adding redundant narration.
---

# Code Annotation Policy

Apply this policy after understanding the requested change and before declaring coding work complete. Honor repository-specific documentation and comment rules when they are stricter. Read [commenting-examples.md](references/commenting-examples.md) when choosing a tier, writing non-obvious comments, handling an urgent fix, or deciding whether a separate document is justified.

## 1. Classify the Change

Classify each implementation by its behavioral scope, not its line count. Choose the higher tier when uncertain.

| Tier | Scope | Required output |
| --- | --- | --- |
| `S` | Local bug fix, small configuration change, or self-contained behavior with one clear intent | Add only necessary concise comments. Do not create a separate implementation document. |
| `M` | A coherent capability spanning several functions or files, or non-trivial state, validation, data transformation, retries, caching, concurrency, or external I/O | Add implementation comments to the important functions, decisions, state, and boundaries. Include a brief implementation summary in the final handoff or an existing change-note location. |
| `L` | A new feature module, public contract, cross-module workflow, substantial refactor, or behavior involving persistence, authorization, protocols, observability, or complex lifecycle cleanup | Add detailed module and implementation comments. Create or update the repository's preferred implementation document. When none exists, use a concise `IMPLEMENTATION.md` next to the feature module. |

Classify a focused fix as `S` even if the surrounding file is large. Classify a small diff as `M` or `L` when it changes a shared lifecycle, asynchronous behavior, ownership rule, data contract, or safety boundary. Record the reason for an `L` classification in its implementation document.

## 2. Apply Comment Requirements

Review every constant and function added or materially changed. Add a concise comment whenever the identifier alone does not state its purpose, units, source, constraints, side effects, or implementation strategy.

Always document:

- Exported or otherwise public constants, functions, classes, types, and public APIs.
- Module-level domain constants, particularly thresholds, time values, limits, protocol values, feature flags, and values with non-obvious units or sources.
- Functions with side effects, complex control flow, non-obvious transformations, security implications, retries, caching, concurrency, lifecycle behavior, or important invariants.
- Workarounds, intentional deviations, and behavior whose reason is not obvious from the code.

For spatial, animation, or time-based code, state the coordinate space, unit, direction, reference point, or timing relationship whenever a future maintainer could otherwise tune the wrong value. For lifecycle code, state what is created, who owns it, and when it must be cleaned up.

Do not document a local value or short private helper when its name and immediate context fully explain it. Do not write comments that merely restate the next line of code. Prefer the reason, constraint, and observable behavior over a narration of syntax.

Use the repository's preferred documentation format. For TypeScript public APIs, use concise TSDoc where it is appropriate. Keep comments current whenever the implementation changes.

## 3. Adapt To Project Size And Urgency

Match the process to the project rather than applying documentation mechanically:

- **Small script or prototype**: Keep comments adjacent to non-obvious decisions. Prefer an existing README or handoff note over creating a new document.
- **Application or team repository**: Describe module boundaries, state ownership, cleanup, and external contracts in the changed code. Put `L` documentation in the repository's established design or implementation area.
- **Library, platform, or multi-team system**: Document public compatibility expectations, error behavior, migration impact, and observability. Request clarification before silently changing a public contract.

For an urgent production fix, first make the smallest correct change and add the minimum comment needed to prevent reversal of the safety decision. Do not block the fix on a long design document. Before handoff, record the risk, validation performed, known follow-up, and the owner/location for deferred `L` documentation. Do not use urgency as a reason to omit comments for security, data-loss, authorization, cleanup, or compatibility boundaries.

## 4. Write Module Documentation for `L`

Use the repository's established documentation location and format. If none exists, add or update `IMPLEMENTATION.md` beside the feature module with these sections:

```md
# <Feature> Implementation

## Requirement Mapping
- <Requirement>: <how the implementation satisfies it>

## Design and Flow
- Entry points:
- Data and control flow:
- Failure and boundary handling:

## Key Decisions
- <decision>: <reason and trade-off>

## Validation
- <tests or other verification>
- Known limitations:
```

Make the document describe the actual implementation and its trade-offs. Do not create a document for a `S` or `M` change merely to satisfy a template.

## 5. Complete the Change

Before handoff, verify that comments match the final code and that `L` documentation is present and accurate. Check that a changed constant still has the right unit, a changed cleanup path still matches ownership, and a changed workaround comment still describes the actual behavior. State the selected tier and summarize the annotations or implementation document added. Mention explicitly when an `S` change needs no additional comments because the code is self-explanatory.
