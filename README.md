# personalSKILLs

Personal Codex Skills, organized by purpose rather than by installation order.

## Layout

```text
skills/
  learning/       # Source-code study, explanations, and learning documents
  engineering/    # Future implementation and maintenance workflows
  productivity/   # Future personal workflow helpers
  <category>/<skill-name>/
```

Each skill directory is self-contained and includes a `SKILL.md`. Supporting references, scripts, and assets belong inside that same skill directory.

## Included Skills

| Category | Skill | Purpose |
| --- | --- | --- |
| `learning` | [`source-study`](skills/learning/source-study/) | Locate concepts in a local repository, trace the relevant implementation path, and write or deeply explain Chinese learning Markdown. |

## Adding A Skill

1. Choose the category by the skill's primary purpose, not its implementation language or framework.
2. Create `skills/<category>/<skill-name>/` with a valid `SKILL.md`.
3. Keep the Skill focused. Put optional detailed guidance in `references/`, deterministic helpers in `scripts/`, and output assets in `assets/`.
4. Validate the Skill before committing.
5. Update the table above when adding a user-facing Skill.

## Using A Skill Locally

Copy or link an individual skill directory into the local Codex Skills directory. For example, install `source-study` under the local skills root as `source-study/`; then invoke it with `$source-study`.

This repository is a source collection. It does not include secrets, provider credentials, generated caches, installed dependencies, or machine-specific configuration.
