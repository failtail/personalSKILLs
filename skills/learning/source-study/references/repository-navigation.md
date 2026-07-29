# Repository Navigation

## Goal To Evidence Map

Translate the user's learning question before searching:

| Learning target | Good initial anchors |
| --- | --- |
| Public API | Export name, package/module manifest, documentation name, import path |
| Runtime behavior | Observable method, event, configuration key, log/error text |
| Internal abstraction | Interface, base type, class/function name, protocol term |
| Framework mechanism | Lifecycle hook, compiler transform, scheduler name, reactive primitive, render entry |
| Failure behavior | Error class/message, error handler, retry/cancellation option |

## Efficient Discovery Order

1. Read top-level manifests and workspace configuration to identify packages and source roots. Examples include `package.json`, workspace manifests, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, build scripts, and export maps.
2. Locate public entry points and exports before searching deep implementation. In a library, start from the import path or exported symbol; in an application, start from the requested route, command, request handler, or event entry.
3. Search exact names with `rg` when available. If unavailable, use the platform's recursive file search and text search. Search definitions, imports, calls, tests, and error strings separately when the result set is large.
4. Follow a narrow path: public entry -> contract/type -> implementation -> caller/callee -> state or I/O boundary -> focused test.
5. Read neighboring files only when they explain a dispatch, generic type, helper, state channel, generated code boundary, or condition that changes behavior.

## Exclusions

Do not begin with `node_modules`, vendor/dependency trees, build output, generated declarations, coverage, caches, lockfiles, or minified bundles. Use them only when they are explicitly the subject or the source is unavailable.

## Framework-Neutral Trace Questions

- Where does an external caller enter the system?
- Which module owns the contract or public abstraction?
- Which concrete implementation executes it?
- What configuration, state, dependency injection, or context crosses the boundary?
- Where does control branch for success, error, retry, cancellation, async work, or lifecycle changes?
- Which test most directly proves the claimed behavior?

## Vue Repository Example

For a local Vue repository, do not search the whole repository for generic words such as `state` or `render` first. Start from the specific API or subsystem, such as `ref`, `ReactiveEffect`, `track`, `trigger`, `queueJob`, `defineComponent`, `compile`, or `createApp`. Then trace across the relevant package boundaries, commonly reactivity, runtime-core, runtime-dom, compiler-core, shared, and tests. Treat the actual checked-out source as authoritative; framework knowledge only guides where to look.
