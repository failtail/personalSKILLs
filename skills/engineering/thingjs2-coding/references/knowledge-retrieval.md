# Knowledge retrieval for ThingJS 2.0

Use this reference when the task needs API evidence, source selection, or a
decision about whether a local engineer example can be reused.

## Evidence order

1. Identify the ThingJS domain and the target project's complete SDK Artifact Set.
2. Read the smallest matching versioned Contract record and project Overlay.
3. Query only the allowlisted official Context7 libraries when a fact is missing.
4. Check the result's exact public owner, member, signature, original official URL,
   and ThingJS 2.0 scope. Context7 is a retrieval channel, not automatic proof.
5. Fall back to the approved official web/API pages when Context7 is partial,
   unavailable, truncated, ambiguous, conflicting, or source-less.
6. Read engineer Examples, Recipes, FAQs, and Incidents only for composition,
   project constraints, and failure patterns. They cannot silently redefine an
   official API fact.

## Stop conditions

- If existence, owner, signature, version, or lifecycle behavior is unknown,
  report `unknown/unverified` and do not generate that call.
- If controlled target-version evidence conflicts with the Contract, preserve both
  records and block the API for that project. If only an unversioned latest page
  changed, mark `stale_review`. Do not invent a compatibility fallback.
- If an example demonstrates ordering but not a signature, use its ordering only.
- If an internal/private-looking page or wrong-owner result appears, record an
  Incident and return to a public official source.

## Output contract

For every ThingJS member in a final diff, report the evidence label, retrieval
channel, original source URL, version scope, project status, and unresolved risk.
Separate official API facts from Examples, Recipes, Overlays, and Incidents.

