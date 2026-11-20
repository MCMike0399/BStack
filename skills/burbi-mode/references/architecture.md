# Architecture

1. Name the decision, the callers or writers it affects, and the behavior they still need. Trace their current contract and how state is owned. Identify constraints from the project and the requested change.
2. Compare meaningfully different viable shapes. Use the current design as an option when it can meet the goal. Compare state ownership, what callers have to know, and compatibility for versions that must coexist. If an unknown could change the choice, name the observation that would settle it and gather it when the task's scope allows.
3. Record the chosen or recommended shape, what made it preferable, the behavior it preserves, and a check that can verify it. Distinguish observed evidence from assumptions and say what remains unresolved.
4. Return the decision to the selected playbook. For a design-only request, finish with the recommendation and evidence. For implementation, carry the chosen contract and its check into the dependent work.
