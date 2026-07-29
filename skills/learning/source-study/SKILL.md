---
name: source-study
description: Create and deeply explain Chinese learning Markdown from any local source-code repository, source files, a module/topic, or user-provided notes. Use when studying how a codebase works, locating implementations from a concept or public API, tracing exports, types, call paths, state, errors, tests, and architecture boundaries in Vue, React, TypeScript, JavaScript, Python, Go, Java, Rust, libraries, applications, monorepos, and frameworks. Support write, explain, and combined write plus explain requests; preserve English technical terms and explain their meaning, role, implementation, and architecture boundary.
---

# Source Study

Turn a local repository into accurate learning material. Do not clone, download, install, modify, build, or test the target project unless the user separately requests that action. Do not implement product features or turn this into a user-interview/grilling workflow.

## Choose The Workflow

Use the request and supplied artifacts to choose one workflow. A request can explicitly require both; then run them in order without requiring the user to submit the output again.

| Workflow | Trigger | Work |
| --- | --- | --- |
| `write` | A repository, topic, module, class, function, public API, or source path | Locate the relevant code, inspect the execution path, then write a standalone learning Markdown chapter. |
| `explain` | Existing Markdown, notes, diagrams, or a focused follow-up question | Read the supplied material, locate and verify relevant source, correct inaccuracies, then teach the requested area in greater depth. |
| `write + explain` | The user says "first write then explain", provides a target and notes, or requests a complete chapter plus a deep dive | First write or complete the chapter, then continue with a source-grounded explanation of the requested or most important implementation paths. |

Do not treat `write` and `explain` as mutually exclusive when the user asks for both.

## Repository Navigation First

Assume the user has already made the desired source repository available locally. Before explaining behavior, locate the right evidence efficiently rather than reading the repository indiscriminately.

1. Determine the repository root, language(s), build/workspace manifests, package/module boundaries, and likely source/test directories.
2. Convert the learning target into search anchors: public API name, type/class/function name, configuration key, error text, protocol term, file name, or observable behavior.
3. Search exact identifiers first. Then trace from public entry or export to contract/type, concrete implementation, direct callers, state/error paths, and focused tests.
4. Prefer source, type definitions, export manifests, and tests. Exclude generated output, dependency/vendor trees, coverage, caches, and lockfiles unless they answer the question.
5. Stop widening the search once the relevant behavior is established. State what remains uncertain rather than reading unrelated modules.

Read [repository-navigation.md](references/repository-navigation.md) before locating a new subject. Read [chapter-template.md](references/chapter-template.md) for the expected learning-document structure. Read [evidence-and-diagrams.md](references/evidence-and-diagrams.md) before writing diagrams or source corrections.

## Source-Grounded Explanation

Treat the local source as the primary authority for implementation claims. Do not invent symbols, return types, file locations, line numbers, or current API behavior. Separate these categories explicitly when relevant:

- **Source fact**: directly established by current local code, types, exports, or tests.
- **Note claim**: a statement from the user's Markdown.
- **Version-sensitive inference**: a reasonable conclusion that can differ by release, configuration, platform, or implementation.

Explain from outside in: architecture boundary, public contract, runtime flow, then the critical methods and state/error paths. Keep the response in Chinese by default. Keep English API/type/file names unchanged; at first use, give a concise Chinese meaning and explain its role in context.

When a repository clearly belongs to a framework or domain with an installed specialist Skill, use that Skill for domain-specific interpretation. Keep this Skill responsible for navigation, evidence, documentation, and deep explanation. For example, use Vue-specific conventions when studying `.vue` files, reactivity, SFC compilation, runtime, router, Pinia, or Volar, while still tracing the actual checked-out Vue source.

## Explain Code, Not Just Names

For every important class, method, hook, module, component, or protocol under discussion, answer the parts that apply:

- Who imports or calls it, and at what point in the broader runtime flow?
- What input, configuration, state, callback/runtime context, or dependency does it receive?
- What does it return, render, emit, yield, or mutate?
- Which abstraction boundary does it protect, adapt, or expose?
- What changes on success, error, cancellation, retry, streaming, reactivity, or lifecycle paths?

Avoid a bare API inventory. Connect public calls to internal implementations and their callers where source supports it.

## Diagrams And Output

Use Mermaid only when it materially clarifies execution, ownership, data/state flow, or branching. Use a flowchart for boundaries and data flow; use a sequence diagram for cross-module chronology; use a state diagram only for meaningful transitions. Provide clickable local links for real source files and add line numbers only after verifying them.

When both workflows are requested, use this order:

1. Deliver the complete or revised Markdown chapter.
2. Add `## Deep Explanation` after the chapter, or clearly label a second Markdown section.
3. Trace the critical execution path, identify corrections to user notes, and explain design tradeoffs and common misconceptions.
4. Finish with a concise `## Mental Model` that relates the central abstractions coherently.

Do not ask the user to copy the generated chapter back into the chat before performing the deep explanation.

## Interaction Examples

```text
Use $source-study: in the local Vue repository, locate how ref(), reactive(), and effect() connect; write a learning chapter, then deeply explain dependency tracking and trigger scheduling.
```

```text
Use $source-study: verify my notes about this TypeScript monorepo's plugin loading system against the local source; revise the chapter, then trace one plugin from public registration to execution and error handling.
```

```text
Use $source-study: from this local Python repository, find the request middleware path and explain which component creates context, which one calls the handler, and how exceptions become HTTP responses.
```

