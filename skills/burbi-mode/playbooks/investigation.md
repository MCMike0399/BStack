# Investigation

1. Identify the question and the part of the project it concerns. Trace the affected entry point through the code. For a question about why something was built the way it is, trace its history through the commits, review discussions, and decision records available within scope, and cite what their authors wrote. Say when the records give no reason.
2. Check the explanation against the strongest evidence available within scope. Keep project files and shared state intact. Use disposable fixtures outside the project tree for probes that write data. When the conclusion depends on a search or check finding nothing, first show that the same method finds a known case on the same surface.
3. Answer the question with what you observed, what you infer from it, and what remains unknown. Cite the relevant code or the command and result, and identify the surface that produced the evidence. If a fix looks warranted, describe it as a recommendation.
