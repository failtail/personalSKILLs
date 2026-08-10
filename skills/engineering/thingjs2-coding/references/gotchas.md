# ThingJS 2.0 known gotchas

These are rejection and conflict patterns, not API recommendations.

| Pattern | Required handling |
| --- | --- |
| `app.dispose()` versus `app.destroy()` | Keep an App teardown conflict until exact official and project-runtime evidence resolves it. |
| `onComplete`, `complete`, and `waitForComplete()` | Verify by exact owner, module, and version; do not transfer a callback shape across modules. |
| `duration/onComplete` versus `time/complete` | Treat as an overload/module conflict; do not infer from field names. |
| Native constructors versus `app.create` | Keep compatibility-style paths blocked unless the target project's explicit evidence permits them. |
| `_...`, `thing_src_*`, or monkey-patched members | Treat as private/internal and exclude from generated public code. |
| Context7 result with a wrong owner or private page | Record a retrieval Incident and use the official-page fallback. |
| Local example claims “complete runnable” | Keep it as Example/Recipe candidate until source, SDK, acceptance, and cleanup evidence exist. |
| Legacy or unversioned example | Mark version pollution; never silently upgrade it to ThingJS 2.0. |

Every Incident should record the source path/query, conflicting member, suspected
owner, version clues, retrieval channel, official result, runtime result, blocked
scope, and the evidence needed to reopen it.

