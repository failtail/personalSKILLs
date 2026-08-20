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
| A14 | Check project ThingJS 2.0.13 Contract/SDK drift | Yes |
| A15 | Decide whether `THING[config.type]` is safe to publish | Yes |
| A16 | Integrate Earth Map/TileLayer and verify the Earth SDK | Yes |
| A17 | Convert an engineer-maintained Earth example into knowledge candidates | Yes: convert mode |
| A18 | Implement a Vue page filter without changing `THING` | No |
| A19 | Catalog the complete official API website for search without a code decision | No |
| A20 | Fix a late callback contaminating state after scene replacement | Yes |
| A21 | Generate `.d.ts` from a verified Contract | Yes |
| A22 | Continue supporting `app.create` in a ThingJS 1.x project | No |

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

R05 has an additional output boundary: the result may be only a compact
conversion-ledger entry or a selectively materialized candidate derivative. It
must resolve an indexed source to exactly one row by normalized path plus SHA,
read only that row, and preserve its domain, primary/evidence class, risk flags,
semantic/direct decision, reason codes, next gate, and materialization policy.
Raw content or file names must not replace those governance fields. Unindexed
material may create only a candidate row with an explicit manifest/index gate. A
true Recipe/Incident promotion also needs preconditions, Contract IDs, and evidence
references; `ledger_only` remains acceptable when evidence or priority is insufficient.
R05 must not edit the triggering `description`, change the routed `mode` or
`domain`, or change any API/Contract state, including by treating the engineer
example as an API fact.

Fail routing when the agent bulk-loads the public references, entire engineer corpus,
or API cache; loads a conditional file without stating its gate; follows nested
references outside the selected route; or continues searching after a defined stop
condition should block the API.

The physical child-workflow assertions are intentionally small:

| Route | Required child bundle |
| --- | --- |
| R02 Entity readiness/teardown | `workflows/entity-lifecycle.md` |
| R03 repeated object events | `workflows/event-ownership.md` |
| R04 camera timing conflict | `workflows/camera-animation.md` |
| Scene loading/replacement variant | `workflows/scene-loading.md` |

`coding-standards.md`, `practice-workflows.md`, Contract, evidence, and project
Overlay remain cross-cutting references selected by the mode and conditional gates;
they are not duplicated into each child workflow.

Mixed requests retain one primary domain in the trace. An unknown-member `verify`
request remains `domain: null`; a scene-replacement qualifier on a camera task may
load `workflows/scene-loading.md` conditionally without becoming a second domain.

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

### Runtime prerequisites and authentication boundary

Record service availability and authentication as separate preconditions for a
target-project Behavior Test. A connection refusal, a redirect to a login page,
or a human-verification page is `NOT_RUN`/`PARTIAL` runtime evidence, never a
passed behavior result. A read-only probe may record the URL, page title, HTTP or
connection result, `typeof window.THING`, and canvas count, but must not read or
export cookies, tokens, passwords, or storage values. Do not submit credentials,
bypass CAPTCHA, or infer runtime behavior from an unauthenticated shell. Resume
the runner only after the user provides a legitimate test session or approved
test-login mechanism and the target service is reachable.

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
   it must also fail for partial output quality or target-project runtime behavior.
   Bind output quality to the hash of an independent evaluator's raw artifact;
   a self-reported forward artifact cannot satisfy the quality gate by itself.
8. require the result record to contain the exact digest, file count, and algorithm
   for the installed Skill tree's non-cache files. Enumerate recursively from the
   `SkillPath` parent, normalize relative paths to `/`, sort by `Ordinal`, and
   exclude cache/temporary boundaries such as `__pycache__`, `.pyc`, `.git`,
   `node_modules`, build outputs, and temporary/log files. For each remaining file,
   append `relative_path + LF + uppercase content SHA-256 + LF` to a UTF-8
   no-BOM manifest, then SHA-256 the manifest. The exact algorithm identifier is
   `thingjs-skill-tree-v1;sort=Ordinal;entry=relative-path+LF+uppercase-content-sha256+LF;manifest=UTF-8-no-BOM;digest=SHA-256;scope=non-cache-files`.
   This tree digest proves only evaluation-input integrity; it never substitutes
   for activation, output quality, Runtime Surface, or Runtime Behavior evidence.
9. inspect the complete diff, public/private boundary, generated reports, and
   installed-copy equality before release.

Fresh commands and artifacts must support every completion claim. Five behavior tests
passing does not prove activation quality, progressive loading, complete API coverage,
or target-project runtime compatibility.
