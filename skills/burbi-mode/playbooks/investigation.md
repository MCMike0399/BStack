# Investigation

1. Identify the question and the part of the project it concerns. Trace the affected entry point through the code.
2. Check the explanation against the strongest evidence available within scope. Keep project files and shared state intact. Use disposable fixtures outside the project tree for probes that write data. When a missing result matters, make sure the same method can find a known result on the intended surface.
3. Answer the question with what you observed, what you infer from it, and what remains unknown. Cite the relevant code or the command and result, and identify the surface that produced the evidence. If a fix looks warranted, describe it as a recommendation.
