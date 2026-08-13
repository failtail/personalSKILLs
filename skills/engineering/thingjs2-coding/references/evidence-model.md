# Evidence model

Use independent evidence dimensions instead of one ambiguous confidence score.

## Entity classes

| Class | Meaning | May define API truth? |
| --- | --- | --- |
| API fact | Existence, owner, kind, signature, parameters, returns, constraints | Yes, with official evidence |
| Concept | Object model, lifecycle, coordinates, loading, or rendering behavior | Yes, with official evidence |
| Example | Official minimal composition | No; references API facts |
| Recipe | A verified solution for a project scenario | No; references API facts |
| Incident | Failed, reverted, paused, or misleading implementation | No |
| Project profile | SDK fingerprint and project constraints | Only for project compatibility |
| Runtime Surface | Browser descriptor observation for one exact SDK Artifact Set | Existence only |
| Runtime Behavior Test | Executed lifecycle, ordering, rendering, readiness, cleanup, or failure scenario | Project behavior only |
| Versioned Contract | Normalized API records bound to one SDK Artifact Set | Machine entry derived from controlled facts |
| Project ThingJS Usage Surface | AST-derived source usage and resolution provenance | No; defines what project code must validate |
| Evaluation | Repeatable task, acceptance criteria, and outcome | No |

## Evidence labels

Apply one or more labels while preserving their different meanings:

- `official_verified`: an exact official ThingJS 2.0 page supports the claim.
- `official_unversioned`: an official 2.0 page supports the claim but does not identify a precise SDK build.
- `existence_verified`: the member was observed through descriptor inspection against
  an identified SDK Artifact Set; no behavior is implied.
- `behavior_verified`: an independent behavior scenario passed against that exact
  Artifact Set and recorded its preconditions and cleanup.
- `runtime_conflict`: an identified Artifact Set disagrees with controlled target-version
  evidence or fails a required behavior test.
- `project_verified`: a complete project behavior passed real runtime acceptance.
- `unit_verified`: a deterministic unit test passed, possibly with mocks.
- `internal_only`: the claim exists only in private/internal material.
- `historical_incident`: Git or project history proves an attempt and its outcome, not official validity.
- `unverified`: evidence is missing or insufficient.

Do not collapse `unit_verified`, `existence_verified`, and `behavior_verified`. A
mock can prove orchestration; descriptor inspection can prove a member exists; only
the behavior test can prove lifecycle or rendering behavior.

## API usage eligibility

| Evidence | Current-project use |
| --- | --- |
| Official ThingJS 2.0 evidence, no known runtime conflict | Allowed, subject to lifecycle completeness |
| Official evidence plus `existence_verified` | Preferred for member existence |
| Official evidence plus matching `behavior_verified` | Required for behavior-dependent release claims |
| Official evidence plus `runtime_conflict` | Blocked for that project |
| `internal_only` | Blocked until reconciled with official evidence |
| Repository code or Git commit only | Blocked as API evidence |
| Unknown-version example | Rejected |

An API record may remain official and still be blocked in one project. Represent that
in the Artifact-Set-bound Contract or behavior record; do not rewrite the controlled
official signature. A change observed only on an unversioned latest official page is
`stale_review`; it does not invalidate a Contract for an older target SDK by itself.

## Recipe promotion

Mark a Recipe `project_verified` only when:

1. every referenced API is eligible;
2. the exact project and SDK fingerprint are recorded;
3. the behavior passed an appropriate real runtime test;
4. cleanup and cancellation paths were exercised or explicitly bounded;
5. source code and verification evidence remain traceable.

A build, lint check, or unit test alone is insufficient for visual, rendering, camera, picking, animation, or lifecycle behavior.

## Git evidence

- Use an introducing commit and its later fix, revert, or removal together.
- Treat a commit message as a locator, not as proof.
- Inspect the actual diff and current code.
- Record failed and reverted work as an Incident even when parts of the implementation remain useful.
- Revalidate old conclusions when tests, source lines, or SDK artifacts change.
