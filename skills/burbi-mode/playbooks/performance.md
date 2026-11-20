# Performance

1. Name the workload, the metric, and the decision the measurements should inform. Find the project's existing benchmark or capture a repeatable baseline on the affected surface. Record the inputs, conditions, run count, and spread.
2. Check that the runs exercised the intended work, including the cache state relevant to the request. Use measurements or traces to locate the cost. For a measurement-only request, finish by reporting the baseline and what it supports.
3. When a change is requested, target the measured cost. Rerun the same workload under comparable conditions and check that the observable behavior still holds.
4. Report the baseline, any comparison, the spread, and the evidence for the limiting factor. Use rule 8 to judge whether a difference is conclusive.
