# Adopting PStack behavior skills in Burbi-mode

## Goal

Burbi-mode is the entry point to BStack. The aim was to borrow the PStack skills that change how an agent works, such as `/correct`, `/automate-me` and `/reflect`, and the ideas in the talk "All Code Is Slop (Except Mine)". Each idea had to become a route an agent can reach from the Burbi-mode router. Sources: [PStack](https://github.com/cursor/plugins/tree/main/pstack) and the [talk](https://www.youtube.com/watch?v=ZZ19zhYnDKY).

The talk's central claim decides most of the mapping. Each correction to an agent should become something deterministic, in this order: architecture and API design, then types, lint rules and compilers, then tests and verification, with prose last. Agents copy the patterns they find in a codebase, so workarounds and deprecated code spread. Review shifts to verification artifacts.

## What changed

| PStack source | Burbi-mode location | Notes |
| --- | --- | --- |
| `/correct`, the talk's ladder | [Recurring mistake](../skills/burbi-mode/playbooks/recurring-mistake.md) playbook | Rule 4 already covers a repeat inside another task. This route is for when preventing the mistake is the task itself. |
| `/automate-me`, `/reflect`, the authoring-a-skill and eval playbooks | [Guidance](../skills/burbi-mode/playbooks/guidance.md) playbook | Covers changing BStack itself or a project's agent instructions, and evaluating how agents follow them. |
| session-pickup and pause-safely playbooks | [Handoff](../skills/burbi-mode/playbooks/handoff.md) playbook | Treats the earlier session's record as claims to verify, which matches Coordination. |
| `/figure-it-out`, `/show-me-your-work`, the autonomous-run and multi-phase-plan playbooks | [Long-running work](../skills/burbi-mode/references/long-running-work.md) reference | Opens alongside a playbook for unattended or audited work, and gives the sequence when no playbook fits. |
| `/blast-radius` | [Review](../skills/burbi-mode/playbooks/review.md) step 2 | Name each fact the change relies on to be safe and test it by running code. |
| `/why` | [Investigation](../skills/burbi-mode/playbooks/investigation.md) step 1 | Answer from the commits, review discussions and decision records. |

The router lists every reference in one "Open a reference" table. Playbook lines that link a reference repeat the table's condition rather than restating it. A structural test checks that every skill file can be reached by relative Markdown links from `SKILL.md`, that each such link resolves, and that each stays inside the skill directory.

## Already covered or not adopted

This list covers the skills and playbooks that shaped the decision. It is not a full inventory of PStack.

- **Already covered.** The 24 `principle-*` skills are covered by engineering rules 1–21 and Carry the work through, except `principle-guard-the-context-window`, which has no counterpart. `/architect` and `/arena` match the Architecture reference and the Prototype playbook. Feature maps and runtime verification are in Project verification and Verification recipes. `/statechart` and the formal verification skills are in State and journey verification. `poteto-agent`, `poteto-mode/worker.md`, `/swarm` and `/interrogate` are in Delegation, the Worker and Advisor roles, and the Review playbook. `/tdd` is in Bug fix step 3, and the hillclimb playbook is in Performance.
- **Comment ban.** Not adopted. `/no-comments`, Comment Sicko and the talk ban most comments. BStack keeps durable context in comments and documentation (commit `896bdc4`). It already prefers a design or check over a comment that warns about a mistake.
- **Restating the goal.** Not adopted. Poteto-mode and `/in-your-own-words` restate the goal first. The BStack core says not to restate a request unless that resolves an ambiguity.
- **Prompt and reply tools.** Not adopted. `/sharpen`, `/poteto-help`, `/ketchup`, `/recall`, `/teach` and `/bro` reshape the user's prompt or the agent's reply. They are not routes for engineering work. Each could become a sibling skill if a need recurs.
- **PR and release process.** Not adopted. Babysit, shipping, autopilot-full, autopilot-stack, opening-a-pr and worktree-cleanup depend on Cursor, GitHub and model-selection conventions. Project verification step 2 already covers the order of release checks.
- **Writing standards and specialist forensics.** Not adopted. `/unslop` and `/technical-writing` are prose standards, and the runtime-forensics, trace-forensics and visual-parity playbooks are specialist workflows. The documentation section and Investigation cover the general case.
- **Per-role model tables.** Not adopted. `/setup-pstack` pins a model to each role. BStack stays model-agnostic. Delegation checks that the launcher can select a required model.

## Tests

Each run was a fresh DeepSeek Harness session with DeepSeek V4.1 Flash at high reasoning effort, launched through T3 Code on 2026-11-20. Each worked in a disposable copy of `tests/fixtures/exports`, outside the repository, with git history added where the case needed it. The agent received only "Use the burbi-mode skill… Read SKILL.md first… Request: …". Each run was judged from its tool trace and the files it left. The parent reran each check the agent reported as passing, and reran each new check against the real past mistake.

| Round | Wording | Runs | Correct first playbook | What changed afterward |
| --- | --- | ---: | ---: | --- |
| 1 | First draft | 7 | 7 | Overnight never opened Long-running work. Recurring mistake also fixed an unrelated retry defect. |
| 2 | After the first Fable review | 7 | 7 | Long-running work opened. Near misses routed correctly: a recurring product bug to Bug fix, "write a lint rule as a script" to Feature, a skill diff review to Review, a pause to Handoff with no edits. Recurring mistake wrote only the note and called a check out of scope. |
| 2b | Check stated as part of the route | 2 | 2 | Both added a check that fails on the real past commit. One rewrote the already-failing retry check instead of narrowing its own. |
| 3 | After the second Fable review | 4 | 4 | Recurring mistake added a narrowed check, wrote a one-sentence note naming it, and left the retry defect as a report. Overnight, pickup and pause behaved as intended. |
| 4 | After the third Fable review | 1 | 1 | Recurring mistake repeated the round 3 result on the final wording. |

Routing held in all 21 runs. Every routing failure was a reference trigger or scope wording problem, and each was fixed and rerun. Fable 5.2 at medium effort reviewed the exact wording three times. The first two reviews found 5 and 3 blocking issues. The third found none, and its 8 wording notes were applied before round 4.

Known gaps:
- The cases are synthetic and use one fixture. Each wording was run once or twice, so these results show routing on these requests, not a reliability rate.
- The T3 delegate wrapper sometimes prepends "Act as the test sub-agent", so the agents under test were not fully blind.
- The live Pi suite (`BSTACK_TEST_PI=1`) has a case for every playbook and runs all cases concurrently (`BSTACK_PI_WORKERS` overrides), about 60–80 s for 24 cases. Its single runs on the revised wording passed 20 of 22 twice, with different cases failing each time because Flash ran `ls` or read a named file before opening the playbook. Treat one failing first action as noise until it repeats.
- `tests/test_pi_core_loading.py` failed intermittently in this session: 5 errors in about 100 s, which matches five 20-second Pi launch timeouts. It was not reproduced in seven later runs, and the cause is unconfirmed.

`SKILL.md` grew from 17,356 to 18,703 bytes in rounds 1–4. [Rule loading research](rule-loading-research.md) measured a 17.4 KB inline layout against an 11.0 KB split one: outcomes matched, the split saved about 20% of first-call tokens, and whole-run tokens and time were indistinguishable. In the split layout, Flash did not open the moved rule files on tasks that did not need them, and one exploratory run did open three. Rules therefore stay inline.

## Whole-skill review (rounds 5–7)

The owner's aim is engineer-grade output on everyday work with any model, so Burbi-mode loads on most tasks. Fable 5.2 at medium effort reviewed the whole skill, not only the new routes, three more times.

- **Round 5 (whole skill).** Three blocking issues:
  - Recurring mistake contradicted itself on existing violations.
  - Adding tests had no route.
  - The Project verification trigger was worded four ways, and two references linked each other, so small bug fixes loaded both.
  - Applied with these changes: one condition wording that a test pins; a Verification recipes row; rule 4 now names the design, types, lint, then tests order; new rule 22 to review your own diff; the Delegate section moved into Delegation; and one name each for the parent and the record.
- **Round 6.** Two blocking issues introduced by round 5:
  - "Repair tests uses Feature" would let an agent edit a failing test until it passes.
  - Rule 22 could revert changes the agent did not make.
  - Also: staging now needs authorization, and nine live-test weaknesses were fixed.
- **Round 7 (final).** One blocking issue: the failing-test sentence keyed on a test's state, not the request. Also a test helper that counted `2>&1` as a write. Both fixed, and live cases added for a failing check and for asking why it fails.

`SKILL.md` is 18,788 bytes. The cap is now 19,000, a ratchet rather than a measured threshold. Playbooks are capped at 3,500 bytes, references at 4,500, and roles at 1,500.
