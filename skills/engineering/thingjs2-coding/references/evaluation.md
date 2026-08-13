# ThingJS 2.0 Skill evaluation

Evaluate five layers separately: activation, progressive routing, output behavior,
Contract pipeline, and real engine behavior. A pass in one layer never implies a
pass in another.

## A. Activation tests: metadata only

Activation depends on `name` and `description`, because the Skill body is not loaded
until after selection. Before changing the description, run the prompt set against
the old metadata and preserve the baseline. After the change, rerun the same prompts
with only the new metadata visible. Do not reveal expected results to the evaluating
agent.

| ID | Prompt shape | Expected `thingjs2-coding` activation |
| --- | --- | --- |
| A01 | Create `THING.App`, load a scene, and clean old listeners | Yes |
| A02 | Review `new THING.Entity(...)` readiness and `destroy()` | Yes |
| A03 | Decide camera timing/completion field names for ThingJS 2.0 | Yes |
| A04 | Debug Vue computed state with no `THING` use | No |
| A05 | Refactor a generic JavaScript utility | No |
| A06 | Preserve ThingJS 1.x compatibility or migration syntax | No |
| A07 | Put a suspicious `THING.fooBar()` into production code | Yes: verify then reject if unsupported |
| A08 | A repository contains `THING`, but the requested edit is CSS-only | No |
| A09 | Verify a specific `THING.App.load` 2.0 signature before use | Yes |
| A10 | Catalog every API website page without a code/use decision | No |
| A11 | Create `THING.Entity` inside Vue and clean it on unmount | Yes, alongside the Vue Skill |
| A12 | Integrate a t3d controller into ThingJS | No |
| A13 | Maintain or evaluate this Skill's activation, routing, or evidence workflow | Yes |

Record false positives and false negatives separately. For a cross-domain prompt
such as A11, success means both applicable Skills can activate without this Skill
prescribing Vue architecture.

## B. Progressive-routing tests

Give the agent the activated Skill and a realistic task, but do not tell it which
references should be read. Require a load trace containing `mode`, `domain`,
`references_loaded`, and conditional reasons.

| ID | Task | Expected route property |
| --- | --- | --- |
| R01 | Verify one exact API signature | API-verification mode; no coding or corpus bundle unless use is requested |
| R02 | Implement Entity readiness and teardown in a real project | Implementation mode plus Entity domain and project Overlay |
| R03 | Review repeated object events | Review mode plus event domain; load an Incident only for a matching failure |
| R04 | Resolve camera `duration/time` conflict | Camera domain plus Gotcha; add source retrieval only if the exact form is unresolved |
| R05 | Convert one engineer example to a Recipe candidate | Corpus-conversion mode; do not load unrelated API domains or promote an API fact |
| R06 | Maintain this Skill's description | Maintenance mode; evaluation/hybrid policy only, plus the route being changed |

Fail routing when the agent bulk-loads the public references, entire engineer corpus,
or API cache; loads a conditional file without stating its gate; follows nested
references outside the selected route; or continues searching after a defined stop
condition should block the API.

## C. Output-behavior smoke tests

These tests measure evidence discipline and safe code behavior after correct
activation/routing. They do not measure website coverage.

### T1 - API retrieval

Choose a real but not overused ThingJS 2.0 API. Require the actual retrieval channel,
exact official URL, owner, signature, version scope, project status, and no guessed
overload. Do not claim Context7 was used when it was not callable.

### T2 - Official example

Adapt one approved official Scene, Object, or Event example. The example may support
composition and ordering, but it must not silently redefine a signature absent from
the matching official reference.

### T3 - Simple business composition

Use a small task such as object click to state/style change. Check verified owners,
listener ownership, async boundaries, and cleanup. Require target runtime evidence
when visual or lifecycle behavior matters.

### T4 - Hallucination trap

Include a nonexistent member and a plausible wrong-owner result. The agent must mark
them unknown/wrong-owner and remove them from final code; source reputation or a
similar member name is not proof.

### T5 - Local knowledge

Use a rule available only in the user-level project workspace or engineer corpus.
The agent must load the smallest matching record, separate it from official API truth,
and apply its preconditions without generalizing it to every project.

## D. Runtime proof

Split runtime proof into two independent artifacts:

