---
name: code-annotation-policy
description: Enforce proportionate code comments and implementation documentation for coding work. Use whenever Codex implements a feature, fixes a bug, refactors code, adds or changes constants, functions, classes, types, modules, or public APIs. Classify the change as small, standard, or module-scale; add comments and, for module-scale work, implementation documentation without adding redundant comments.
---

# Code Annotation Policy

Apply this policy after understanding the requested change and before declaring coding work complete. Honor repository-specific documentation and comment rules when they are stricter.

## 1. Classify the Change

Classify each implementation by its behavioral scope, not its line count. Choose the higher tier when uncertain.

| Tier | Scope | Required output |
| --- | --- | --- |
| `S` | Local bug fix, small configuration change, or self-contained behavior with one clear intent | Add only necessary concise comments. Do not create a separate implementation document. |
| `M` | A coherent capability spanning several functions or files, or non-trivial state, validation, data transformation, retries, caching, concurrency, or external I/O | Add implementation comments to the important functions, decisions, state, and boundaries. Include a brief implementation summary in the final handoff or an existing change-note location. |
| `L` | A new feature module, public contract, cross-module workflow, substantial refactor, or behavior involving persistence, authorization, protocols, or observability | Add detailed module and implementation comments. Create or update the repository's preferred implementation document. When none exists, use a concise `IMPLEMENTATION.md` next to the feature module. |

## 2. Apply Comment Requirements

Review every constant and function added or materially changed. Add a concise comment whenever the identifier alone does not state its purpose, units, source, constraints, side effects, or implementation strategy.

Always document:

- Exported or otherwise public constants, functions, classes, types, and public APIs.
- Module-level domain constants, particularly thresholds, time values, limits, protocol values, feature flags, and values with non-obvious units or sources.
- Functions with side effects, complex control flow, non-obvious transformations, security implications, retries, caching, concurrency, lifecycle behavior, or important invariants.
- Workarounds, intentional deviations, and behavior whose reason is not obvious from the code.

Do not document a local value or short private helper when its name and immediate context fully explain it. Do not write comments that merely restate the next line of code. Prefer the reason, constraint, and observable behavior over a narration of syntax.

Use the repository's preferred documentation format. For TypeScript public APIs, use concise TSDoc where it is appropriate. Keep comments current whenever the implementation changes.

## 3. Write Module Documentation for `L`

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

## 4. Complete the Change

Before handoff, verify that comments match the final code and that `L` documentation is present and accurate. State the selected tier and summarize the annotations or implementation document added. Mention explicitly when a `S` change needs no additional comments because the code is self-explanatory.
