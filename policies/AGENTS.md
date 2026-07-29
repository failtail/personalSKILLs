# Global Code Annotation Rule

For every task that adds, modifies, or refactors source code, apply the
`code-annotation-policy` skill throughout the work.

1. Classify the implementation as `S`, `M`, or `L` by behavioral scope.
2. Add proportionate comments while implementing. Explain intent, constraints,
   side effects, boundaries, and non-obvious decisions; do not restate obvious
   code.
3. Document exported/public APIs, meaningful module constants, and complex
   functions when their names alone do not communicate the required context.
4. For `L` changes, create or update the repository's implementation document
   according to the skill and local project conventions.
5. Before completion, verify that comments and any implementation document
   match the final code. State the selected tier in the handoff.

Repository-level instructions override this global rule when they are more
specific or stricter.
