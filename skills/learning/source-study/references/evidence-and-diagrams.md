# Evidence And Diagrams

## Evidence Rules

- Read the local implementation before asserting a current behavior.
- Read nearby type definitions before interpreting TypeScript generics or method contracts.
- Read tests when behavior is conditional, version-sensitive, or unclear from the implementation alone.
- Distinguish an API's stated contract from one provider implementation's behavior.
- State uncertainty plainly instead of filling gaps with plausible implementation details.
- When the user note is correct, say so briefly and extend it; do not manufacture corrections.

## Diagram Selection

Use a **flowchart** for component boundaries, data flow, ownership, or decisions with branches.

Use a **sequence diagram** for a chronological call path across three or more participants, especially when callbacks, SDK calls, tools, or state persistence cross boundaries.

Use a **state diagram** only for meaningful state transitions such as graph execution, agent routing, lifecycle states, or retry status.

Do not create a diagram for a one-step fact, an API property list, or a relationship already clearer as a short table.

## Mermaid Rules

- Use ASCII labels when Mermaid parser compatibility is uncertain; add Chinese explanation in surrounding prose.
- Keep each diagram focused on one question.
- Name node labels after the actual source concept where possible.
- Include error/cancellation branches only when they change the learning conclusion.
- Do not claim an edge exists unless source, types, or tests support it.

## Source Link Rules

- Link to actual local files using absolute paths.
- Include a line number only after verifying it in the current local checkout.
- Prefer one high-signal link per claim cluster instead of a long list of shallow links.
