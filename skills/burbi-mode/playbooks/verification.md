# Verification

When the check exercises a running app or its public entry point, open [Project verification](../references/project-verification.md) before running the check.
For checks involving retries, event order, timed transitions, or recovery, also open [State and journey verification](../references/state-and-journey-verification.md).

1. Name the behavior and a pass condition before running the check. When a revision is requested, confirm the checkout or build matches it. Use a disposable checkout when needed and authorized. A result from an unconfirmed revision leaves the requested revision unverified. Use the project's documented procedure for the affected entry point. When a substitute is needed, identify which part of the original behavior it can exercise.
2. Run the check within the task's existing authorization. Use disposable inputs for probes that write data and preserve project files and shared state. Confirm the run reached the intended path and inspect any relevant side effects.
3. Report the command or steps, the observed result, and the verdict for the surface you exercised. Report a blocked or incomplete check as inconclusive and state what remains unverified. Treat a request to implement a fix as a new routing decision.
