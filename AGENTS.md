# Repository Agent Guidance

This repository is a public, reusable Codex Skill collection. Keep reusable
workflow rules here and keep machine-specific project evidence in the user's
local ThingJS workspace.

## Before changing ThingJS assets

Read these files in order:

1. `policies/AGENTS.md` for repository contribution rules.
2. `skills/engineering/thingjs2-coding/SKILL.md` for ThingJS 2.0 execution rules.
3. `docs/thingjs2-hybrid-policy.md` for the active Hybrid retrieval boundary.
4. `docs/thingjs2-skill-creation-process.md` for the current implementation stage.

When the user supplies an engineer-maintained ThingJS document corpus, treat it
as high-value project evidence for recipes and incidents. It may improve the
workflow, but it does not override official ThingJS 2.0 API facts. Classify
each item before promotion and keep the original corpus outside this public
repository unless the user explicitly provides a public-safe excerpt.

## ThingJS Hybrid boundary

- Generate ThingJS 2.0 only; reject 1.x, compatibility, migration, t3d, and
  guessed APIs.
- Use a local Verified Recipe only as an implementation candidate.
- Use only the allowlisted Context7 ThingJS libraries
  `/websites/thingjs_new` and `/websites/cdn_uino_cn_thingjs_apidocs`. Their
  first-party corpus identity is trusted, but each result still needs exact
  source URL, public owner/member/signature and ThingJS 2.0 provenance checks.
- Keep the ThingJS Skill progressively disclosed: load source-trust and
  engineer-practice references only for the matching task domain.
- Use the Artifact-Set-bound versioned Contract as the only machine-consumption
  API entry. Runtime Surface proves existence only; behavior requires an
  independent Runtime Behavior Test.
- Generate Project ThingJS Usage Surface primarily through AST analysis for
  JavaScript, TypeScript, and Vue script blocks. Regex findings are discovery
  fallback and cannot create verified usage.
- Block controlled target-version mismatches and production unresolved usage;
  treat unversioned latest official changes as `stale_review`.
- If Context7 is unavailable, partial, waiting, rejected, incomplete, or lacks
  a source, use the approved official web sources and local project evidence.
- Use internal/project evidence for project constraints, compatibility, recipes,
  and incidents; never rewrite general official API truth with it.
- Do not add private URLs, absolute machine paths, SDK fingerprints, project
  overlays, internal documents, or runtime results to this public repository.

## Git phase gate

Each implementation phase must leave a reviewable Git checkpoint:

1. inspect status and the complete diff;
2. run the smallest relevant validation and `git diff --check`;
3. commit one focused change;
4. push the current branch only after the checkpoint passes;
5. report the commit, validation, and unresolved evidence boundary.

The repository-level file is intentionally named `AGENTS.md`; do not create a
lowercase `agent.md` duplicate that Codex will not reliably discover.
