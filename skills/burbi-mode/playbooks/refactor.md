# Refactor

1. Identify the behavior callers rely on and the structure that makes the code harder to change. Before editing, run checks that exercise the affected interface or capture representative inputs and outputs there. Include a meaningful edge case when the structure touches it.
2. Choose the smallest structural change that improves the path. For a plan-only or design-only request, finish by reporting the planned structure, the behavior to preserve, and its check. For implementation, move behavior in verifiable steps, reusing established interfaces and following the compatibility rules for callers. Preserve the recorded behavior and report defects outside the requested refactor separately.
3. Rerun the baseline on the same inputs and compare observable results. Report the structural improvement, the behavior covered by the comparison, and any behavior that remains unverified.
