# Burbi-mode for Rakazo

## Skill draft — not installed

1. Before acting, choose the smallest scope that meets the goal and decide what observable result would show it worked. Before calling the work done, check that result and say what remains unverified.
2. Before changing stateful logic, identify where the state lives, what can change it, and what must stay true afterward. If states are only implied by flags or scattered conditionals, name the states and the allowed transitions first. Restructure only when the task calls for it.
3. If a step needs approval you don't have, stop before taking it and say which approval is missing. Keep working only on what is already authorized and doesn't depend on that step. Don't reach the blocked result another way.

## Review notes — not part of the skill

- **Smallest scope:** Adapted from Poteto-mode’s first-message trigger and [Laziness Protocol](../upstream-reference/pstack/skills/principle-laziness-protocol/SKILL.md.txt). Burbi-mode does not require restating the request.
- **Verify the result:** Lauren Tan’s [conference transcript](https://ai.engineer/code/2026/talks/lauren-tan), 1:11:04–1:11:38, describes reviewing verification artifacts and having agents run the code themselves. Poteto’s [Prove It Works](../upstream-reference/pstack/skills/principle-prove-it-works/SKILL.md.txt) reinforces checking the actual result rather than a proxy.
- **Decide what to check up front and disclose gaps:** These are BStack adaptations, not claims about what Lauren said in the talk.
- **State ownership and implicit states:** Poteto’s [Foundational Thinking](../upstream-reference/pstack/skills/principle-foundational-thinking/SKILL.md.txt) asks what happens when another actor changes shared state. [Model the Domain](../upstream-reference/pstack/skills/principle-model-the-domain/SKILL.md.txt) suggests state machines over scattered booleans or phase checks when appropriate. Naming implicit states and transitions without requiring a refactor is BStack’s adaptation.

- **Approval gates:** Continuing independent work adapts Poteto’s [Never Block on the Human](../upstream-reference/pstack/skills/principle-never-block-on-the-human/SKILL.md.txt). Existing approval requirements still govern; stopping only when approval is missing and forbidding alternate routes to the blocked result are BStack adaptations.
