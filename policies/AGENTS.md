# Global Code Annotation Rule

For every task that adds, modifies, or refactors source code, apply the
`code-annotation-policy` skill throughout the work.

1. Classify the implementation as `S`, `M`, or `L` by behavioral scope.
2. Add proportionate comments while implementing. Explain intent, constraints,
   side effects, boundaries, and non-obvious decisions; do not restate obvious
   code.
3. For coordinate-, time-, animation-, and lifecycle-related code, document
   units, reference frames, ownership, cleanup timing, or other constraints
   when they are not evident from the identifier and nearby code.
4. Document exported/public APIs, meaningful module constants, and complex
   functions when their names alone do not communicate the required context.
5. Scale the documentation process to the repository: keep prototypes concise;
   document module boundaries and state ownership in applications; document
   public compatibility and failure behavior in libraries or platforms.
6. For urgent fixes, make the smallest correct change first, retain comments
   for safety and compatibility decisions, then hand off validation, residual
   risk, and any deferred documentation work.
7. For `L` changes, create or update the repository's implementation document
   according to the skill and local project conventions.
8. Before completion, verify that comments and any implementation document
   still match the final code. State the selected tier in the handoff.

Repository-level instructions override this global rule when they are more
specific or stricter.
