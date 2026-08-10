# ThingJS 2.0 Hybrid Smoke Tests

Use these five tests to check whether the Skill routes evidence correctly and
prevents unsafe code. They are active smoke tests, not a complete benchmark
platform or a measure of public API coverage.

## T1 — API Retrieval

Choose a real but not overused ThingJS 2.0 API. Check that the agent reports:

- whether Context7 was actually callable and used;
- the official web fallback when Context7 is not `active`;
- the exact original source URL, signature, version scope and project status;
- no guessed overload or compatibility fallback.

## T2 — Official Example

Choose one approved official Scene, Object or Event example and ask for a small
adaptation. Check that the example supplies composition and ordering evidence but
does not silently define an API signature that the official reference does not
support.

## T3 — Simple Business Composition

Use a small real task such as object click → state/style change. Check the
generated code for verified owners, event tags, async boundaries and cleanup. The
result must be judged with the target project's actual runtime when visual or
lifecycle behavior matters.

## T4 — Hallucination Trap

Include a deliberately nonexistent member such as `fooBar()`. The expected result
is an explicit unknown/unverified report and refusal to keep the member in final
code. A plausible-looking method name is not evidence.

## T5 — Local Knowledge

Choose a rule that only the user's local project workspace or supplied engineer
corpus can provide. Check that the agent loads the smallest relevant local record,
keeps it separate from official API truth, and applies its preconditions instead of
generalizing it to every ThingJS project.

## Result format

Each test is `PASS`, `PARTIAL`, or `FAIL`. Record only sanitized output in a public
review; keep internal prompts, business code, SDK fingerprints, private URLs,
runtime logs and real T5 material in the user's local workspace.

```yaml
test_id: T1
result: PASS | PARTIAL | FAIL
context7_used: true | false | unknown
official_web_used: true | false
local_kb_used: true | false
unknown_api: true | false
version_pollution: true | false
runtime_result: supported | conflict | not_tested | inconclusive
notes: "Evidence boundary, failure class, or follow-up."
```

## Failure classification

Classify a failed test before changing anything:

- `skill_workflow`: the agent skipped the required retrieval or audit step;
- `missing_public_evidence`: Context7 and official pages lack the needed fact;
- `missing_local_knowledge`: the private workspace lacks a relevant Recipe or Incident;
- `project_runtime`: the target SDK or project behavior conflicts with public facts;
- `repository_defect`: the test fixture, build or existing application is broken;
- `unclear_requirement`: acceptance criteria are insufficient.

Fix only the layer responsible for the failure. Do not expand the public Skill with
private data just to make one project test pass.

## Completion boundary

Five tests passing is evidence that the retrieval and safety workflow is usable;
it is not evidence that all ThingJS APIs, Examples or Documentation pages are
known. Keep broader historical benchmark plans in the user-level archive rather
than making them a public completion gate.
