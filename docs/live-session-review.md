# Live session reviews

Reviews of Burbi-mode in real work, judged from the session's tool trace, its files and its delegate threads rather than from the agent's own summaries. The project, people and records involved are private and are described here only in general terms.

## 2026-11-20 · Production bug fix with an Advisor (Claude Code, Opus 5.5, T3 Code)

A user-facing action failed in production because a free-text address parser could not classify an order's postal code. The owner used `$burbi-mode` three times in one thread:

1. Investigate the failure and whether a new business rule caused it.
2. Fix it end to end: tests, a DEV journey, a PR, promotion to production, repair of the stuck order, and a Fable 5.2 Advisor at medium effort before promotion.
3. Continue the work when the Advisor returned its result.

At the time of review the PR's CI was still queued on busy runners, and promotion was still pending.

**What held:**
- Each run opened the right playbook as its first action: Investigation, then Bug fix. Bug fix also loaded Project verification, Delegation and Long-running work.
- The agent read production data read-only.
- It used AskUserQuestion for the business decision.
- It kept a decision log outside the tree with a finish condition.
- It showed the new tests failing on the unfixed code, and compared type-checker output against a baseline.
- It reproduced the failure on DEV before the fix was deployed.
- It watched the PR instead of polling.
- The Advisor brief was bound to a snapshot ID, stated the requirement and what was out of scope, and kept the author's conclusions out.
- The Advisor found three material issues. One was a new misclassification in other callers that would have made a free shipping option available for out-of-area orders. The parent checked each claim before acting and added tests that fail on the earlier candidate.

**What fell short, and the change made:**

| Observation | Change |
| --- | --- |
| The fix widened a shared parser whose docstring recorded a deliberate "don't guess" choice and asked callers for a structured field. The staff form had the structured postal code but sent only the free-text address. No alternative fix was compared, and the widened rule reached the storefront and chat callers. | [Bug fix](../skills/burbi-mode/playbooks/bug-fix.md) step 2: code that does what its comment, doc or test says is a recorded decision, so keep tracing past it. A correction to shared code or to a recorded decision is compared with one confined to the failing entry point. |
| The stuck order needed only a field update that did not depend on the deploy, but the plan put that repair after promotion. | Bug fix step 3: do an authorized repair that does not depend on the correction first, and check that it held. |
| In both review rounds the Advisor reran the full deterministic suite that the parent had just run on the same snapshot. | [Delegation](../skills/burbi-mode/references/delegation.md) step 2: list the checks already run, with their results. The Advisor reruns one only when a finding depends on it. |
| The agent had to decide whether a second review round should resume the same Advisor or start a fresh one. It resumed the same one, which then reviewed a fix it had itself proposed. | Delegation step 3 now follows PStack's fresh-by-default rule: the next round goes to a fresh Advisor with the original brief, the new snapshot ID and the previous report. The earlier Advisor is resumed only for state that is costly to move. |

**Not changed, and why:**
- Two seven-minute test suites ran in the foreground. A rule to run slow checks in the background was drafted and then dropped after a second Fable review and the owner's doubt. In both runs the next step needed the result. The agent's fail-before demonstrations checked out the unfixed source in the same tree, which would corrupt a run going on in the background. The existing "advance independent in-scope work" sentence and the harness prompts already cover waiting. The owner's wish to stay able to talk during slow eval runs stays in their own instructions. tstack, Matt Pocock's skills and gstack all run work in the background only when the next step doesn't need its result. If a later session shows a foreground check blocking independent work that doesn't touch the tree, extend the missing-prerequisite sentence with "or a check is still running" rather than adding a new rule. This follows Matt Pocock's grilling skill: "only the questions downstream of it wait."
- The agent offered the owner a fallback, then dropped it without recording why. The dropped option conflicted with a rule recorded in the code, which the agent had not checked before offering it. This happened once, and Long-running work step 4 already asks for rejected alternatives to be recorded.
- The Advisor brief paraphrased four engineering rules instead of sending them. The review was strong anyway.
- State and journey verification was not opened, although the owner asked for a "customer journey". The agent still produced a replayable before-and-after journey script.
- When an old DEV test login was rejected, the agent created a new DEV staff identity outside the app's registration path without asking. This is left for the owner to decide. If they want an approval step, the place for it is [Project verification](../skills/burbi-mode/references/project-verification.md) step 3.

A Fable 5.2 Advisor at medium effort reviewed the research and the draft wording before these edits. It corrected two claims. First, the structured postal code was available only in the front end, and the backend deliberately never borrows another address's zone. Second, the fallback the agent dropped was the right call. It also rewrote the Bug fix trigger around signals a model can observe, and identified the out-of-order repair.

**Untested:** these edits have not yet been exercised in fresh sessions on Opus or DeepSeek Flash. All of them rest on this one session. Two Fable reviews and the owner's decision to proceed are their only other support. The proper fix for the parser problem belongs in that project: the form should send the structured postal code or zone. Prose in this skill cannot substitute for that fix.
