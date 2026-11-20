# Rule loading research

## What each stack loads

**PStack uses an index and full principle skills.** At upstream `0b46ec3`, there are 24 `principle-*` skill files, all marked for explicit invocation. Activating Poteto Mode loads a short trigger and summary for each principle. The mode tells the agent to read the full file for each principle it applies and cite it only after reading it. Autonomy, approval boundaries, delegation and playbook routing already appear in the main file. An idempotence check, for example, starts with a short reminder in the index, then its full skill adds how to recognize partial progress and test recovery. [Poteto Mode](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/poteto-mode/SKILL.md#principles) · [Idempotence principle](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/principle-make-operations-idempotent/SKILL.md)

**BStack loads its 21 engineering rules together on invocation.** [Burbi Mode](../skills/burbi-mode/SKILL.md) already routes further detail to playbooks and references. Agent Skills calls this progressive disclosure and recommends focused references one link away from the main skill. Pi lists the metadata of model-selectable skills and loads the full body on selection. Its explicit-only setting lets a person invoke a skill through `/skill:name` while omitting it from automatic model selection. A disposable offline Pi 1.5.0 catalog check registered the parent skill when its file or directory was supplied. Passing a bundle directory registered both sibling skills. The nested fixture stayed outside each command list. Linked reference files let the parent reach related instructions with one user-facing command. [Agent Skills specification](https://agentskills.io/specification#progressive-disclosure) · [Pi skill discovery](https://docs.pi.dev/latest/skills#understand-how-skills-load)

## What the studies compared

- **SkillsBench v4** matched task runs with and without curated procedural skills, using 87 tasks across 18 model–harness configurations. Mean pass rate rose from 33.9% to 50.5%. Appendix F groups different tasks by the total number and size of available skills. The 2–3 skill group gained 19.0 percentage points over its own baseline, compared with 10.1 for the group with four or more. Since each group contains different tasks and guidance, a fixed-text BStack test is needed to estimate the effect of moving the same rules to separate files. Appendix K also measures actual reads or invocations distinctly from successful outcomes. [SkillsBench v4, §§4–6 and Appendices F and K](https://arxiv.org/html/2602.12670v4)
- **SWE-Skills-Bench** tested explicit invocation of a matching public skill against no skill in 3,920 paired software engineering runs. The mean pass ratio moved by less than one percentage point in each of the four configurations. Individual results varied. This tests adding an entire skill to implementation tasks and leaves packaging of the same instructions as a separate question. [SWE-Skills-Bench, §§3–4](https://arxiv.org/html/2603.15401)
- **Evaluating AGENTS.md v3** studied persistent repo context files. Its developer-authored files lifted average resolution by 2.4 percentage points on CTXbench, a difference within statistical uncertainty. Generated files increased cost by about 20% on SWE-bench and 23% on CTXbench. The authors also found that agents followed instructions more often by exploring and testing more, with no clear relationship between file length and resolution. This concerns task resolution with repo-level context; BStack's opt-in rule loading and safety behavior call for their own measurements. [Evaluating AGENTS.md v3, §§4.1–4.4](https://arxiv.org/html/2602.11988v3)

## BStack comparison

The decision was whether to split the full rule text out of Burbi Mode. A split should preserve the observed outcomes and provide reliable access to rules that matter to the decision. It should also improve the practical context or tool cost enough to justify changing the layout.

I used BStack at `c200218`, native Pi 1.5.0 and DeepSeek V4.1 Flash with low effort. The inline arm copied the current skill. The split arm replaced the 21 full rules in the entry file with a short trigger and summary for each, linking to 21 explicit-only leaf `SKILL.md` files. Each leaf preserved its full BStack rule verbatim. The split entry told Pi to read an applicable leaf in full. The core, the rest of Burbi Mode, the playbooks, the references, the tool set and each task's user prompt were identical. Both arms were invoked as one Burbi Mode skill. The leaves in the test were read by path rather than registered as separate commands.

Three tasks ran twice in each layout, for 12 fresh sessions, with the order shuffled using seed `20261119`. Pi ran in disposable, write-confined workspaces with one core injection and the same model configuration. The fixtures were synthetic or came from BStack's existing export tests.

| Task | Behavior checked independently |
| --- | --- |
| Read-only CLI verification | Reread the known failing storage result from the real CLI retry check. The agent must report the duplicate and preserve the project files. |
| Fix overlapping retries | The real CLI must keep sequential distinct IDs in order, retain only one row per repeated ID, and pass a 20-process overlap check. Only the worker source is writable. The trace must show the project retry check failing before and passing after the fix. |
| Review a rolling writer migration | Two writers share one JSON file. A controlled overlap shows the old writer losing the candidate writer's update. The review must reproduce and explain the loss during coexistence, and preserve the project files. |

Prompt tokens are Pi's reported input plus cache reads and cache writes. The first call measures upfront context, and the total adds every assistant call in the run. This measures context processing, including repeated prefixes. DeepSeek gives cache hits a different cost from misses, so the totals should not be read as a billing comparison. Tool traces show actual reads and checks. A full leaf counts when its rule text appears in a tool result. [DeepSeek usage fields](https://api-docs.deepseek.com/api/create-chat-completion/) · [DeepSeek context caching](https://api-docs.deepseek.com/guides/kv_cache)

In a separate offline Pi catalog test using the same generated files, registering the router with its leaves nested underneath exposed one skill command. Registering the router and the 21 leaves as siblings exposed 22 commands. Both layouts can use the same full rule text; their discoverability and loading costs depend on the harness and registration.

### Results

All 12 runs used the expected provider and model, opened the requested outcome's playbook first, stayed within the file scope, and passed the behavioral rubric. Both fixes in each arm passed an independent concurrent CLI check. Both review runs in each arm reproduced the lost update while the old and new writers coexisted. **Pi read zero full rule leaves across all six runs in the split arm.** Its summaries, playbooks, and project evidence were sufficient for these cases. The test did not show that Pi reliably retrieves more detailed instructions when a case needs them.

| Measure | Full rules inline | Trigger summaries + linked rules |
| --- | ---: | ---: |
| Behavior passed | 6/6 | 6/6 |
| Correct playbook first | 6/6 | 6/6 |
| Entry file, UTF-8 bytes | 17,399 | 10,987 |
| First model prompt tokens, median (range) | 5,874 (5,850–5,894) | 4,714 (4,696–4,740) |
| Whole-run prompt tokens, median (range) | 44,905 (26,855–116,253) | 39,303 (27,220–122,653) |
| Tool calls, median (range) | 9 (8–18) | 9 (4–14) |
| Wall seconds, median (range) | 19.7 (11.4–44.7) | 16.7 (12.1–40.4) |

The split layout used about 20% fewer input tokens on the first model call. The whole-run and wall-time ranges overlap widely, so this sample does not establish a reliable reduction in either. The split arm's apparent savings also reflect leaving every full leaf unread. Results with those files actually loaded would measure a different context and tool cost.

### A case that needed a detail

I ran one additional matched review pair after the primary tests. The migration plan included a temporary warning proxy that would be removed once things looked settled. The project had no rule requiring a concrete retirement condition. Full BStack rule 21 requires one, while the split index's summary names verifiable end and intermediate states without that specific requirement.

Both runs flagged the proxy's removal criteria in the review rubric and preserved the fixture. The split run read rules **5, 9, and 21** in full. This shows that Pi can retrieve a useful leaf in a more open-ended case. It is one exploratory pair, so the result does not establish how reliably Pi will retrieve that detail or what it will cost across tasks.

## Recommendation

Keep one opt-in Burbi Mode entry point. Keep short rules that affect many tasks, including approval boundaries, scope, and the obligation to verify, in its inline instructions. Use a direct link from the relevant playbook for deeper methods that only some tasks need. BStack already does this for verification, shared design and cross-agent coordination. A separate skill earns a command when someone will invoke its workflow independently.

Our pilot supports the current layout for now. It found a repeatable first-call context saving for the trigger index, similar outcomes on the chosen tasks, and one successful full-rule retrieval in an exploratory case. It leaves open reliability on rule-specific details across tasks and models. The next useful comparison, if the inline file's context becomes a practical cost, would hold the task and rule semantics fixed and check cases that deliberately require a leaf-only clause. Measure whether the clause reaches the agent before the decision and judge the actual outcome.
