# Verification recipes

Apply the recipe steps within the task’s requested scope. For a design-only request, return the proposed recipe and any unverified prerequisites.

1. Find the project’s existing guidance and commands. Choose one affected user journey or caller operation to start. Reuse the existing feature map, recipe, and driver where they fit. Record missing prerequisites or tooling by the behavior they prevent you from checking.
2. Use the repo’s established location. Write for a reader with no prior context. Record the entry point, disposable starting state, launch and readiness checks, exact action, pass condition, relevant effects, and where to inspect or save the result. Name the diagnostic signal to check on failure and how to clean up the resources the run starts. Link the recipe from the existing project instructions or feature index when that edit is in scope. Otherwise include the pointer in the handoff.
3. Follow the recipe once within the task’s authorization. Prepare the surface, run the action, inspect the result, clean up, and confirm the evidence can still be found. In the recipe, mark any part you could not exercise in the target environment and record what the run reached and which prerequisite was missing.
4. When updating a recipe, trace a mismatch to the instructions, the driver, or the product behavior. Correct the instructions when they describe the intended behavior inaccurately. Report driver limitations and product regressions with evidence and address them when the task authorizes that work. Rerun any changed step whose outcome affects the proof.

For a recipe whose result depends on event order, time, or recovery, record the build, starting state, ordered inputs and actions, and any timing, seed, or trace needed to replay the check. See [State and journey verification](state-and-journey-verification.md).
