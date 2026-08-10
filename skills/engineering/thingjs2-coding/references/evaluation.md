# Evaluation workflow

Measure whether the Skill improves real ThingJS 2.0 work, not only whether it produces more documentation.

## First-release strategy

1. Discover the complete approved source inventory.
2. Select 10–15 real tasks from current project history.
3. Extract only the API domains required by those tasks.
4. Build the matching canonical records, Examples, Recipes, and Incidents.
5. Run the tasks with and without the Skill using equivalent clean contexts.
6. Expand domain coverage only after the vertical slice improves outcomes.

Mark undiscovered pages separately from discovered-but-not-ingested pages. `not_ingested` never means that an API does not exist.

## Task record

Each benchmark should contain:

- stable ID and user-style prompt
- starting repository commit or fixture
- required capability domains
- observable acceptance criteria
- prohibited shortcuts and compatibility fallbacks
- test and runtime validation commands
- expected evidence report, without leaking a preferred implementation
- final outcome and failure classification

## Metrics

Track at least:

- task acceptance pass rate
- unknown or fabricated API count
- blocked API leakage count
- exact official-source traceability
- lifecycle and cleanup defects
- real runtime pass rate
- regressions in existing tests
- time and context cost when practical

Do not claim success from coverage, duplicate count, or build success alone.

## Validation integrity

- Use fresh agents or clean contexts for comparative runs.
- Give the task and raw repository state, not the intended answer.
- Do not expose the known bug, expected diff, or previous diagnosis unless the task itself includes it.
- Preserve outputs, diffs, logs, screenshots, and API inventories as evaluation artifacts.
- Separate failures caused by missing knowledge, weak Skill workflow, repository defects, unavailable runtime, and unclear requirements.
