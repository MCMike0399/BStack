# Feature

Open [Project verification](../references/project-verification.md) before planning checks that need a running app, device, or external dependency the usual checks do not exercise, and before choosing release checks. Before writing or updating a verification recipe, open [Verification recipes](../references/verification-recipes.md).

For a request to add tests, the behavior under test is the example. If a new test fails on current code, report the defect and keep the expected value from the requirement.

1. Describe who uses the new behavior, how they reach it, and an observable example that would satisfy the request. Identify the existing behavior and interfaces that the example still depends on.
2. Trace the affected path. Decide the shape of any data or state before changing its logic. For a plan-only or design-only request, finish by reporting the approach and its checks.
3. Build the smallest slice that yields a useful result through the real entry point. For dependent slices, verify each before building on it.
4. Run the acceptance example and the relevant existing checks. Exercise a consequential failure or recovery path when the change affects one. Report what works for the user, the evidence, and any gap.
