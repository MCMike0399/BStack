# Review

When reviewing claims about a replayed or recorded journey, open [State and journey verification](../references/state-and-journey-verification.md) before assessing the evidence.

1. Identify the version or diff under review and the requirements and conventions that apply. Name the comparison point when it matters. For a design review, use the proposed design as the artifact.
2. Trace changed behavior through affected callers and supported cases. Name each fact the change relies on to be safe. Look beyond the diff, in stored data, wire formats, configuration, and separately deployed readers, for cases where it does not hold. When feasible and authorized, test it by running the real code with a disposable probe outside the project tree. Otherwise report it as unproven. Check whether the change meets the request and follows project conventions. Ground findings in code, a reproducible check, or a concrete failing scenario.
3. Report actionable findings in order of impact, with their locations and evidence. State what the review covered and what remains unverified. If the user asks to implement a finding, route that work by its requested outcome.
