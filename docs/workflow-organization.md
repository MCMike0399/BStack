# Organizing Burbi-mode playbooks and design methods

## Patterns from existing projects

- PStack’s Refactoring playbook pins observable behavior, calls Architect for a change to a function boundary, delegates scoped edits, and verifies the result. Architect compares shapes using state ownership and caller burden. The parent owns the outcome across those steps. This supports one shared design method called where it helps several playbooks. [PStack Refactoring](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/playbooks/refactoring.md) · [PStack Architect](https://github.com/cursor/plugins/blob/main/pstack/skills/architect/SKILL.md)
- Agent Skills defines an entry file and on-demand reference files. Pi documents relative links within a skill and explicit activation via `/skill:name`. A focused method file under the existing skill fits the current Pi quick start. A sibling skill needs its own registration. [Agent Skills specification](https://agentskills.io/specification#progressive-disclosure) · [Pi skills](https://docs.pi.dev/latest/skills#understand-how-skills-load) · [BStack quick start](../README.md#try-burbi-mode-in-pi)
- Superpowers separates the plan from execution and supplies fresh implementers with scoped task briefs. Reviewers receive the exact diff and relevant constraints. BStack can borrow those handoffs while keeping review frequency governed by the task. Anthropic documents the same context benefit when delegates return distilled results to the coordinating session. [Superpowers planning](https://github.com/obra/superpowers/blob/main/skills/writing-plans/SKILL.md) · [Superpowers delegation](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md) · [Anthropic context engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- Spec Kit gives feature development, bug fixing, and idea assessment their own entry points. Assessment can end with a decision artifact and hand off later when implementation is requested. BStack can use that stopping point without adopting Spec Kit’s commands or templates. [Spec Kit process selection](https://github.com/github/spec-kit#choose-your-process) · [Spec Kit idea assessment](https://github.com/github/spec-kit#idea-assessment)

## Two layouts for BStack

**One skill with a parent-loaded reference.** Keep `skills/burbi-mode/SKILL.md` as the opt-in router and `playbooks/` as the source for each outcome’s sequence. Add `skills/burbi-mode/references/architecture.md` for a reusable design procedure. Put its trigger and direct link in the parent skill. Open the playbook first, then the reference when an unresolved shared interface or state ownership decision affects the work. The method returns the chosen or recommended shape, behavior to preserve, affected callers or owners, the tradeoff, and any check needed before dependent work. The selected playbook resumes after the decision when the task includes implementation. A design-only task uses the playbook for the underlying change and ends with the design and evidence.

**An independently invocable sibling skill.** Give `skills/architecture/SKILL.md` its own metadata and Pi command. It owns the same method and the same design deliverable. The user can open it directly for a stand-alone design task, and Burbi-mode can point to its instructions when it is installed. This adds a second registration and a dependency between skills. It pays off when standalone invocation or reuse from another workflow recurs. Move the method to the sibling skill at that point so the procedures have one source. [Pi skill discovery and explicit commands](https://docs.pi.dev/latest/skills)

## Walkthrough for the one-skill layout

| Request | What the parent opens and returns |
| --- | --- |
| Clean up one file with the existing interface intact | Refactor, then relevant project context. Capture the affected behavior, make the scoped edit if requested, and compare the same behavior afterward. |
| Choose a shared interface used by several callers | The playbook for the user’s outcome, then the architecture reference before dependent work. Compare viable shapes against the preserved behavior and record the chosen contract. Use Prototype when an observation can decide the tradeoff. |
| Design a shared contract and stop before implementation | Open the Feature, Refactor, or Migration playbook for the underlying change, then the architecture reference. Return the recommended contract, evidence, and open decisions. |
| Delegate implementation or independent review | The parent owns the playbook and sends the core, engineering rules, applicable role, and one brief. A Worker receives the selected playbook and the settled contract, starting snapshot, scope, and acceptance check. An Advisor receives the decision question or exact artifact, review criteria, and evidence. The parent inspects the result and verifies the integrated change. |

Start with the one-skill layout. Keep the nine playbooks and two role files in their current locations. A workflow can share the architecture method without routing a one-file edit through it. Add the reference when adopting the architecture step, and use the sibling layout once direct invocation earns a separate entry point. Keep project seats and decisions in the project's guidance and retain the parent's authority over shared choices. [Current router](../skills/burbi-mode/SKILL.md) · [Worker role](../skills/burbi-mode/roles/worker.md) · [Advisor role](../skills/burbi-mode/roles/advisor.md)

## Fable review and proposed checks

Fable 5.2 at medium effort agreed with keeping one skill. It spotted a conflict in the first draft. Opening Architecture directly for a design-only request would bypass the current requirement to open the relevant playbook first. Keep plan-only work in the matching playbook, and use one narrow trigger for Architecture. `references/` fits the Agent Skills layout and keeps the method reachable from the entry file.

Architecture compares choices using known requirements and evidence. Prototype earns its step when the user asks for a prototype or when an observation from exercising a candidate could change the decision. The parent owns routing and selects what to send. Implementation Workers receive settled constraints. A Worker assigned to draft a design can receive the relevant method. An evidence-only Advisor receives the actual artifact and applicable criteria in its brief.

When adopting the reference, check fresh Pi sessions for a small refactor, a shared-interface change, a design-only request, a staged migration, and a request to exercise a prototype. Verify the first playbook read, whether Architecture opened, and the absence of project edits for a no-edit request. Check that the link resolves from the installed skill location and that a delegate can act on its brief without the parent’s transcript.

## Adopted layout

BStack uses one opt-in skill. The parent [routes to the playbook first](../skills/burbi-mode/SKILL.md#choose-a-playbook), then opens [Architecture](../skills/burbi-mode/references/architecture.md) for an unresolved shared design decision. Five fresh Pi + DeepSeek V4.1 Flash sessions opened the expected playbook from a relocated skill directory. Feature, Refactor, and Migration design cases opened Architecture. A tiny refactor and a disposable prototype skipped it. All five kept their fixture files intact.

## Router prose moved to rows and references

On 2026-11-20 the owner asked for a review of the prose under the router table and in the documentation section of `SKILL.md`. The concern was that it was long and possibly wrong, and that it should move into playbooks, references, or other files.

**What other stacks do.** PStack's Poteto mode routes with one line, "Match the task to a playbook and open its steps", and each playbook states its own scope. For example, Investigation says its requests are read-only and re-routes to Bug fix or Feature before a code change. Matt Pocock's writing-for-agents gives the placement test: inline what every branch needs, and push behind a pointer what only some branches reach. Keep one trigger per branch and one source for each meaning. GStack splits a long skill into section files listed in a manifest with trigger text. Superpowers keeps per-harness notes in `references/`. [Poteto mode @ aaeb0ea](https://github.com/cursor/plugins/blob/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/skills/poteto-mode/SKILL.md#playbooks) · [Writing for agents @ abeeaf9](https://github.com/mattpocock/skills/blob/abeeaf95660ba9e8b7c753eb38f441ca707a8823/skills/productivity/writing-for-agents/SKILL.md) · [GStack section manifest @ 87a473e](https://github.com/garrytan/gstack/blob/87a473e5aa2726343d1269c25de1179565a4f649/document-release/sections/manifest.json) · [Superpowers @ 22f0b46](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/using-superpowers/SKILL.md)

**What the review found.** Most of the routing paragraph defined a table row's trigger a second time:
- The converter, test, and Handoff sentences repeated their rows.
- "Then open the playbook for the remaining work" already appears in Handoff step 2.
- The plan-only endings already appear in step 2 of Feature, Refactor, Migration, and Performance.
- Investigation, Review, and Verification already keep project files intact.

The text was otherwise correct. One gap came from live use: in a session that received seven tracker tasks, the agent opened Bug fix and Feature together and kept one PR per task. Only review comments had a per-item routing sentence.

| Old text | New place | Why |
| --- | --- | --- |
| Tie-break sentences for Bug fix, Feature, Migration, Review, Recurring mistake, and Handoff | The matching row of the playbook table | The agent still sees each one before it chooses, with one definition per trigger |
| Several tasks, plan-only requests, a named playbook, follow-ups, work outside the routes | A list under the table | These apply across routes. Review comments generalize to separate tasks, and steps toward one outcome count as one task |
| The no-edit boundary | One bullet in that list | It can attach to any route. A first draft moved it into a reference whose pointer row was 201 bytes, for a 359-byte file. In three live runs it went unopened in one or two no-edit cases per run, different cases each time, so it moved back inline |
| A named Bug fix with a no-edit limit | [Bug fix](../skills/burbi-mode/playbooks/bug-fix.md) | Only that playbook uses it |
| Stage, commit, or publish only when authorized | Carry the work through, beside rule 3 | Every route needs it |
| Maintain comments and documentation | [Comments and documentation](../skills/burbi-mode/references/comments-and-documentation.md) | Only work about to write a comment or project doc, or that confirms a durable fact while edits are in scope, needs it. A first trigger of "you change code" would have loaded it for a one-line rename, which the live `rename` case forbids. |

Find project context and the engineering rules stay inline. Every route needs project context, and [Rule loading research](rule-loading-research.md) found that rules moved out of the entry file went unread. No new folder earned its place. The moved text is on-demand reference, which `references/` already holds under the Agent Skills layout, and gstack's `sections/` folder plays the same role.

`SKILL.md` went from 18,788 to 16,953 bytes, and its cap ratchets down from 19,000 to 17,100.

### Checks

These checks ran on 2026-11-20 with Pi 1.5.2 and DeepSeek V4.1 Flash, using the live suite and disposable export fixtures. Two cases were added: `batch` (two tracker tasks, which must open Bug fix and Feature) and `continue` ("Continue the --dry-run work described in HANDOFF.md", which must open Handoff first). The suite now prints the references each case opened.

- **Baseline wording.** 22 of 24 passed. `preview` (add `--dry-run`) misrouted to Bug fix, and `pickup` read four files before opening its playbook.
- **Final wording, full suite.** 24 of 26 passed, with `unattended` and `continue` failing. `preview` routed to Feature in all five runs across the drafts. Every no-edit case kept the fixture files and git state unchanged, and `rename` opened no reference.
- **Repeated cases, baseline versus final, four runs each unless noted.**
  - `batch`: 4 of 4 versus 3 of 4.
  - `retry`: 4 of 4 versus 4 of 4.
  - `pickup`: 2 of 4 versus 4 of 4.
  - `continue`: 3 of 4 versus 2 of 4.
  - `unattended`: 6 of 8 versus 5 of 8.

  The spread is as large as each difference, so these comparisons are inconclusive.
- **Batches of timeouts.** Whole batches of sessions intermittently hit the 150–300 s timeout on both wordings, while a single probe passed in 13 s. Those batches were rerun and are excluded.

Two drafts regressed and were reverted:
- Telling the agent to open a reference "then or when the work reaches it", together with "open its playbook before starting it", dropped `unattended` to 0 of 4 and then 1 of 4. The agent put off Long-running work until after its first edit.
- "Open each selected playbook first" left `unattended` at 1 of 4.

A Fable 5.2 Advisor at medium effort reviewed the first draft word by word against the old text. It found one blocking issue, the read-only boundary hidden behind a pointer, which is now fixed. It also found eight non-blocking issues, which were applied except where the runs above reverted them. It left "Find project context" unchanged and needed.

Open gaps:
- `continue` opens Feature before Handoff in about half the runs on both wordings. The Handoff row's "Open this before the playbook for the remaining work" has not fixed it.
- `unattended` skips Long-running work in about a quarter of runs on both wordings.

Both cases stay in the suite as the checks for any future fix.
