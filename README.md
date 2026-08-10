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
```

Each skill directory is self-contained and includes a `SKILL.md`. Supporting references, scripts, and assets belong inside that same skill directory.

## Included Skills

| Category | Skill | Purpose |
| --- | --- | --- |
| `learning` | [`source-study`](skills/learning/source-study/) | Locate concepts in a local repository, trace the relevant implementation path, and write or deeply explain Chinese learning Markdown. |
| `engineering` | [`code-annotation-policy`](skills/engineering/code-annotation-policy/) | Apply proportionate comments and implementation documentation according to coding-change scope. |
| `engineering` | [`thingjs2-coding`](skills/engineering/thingjs2-coding/) | Implement, review, debug, and refactor ThingJS 2.0 code using verified official evidence and project runtime boundaries. |

## Shared Policies

| File | Purpose |
| --- | --- |
| [`policies/AGENTS.md`](policies/AGENTS.md) | Require the `code-annotation-policy` workflow for source-code additions, modifications, and refactors. |

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
