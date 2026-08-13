# personalSKILLs

Personal Codex Skills, organized by purpose rather than by installation order.

## Layout

```text
skills/
  learning/       # Source-code study, explanations, and learning documents
  engineering/    # Future implementation and maintenance workflows
  productivity/   # Future personal workflow helpers
  <category>/<skill-name>/
policies/         # Shared Codex instruction files; not independently invokable Skills
AGENTS.md         # Repository-level navigation and ThingJS Hybrid boundary
```

Each skill directory is self-contained and includes a `SKILL.md`. Supporting references, scripts, and assets belong inside that same skill directory.

## Included Skills

| Category | Skill | Purpose |
| --- | --- | --- |
| `learning` | [`source-study`](skills/learning/source-study/) | Locate concepts in a local repository, trace the relevant implementation path, and write or deeply explain Chinese learning Markdown. |
| `engineering` | [`code-annotation-policy`](skills/engineering/code-annotation-policy/) | Apply proportionate comments and implementation documentation according to coding-change scope. |
| `engineering` | [`thingjs2-coding`](skills/engineering/thingjs2-coding/) | Implement, review, debug, and refactor ThingJS 2.0 code through controlled official evidence, Artifact-Set-bound Contracts, AST project usage gates, and traceable promotion queues. |

## Process records

| Record | Purpose |
| --- | --- |
| [`thingjs2-skill-creation-process`](docs/thingjs2-skill-creation-process.md) | Explain the ThingJS 2.0 Skill design, validation boundary, public/private split, and current result. |
| [`thingjs2-hybrid-policy`](docs/thingjs2-hybrid-policy.md) | Define the active Context7, official web, engineer-corpus, local-knowledge, and runtime evidence boundary. |

## Shared Policies

| File | Purpose |
| --- | --- |
| [`policies/AGENTS.md`](policies/AGENTS.md) | Require the `code-annotation-policy` workflow for source-code additions, modifications, and refactors. |
| [`AGENTS.md`](AGENTS.md) | Navigate repository rules and the public/private ThingJS Hybrid boundary. |

## Adding A Skill

1. Choose the category by the skill's primary purpose, not its implementation language or framework.
2. Create `skills/<category>/<skill-name>/` with a valid `SKILL.md`.
3. Keep the Skill focused. Put optional detailed guidance in `references/`, deterministic helpers in `scripts/`, and output assets in `assets/`.
4. Validate the Skill before committing.
5. Update the table above when adding a user-facing Skill.

## Using A Skill Locally

Copy or link an individual skill directory into the local Codex Skills directory. For example, install `source-study` under the local skills root as `source-study/`; then invoke it with `$source-study`.

This repository is a source collection. It does not include secrets, provider credentials, generated caches, installed dependencies, or machine-specific configuration.

## Maintaining This Collection

Follow [CONTRIBUTING.md](CONTRIBUTING.md) before adding, updating, validating, committing, or pushing a Skill.
