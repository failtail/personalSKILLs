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
| Evaluation | Repeatable task, acceptance criteria, and outcome | No |

## Evidence labels

Apply one or more labels while preserving their different meanings:

- `official_verified`: an exact official ThingJS 2.0 page supports the claim.
- `official_unversioned`: an official 2.0 page supports the claim but does not identify a precise SDK build.
- `runtime_verified`: the claim passed a recorded probe against an identified SDK artifact.
- `runtime_conflict`: an identified SDK disagrees with the official claim or expected behavior.
- `project_verified`: a complete project behavior passed real runtime acceptance.
- `unit_verified`: a deterministic unit test passed, possibly with mocks.
- `internal_only`: the claim exists only in private/internal material.
- `historical_incident`: Git or project history proves an attempt and its outcome, not official validity.
- `unverified`: evidence is missing or insufficient.

Do not collapse `unit_verified` into `runtime_verified`. A mock can prove orchestration and cleanup calls, but it cannot prove that ThingJS exposes the mocked API.

## API usage eligibility

| Evidence | Current-project use |
| --- | --- |
| Official ThingJS 2.0 evidence, no known runtime conflict | Allowed, subject to lifecycle completeness |
| Official evidence plus `runtime_verified` | Preferred |
| Official evidence plus `runtime_conflict` | Blocked for that project |
| `internal_only` | Blocked until reconciled with official evidence |
| Repository code or Git commit only | Blocked as API evidence |
| Unknown-version example | Rejected |

An API record may remain official and still be blocked in one project. Represent that with a project runtime verification record; do not rewrite the canonical official signature.

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