- Runtime Surface records descriptor-based member existence for an exact SDK
  Artifact Set. It must fail capture if an artifact fails to load and must not invoke
  constructors, getters, or methods while discovering members.
- Runtime Behavior Test records one exact scenario, preconditions, browser result,
  cleanup observation, and unresolved visual behavior for the same Artifact Set.

A build, mock, Git commit, public example, Runtime Surface, or agent report cannot
substitute for target-project behavior evidence.

## E. Contract pipeline tests

Run the synthetic pipeline tests and at least one real-project dry run when changing
the Contract schema, Usage Surface extractor, validator, allowlist, or CI wrapper.

Required synthetic cases:

| ID | Case | Expected result |
| --- | --- | --- |
| C01 | Direct, alias, destructured, and static computed ThingJS access in JS/TS | Resolved Usage Entities with provenance |
| C02 | Vue `<script>` and `<script setup>` access | Same Usage Entity schema as JS/TS |
| C03 | Production-reachable dynamic property access | Blocked without exact allowlist |
| C04 | Exact Usage-ID/expression allowlist bound to the Artifact Set | Only the matching Usage Entity passes |
| C05 | Inherited prototype member | Resolves through captured inheritance edges |
| C06 | Unversioned latest official change | `stale_review`, not automatic block |
| C07 | Current artifact differs from Contract binding | Block |
| C08 | Regex fallback finds a token | Discovery only; no verified Usage Entity |
| C09 | Production entry reaches an unresolved local/dynamic import | Block as incomplete reachability |
| C10 | Broad or expression-mismatched dynamic allowlist | Ignore exception and keep the Usage Entity blocked |

A real-project non-zero result is a valid pipeline outcome when the report identifies
genuine missing Contract coverage or unresolved production usage. Report it as an
expected block with counts and evidence paths, not as a tool failure or a successful
release.

## Result record

Use `PASS`, `PARTIAL`, `FAIL`, or `NOT_RUN` for each layer. Keep internal prompts,
business code, SDK fingerprints, private URLs, and raw runtime logs in the user's
workspace; commit only sanitized summaries.

```yaml
case_id: A01 | R01 | T1 | C01 | runtime-id
layer: activation | routing | output | contract | runtime_surface | runtime_behavior
result: PASS | PARTIAL | FAIL | NOT_RUN
coverage_result: PASS | PARTIAL | FAIL | NOT_RUN
quality_result: PASS | PARTIAL | FAIL | NOT_RUN
expected_activation: true | false | null
actual_activation: true | false | unknown
mode: implement | debug | review | verify | convert | promote | maintain | null
domain: app | entity | event | camera | scene-replacement | query-rendering | gotcha | null
references_loaded: []
conditional_reasons: []
context7_used: true | false | unknown
official_web_used: true | false
local_kb_used: true | false
unknown_api: true | false
version_pollution: true | false
runtime_result: existence_verified | behavior_verified | conflict | not_tested | inconclusive
notes: "Evidence, failure class, or follow-up."
```

## Failure classification

- `activation_false_positive` or `activation_false_negative`
- `routing_overload`, `routing_gap`, or `routing_stop_failure`
- `skill_workflow`
- `contract_schema`, `artifact_drift`, `usage_resolution`, or `allowlist_scope`
- `missing_public_evidence`
- `missing_local_knowledge`
- `project_runtime`
- `repository_defect`
- `unclear_requirement`

Fix only the responsible layer, rerun the same case, and preserve the before/after
record. Never broaden the public Skill or leak private data merely to make a test pass.

## Completion gate

Before claiming the Skill change is validated:

1. run structural validation and link/privacy checks;
2. rerun A01-A13 against the revised metadata;
3. run the routing cases affected by the change and inspect their load traces;
4. run the relevant T1-T5 behavior tests;
5. run the synthetic Contract pipeline and record any real-project expected block;
6. state Runtime Surface and Runtime Behavior cases separately as passed, partial,
   conflicting, or not run;
7. run the user-level replay checker, when present, against the exact fixtures and
   result record; its complete mode must fail while any required case is `NOT_RUN`;
8. inspect the complete diff, public/private boundary, generated reports, and
   installed-copy equality before release.

Fresh commands and artifacts must support every completion claim. Five behavior tests
passing does not prove activation quality, progressive loading, complete API coverage,
or target-project runtime compatibility.
