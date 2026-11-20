# Verification research

## Lauren Tan’s verification workflow

Tan describes verification as part of the environment that makes autonomous coding credible. The agent runs the changed behavior and gives reviewers artifacts they can inspect, such as screenshots, videos, traces or diagrams. Her feature map names the product from the user’s point of view. Repository-specific drivers give the agent reusable actions and observations. Her CODE talk then adds model checking, proofs for selected algorithms and generated UI actions. The release example builds on that inner verification loop. [AI Engineer CODE talk and timestamped transcript](https://ai.engineer/code/2026/talks/lauren-tan)

### Runtime verification

PStack’s explicitly invoked `create-verification-skill` authors a separate, repository-owned skill. It reads the repo to identify the user surface, launch command and readiness signal, existing driver, observable effects, and disposable or shared resources. It prefers existing project harnesses. Its fallbacks adapt to the surface, such as browser/CDP, PTY or HTTP. The output is `.cursor/skills/verify-<app>/SKILL.md` with launch, health diagnosis, drive, evidence and cleanup instructions. The sibling `features/README.md` indexes feature files. Each feature describes entry points, concrete actions, observable results, and prerequisites or gotchas. [Runtime skill authoring](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/create-verification-skill/SKILL.md) · [Feature map example](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/create-verification-skill/references/feature-map-example/create-note.md)

Authoring requires a first run of the generated instructions from launch and health check through one mapped journey and teardown. The evidence must survive cleanup. Later, a coding agent selects the affected journey and checks its actual surface, including relevant side effects. The example confirms a save by reopening the record through another user-facing view. The guide asks for exact commands and outputs and treats an unavailable check as inconclusive. PStack’s separate maintenance workflow checks the map against source and runs each feature live, with one coordinator driving the app. The pass distinguishes inaccurate docs, limitations of the driver, and product regressions. [Proving the generated skill](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/create-verification-skill/SKILL.md#4-prove-the-generated-skill-before-handing-it-over) · [Verify and ship guide](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/docs/guide/06-verify-and-ship.md) · [Runtime skill maintenance](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/maintain-verification-skill/SKILL.md)

### Formal verification and generated UI tests

- **TLA+ and TLC** fit a question about possible orders of events, such as whether two workers can own the same lease. TLC checks the stated properties of the model under its configured bounds and assumptions. PStack’s `statechart` turns the model into a user-facing Mermaid diagram and reports paths to violated rules. Replay a reported path against the implementation before calling it a product defect. Keep the model’s mapping to real code, including atomic steps and omitted behaviors, reviewable. [TLC model checker](https://lamport.azurewebsites.net/tla/tools.html#TLC) · [PStack statechart](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/statechart/SKILL.md)
- **Lean and other code-level verification** fit a precise property about an algorithm or implementation. A Lean proof establishes its stated theorem about the definitions in scope. Applying a proof to shipped code requires checking that connection. PStack’s formal authoring skill chooses one consequential property and a tool suited to it. It generates a project-local skill without imposing a name or fixed destination. It records covered code, the sync commit, assumptions, bounds, and a rerun command. It exercises the check on a broken scratch variant and restores the baseline. A separate maintenance pass checks whether code changes invalidate the model or proof. [Lean theorem proving](https://lean-lang.org/theorem_proving_in_lean4/) · [Formal skill authoring](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/create-formal-verification-skill/SKILL.md) · [Formal skill maintenance](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/maintain-formal-verification-skill/SKILL.md)
- **Bombadil** explores the running UI with generated action sequences and evaluates declared properties over observed states. Its trace records actions and state and can embed screenshots. Reproduction can diverge, and shrinking searches for a shorter failing sequence. Useful evidence is a named property, the observed violation and a reproducible action trace. A passing bounded run supports the explored cases and the properties it actually checked. [Bombadil introduction](https://antithesishq.github.io/bombadil/browser/1-introduction.html) · [Bombadil workflow and CLI manual](https://antithesishq.github.io/bombadil/browser/bombadil-manual.txt)

### State machines and replay

Tan pairs a feature map with a reusable driver so an agent can perform the real action, then bring back evidence a reviewer can inspect. Her statechart example adds a view of the behavior in the user's language alongside screenshots or video. For a CLI or UI check, record the starting fixture, build, action sequence, and what changed. Use stable selectors or command arguments and verify the relevant stored or external effect alongside the visible result. [Tan's talk, runtime verification and statecharts](https://ai.engineer/code/2026/talks/lauren-tan#review-behavior-and-evidence-not-only-the-diff) · [PStack runtime authoring](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/create-verification-skill/SKILL.md)

PStack's TLA+ statechart labels states and transitions for the reader, marks violated rules, and reports the shortest counterexample paths found by TLC. It also reports rules left unchecked by bounds or errors. Report the property, checked model and bounds, and the failing sequence in plain language. Replay that sequence against the implementation one step at a time before reporting a product bug. PStack's formal verification authoring also asks the author to show the check can reject a broken variant and record the source revision where the model or proof was checked against the code. [PStack statechart handoff](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/statechart/SKILL.md#hand-off) · [PStack formal authoring](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/create-formal-verification-skill/SKILL.md)

For generated UI checks, save the failing property, original trace, fixture, tool version and options, plus the seed when the runner exposes one. Bombadil replays a trace with the original options and reports divergence. Its shrink command searches for a shorter trace that still breaks the same property. Keep the shortest reproduced sequence with the original evidence so a person can understand the failure and turn it into a repeatable regression check. [Bombadil replay](https://antithesishq.github.io/bombadil/browser/4.1-reproducing-violations.html) · [Bombadil shrinking](https://antithesishq.github.io/bombadil/browser/4.2-shrinking-violations.html)

### Verification across a release

The supplied production slide redraws Cindy Sridharan’s lifecycle. Her service-testing article distinguishes deploy, release, and post-release. Deployment can provide evidence about the installed candidate and environment before it receives ordinary traffic. Release can compare a limited rollout with a baseline. After release, logs, metrics, traces and profiles can reveal behavior under real workloads. Which phases a project can exercise depends on its release mechanics and authorization. The article scopes its production techniques to services controlled by the team deploying them. [Testing in Production, the safe way](https://copyconstruct.medium.com/testing-in-production-the-safe-way-18ca102d0ef1)

### Upstream reread before adoption

Tan’s talk ties verification to reviewable evidence from the behavior people use. PStack’s current source at `0b46ec3` makes this concrete. Readiness means the instance can serve the intended action. A run records the action, the result, and relevant side effects. When a dry run or substitute is needed, observe what it actually exercises and record any setup that the target still needs. Keep setup and maintenance separate from using the recipe. Prove a new recipe from launch through cleanup, then check that its evidence survived. When a maintained recipe and the app disagree, check whether the documentation, the driver, or the product behavior changed. For formal evidence, record the checked property, bounds, and last revision where the model or proof matched the code. These are the behaviors to carry into Burbi Mode, with each repository supplying the commands and tools. [Tan’s runtime verification discussion](https://www.youtube.com/watch?v=ZZ19zhYnDKY&t=4264s) · [Runtime authoring](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/create-verification-skill/SKILL.md) · [Runtime maintenance](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/maintain-verification-skill/SKILL.md) · [Formal maintenance](https://github.com/cursor/plugins/blob/0b46ec399d55f2829e88822998f53b84944837d3/pstack/skills/maintain-formal-verification-skill/SKILL.md)

## BStack verification footprint

Keep the verification method in Burbi Mode and the runnable recipes in each repository. The repo already knows how to start its app, seed data, drive a real entry point, diagnose a failure, and collect proof. A small feature map makes that knowledge reachable in a fresh agent session. ChopperBot’s topic map already routes to its Workshop guide. Reuse the project’s existing topic map and evidence requirements where they fit.

| Where | What it owns |
| --- | --- |
| Burbi Mode | Select the playbook, then open [Project verification](../skills/burbi-mode/references/project-verification.md) when runtime, environment, release, or recipe work calls for it. [Verification](../skills/burbi-mode/playbooks/verification.md) gives a check and verdict. [Feature](../skills/burbi-mode/playbooks/feature.md), [Bug fix](../skills/burbi-mode/playbooks/bug-fix.md), and [Performance](../skills/burbi-mode/playbooks/performance.md) integrate checks into the work. |
| Project instructions | Point to the relevant recipe by user-facing behavior or affected area. Reuse the existing `AGENTS.md`, `CLAUDE.md`, or topic index. A small repo can keep everything in one page. Split out feature pages when it makes them easier to find and maintain. |
| Project recipe and tools | Describe the surface and the reusable way to exercise it. Keep runnable commands in scripts, test configs, or existing runbooks. Point to those authoritative definitions. Specify the host, fixture, dependency and credentials class only where it changes what the check proves or affects what it touches. |
| Evidence from a run | Record the checked revision or build, environment and surface, what actually ran, observed result, receipt or artifact, and remaining gap. Preserve the evidence across cleanup. The parent hands the relevant recipe and acceptance check to a Worker, then inspects the result on the integrated revision. |

Pi can load the project pointer through its normal context-file discovery and can open a repo Markdown recipe by path. ChopperBot already points `AGENTS.md` at `CLAUDE.md`. A project that wants a direct command can later expose a verification skill from `.pi/skills/` in a trusted project, or load a skill explicitly with `--skill`. Keeping the recipe in Markdown lets the same content work in other harnesses. [Pi context-file discovery](https://docs.pi.dev/latest/configuration#context-files) · [Pi skills](https://docs.pi.dev/latest/skills) · [ChopperBot project instructions at v2.16.0](https://github.com/MCMike0399/ChopperBot/blob/14b04131c2046def46487bfa7c930fddc49b9089/CLAUDE.md)

A pointer can be one sentence in an existing routing table. For example, “For Workshop attachment delivery or storage, read the verification section of `docs/capabilities/workshop.md`.”

### State transitions and reviewable journeys

[State and journey verification](../skills/burbi-mode/references/state-and-journey-verification.md) gives a replay procedure to the agent running the selected playbook. It pairs the feature map with a driver, starting state, ordered actions, expected effects and a repeatable assertion. This is useful when the same steps in a different order, a retry, or a restart can change the result. Generated cases and formal counterexamples feed shorter regressions against the implementation when they can be replayed there. A visual check binds the recorded action and result to the build and accompanying state evidence.

**UMO on Alienware.** I read the completed T3 thread `mcp:531b09b3-e2ab-4d8c-9a3a-674f68da5a14`, the repo’s routing and evidence guides, its Square runner, and the installed E2E Showcase skill and UMO example. The project's map separates native customer behavior, merchant web screens, provider effects and the diagnostics surface. Its earlier Square runner and skill pair visible steps with durable provider and application assertions, finalize recording during cleanup, and preserve originals for a recut. The skill records an instance where overlapping UI controllers interrupted the native card sheet.

On Alienware I checked the v6 files with `ffprobe` and verified both SHA-256 receipts. The client cut is 3840×2160 at 30 fps with 314 chapters, and the full reference has 463 chapters at the same resolution. I independently sampled two J8 frames from the client cut. At **26:15** the first incident shows a deadline of **10:00**. At **26:33** both incident rows show **10:01**. The J8 receipt records the server's order of marks and a deadline 600 seconds after the second mark. The edited caption agrees with the screen and calls the product decision open. The thread also identifies a later ticket-scroll fix in `e737c8c` as outside the captured build. I checked file identity, metadata, the selected frames, the receipt timestamps and the fix diff. The thread records broader decode and visual review coverage.

For a regression, preserve the two mark actions, their relative times and the initial order state. Once the product rule is settled, assert the server deadline and what each row displays. Keep a short replay entry point for the next agent and link the reviewer to the relevant frames. The E2E Showcase skill continues to handle presentation and export details when a video is requested.

| Slide | What to take into UMO |
| --- | --- |
| Feature map and driver | Map the barista's incident action to the merchant web route, and the customer's return to the ticket to the native route. Reuse Playwright and Maestro for those surfaces. Compare the displayed deadline with the same order's application receipt. One reproducible runner invocation can coordinate the steps and save their evidence. |
| State machine and proofs | For J8, begin with one paid order, then mark the first and second incidents at controlled times. Record the expected transitions once the shared-deadline rule is decided. Add the deterministic two-mark regression first. A bounded TLA+ model earns its cost if timing, retries or competing actors leave important sequences unexplored. Replay any counterexample against the real entry point. A Lean proof could address a precise pure calculation, such as a deadline or rounding function, when it can be tied to the implementation. |
| UI property-based testing | Try varied sequences of marking, navigating away, reopening and refreshing in an isolated run. One candidate property to agree with the owner is that reloading reflects the same recorded deadline when no new incident action occurs. Keep the original failure trace and a short replay that preserves the violation. Captions and screenshots can then point to the exact failing action and state. |

These are test designs for future UMO work. The current review inspected the recorded artifacts and receipt.

### Writing or maintaining a recipe

A request to write or update a recipe uses Feature unless the user names another playbook. The [Verification recipes reference](../skills/burbi-mode/references/verification-recipes.md) starts with existing tools and one behavior, then asks the author to prove that a fresh run can follow the instructions and retain its evidence. Maintenance distinguishes drift in the instructions, limitations of the driver, and changes in product behavior.

### A one-feature recipe

Copy the structure into the repo’s existing docs when authoring a recipe. Use the sections the feature needs.

```markdown
# <User-facing behavior>

## Reach
Actor, starting state, and entry point a real user uses.

## Prepare
Candidate revision or build, environment, command or runbook, disposable data,
and the readiness check that confirms the relevant dependency can serve the test.
Name the effects of running it and the prerequisites for using a shared surface.

## Drive
Existing test selector, CLI command, HTTP flow, browser driver, or simulator inputs.
Include the recovered or failing path when it changes the acceptance result.

## Observe
What proves the outcome in user terms, including relevant persistence or external
effects. Where to inspect the actual result and save evidence tied to this run.

## Diagnose
Where to look when readiness or the behavior check fails. Name the relevant log,
trace, snapshot, or debug command and the signal that narrows the cause.

## Clean up
Remove the resources created by this run. Confirm cleanup when it affects shared
state. Keep the evidence where the next agent or reviewer can retrieve it.
```

Choose the driver and the evidence together. For an Electron settings change, a real app action followed by reopen and read-back may answer the question. For a CLI change, the real executable, exit status, output and resulting files may be sufficient. For an API retry, compare the returned result and durable state after a duplicate request. For a simulator journey, record the input sequence, resume checkpoint and observable end state. Add generated sequences when sequences are the uncertainty. Add a formal model or proof when the property is precise, a finite test suite has a meaningful coverage gap, and there is a useful connection back to the implementation. For release work, use the project’s release procedure and identify which receipts speak to the candidate build, the rollout, and behavior after release.

## Worked example from ChopperBot Workshop

**Feature.** A Workshop member requests documents and receives the final deliverables together. Scratch or recalculation copies stay out of the delivery. Expected evidence is one Discord message containing the intended final attachments and the associated durable storage records.

| Surface | What is available and what it supports |
| --- | --- |
| Pre-production | The repo uses Vitest with in-memory SQLite for many local checks. The Pi trace ended with 1,768 passing tests. The v2.16.0 GitHub ARM CI log records **1,745 passed and 23 skipped** out of 1,768 tests. The job also ran formatting, typecheck and build. The counts describe different environments. [CI workflow](https://github.com/MCMike0399/ChopperBot/blob/14b04131c2046def46487bfa7c930fddc49b9089/.github/workflows/ci.yml) · [CI run](https://github.com/MCMike0399/ChopperBot/actions/runs/44650217459) |
| Delivery integration | The repo already has a driver in `scripts/e2e-workshop-delivery.ts`. It seeds final files and scratch copies, calls the real delivery helper, then checks real Discord attachments, the manifest and MinIO read-back when MinIO is configured. The script tests nonempty MinIO read-back, so a claim about byte identity would need a separate comparison. It creates and cleans up a temporary private Discord channel and test data. Both Pi tool traces reported successful attachment counts and MinIO read-back. [Tagged driver](https://github.com/MCMike0399/ChopperBot/blob/14b04131c2046def46487bfa7c930fddc49b9089/scripts/e2e-workshop-delivery.ts) · [Workshop verification record](https://github.com/MCMike0399/ChopperBot/blob/14b04131c2046def46487bfa7c930fddc49b9089/docs/capabilities/workshop.md) |
| Build and deployment | I verified that GitHub published `v2.16.0` at `14b0413`, CI’s check and release jobs passed for that commit, the Pi service’s working directory was at that tag, and systemd reported it as active and running. Those are release and service-state receipts. [v2.16.0 release](https://github.com/MCMike0399/ChopperBot/releases/tag/v2.16.0) · [CI run](https://github.com/MCMike0399/ChopperBot/actions/runs/44650217459) |
| Member turn and document behavior | The delivery driver seeds files and invokes the helper directly. A real member turn adds prompt behavior, tool use and the generation path. The completed T3 thread left the member-facing prompt behavior open. Formula recalculation, text explanations and the absence of duplicate variants each need observations that exercise the corresponding behavior. |

The first repo footprint could be a short verification section in the existing Workshop guide. Point to `pnpm exec vitest run src/capabilities/workshop/__tests__/deliver.test.ts` for the local delivery contract and `pnpm exec tsx scripts/e2e-workshop-delivery.ts` for the live driver. The live driver requires authorization to create, post in, and delete a temporary private Discord channel. Its overall success can cover Discord alone when MinIO is absent, so read the separate MinIO receipt before making a storage claim. The script output and Workshop service logs are the starting points for diagnosing a failed check. This example is a walkthrough of documented and observed evidence. It did not run the delivery driver again or exercise a member turn.

### Startup-plan message

Both Pi tool traces opened the Feature playbook first. In the second thread, the user asked for an optional startup plan before the existing tool-action trace and requested testing before shipment. The local trace showed a focused plan test fail and later pass, plus broader Workshop and presenter checks. These results support the paths exercised by those tests.

The trace shows the push to `main` at 19:08 Mexico City time, the v2.17.0 release at 19:09, and the first live plan probe at 19:11. The probe failed on an invalid Discord permission flag. The corrected driver reported success at 19:12. A later commit changed the driver and version, and its CI published v2.17.1. GitHub’s tag and workflow records independently confirm the two published revisions. [v2.17.0 release](https://github.com/MCMike0399/ChopperBot/releases/tag/v2.17.0) · [Proof driver correction](https://github.com/MCMike0399/ChopperBot/commit/03469566e4b834ac7d2fe4d008df0dc1fd4a5338) · [v2.17.1 CI](https://github.com/MCMike0399/ChopperBot/actions/runs/44651986224)

The successful probe checks the real model’s plan output, Discord presentation, takeover by the action trace, and a late plan leaving that trace intact. It invokes the planner and presenter directly. The complete member-turn path through Workshop’s optional setting requires its own check. The probe failure belongs to the driver in the recorded trace. The release sequence shows why the first publishing action should be identified before the checks are chosen. A candidate-level drive belongs before that action when feasible and authorized. Checks that depend on the deployed environment need a distinct stage and verdict. [Tagged startup-plan driver](https://github.com/MCMike0399/ChopperBot/blob/03469566e4b834ac7d2fe4d008df0dc1fd4a5338/scripts/e2e-workshop-plan.ts)

## BStack checks

The first disposable Pi + DeepSeek Flash trials reached the repo recipe and reproduced the broken CLI retry. Both trials skipped the shared reference when its pointer lived only in Burbi Mode. A separate recipe authoring run chose Verification and skipped the references. After direct pointers were added to Feature and Verification, the final smoke runs opened the expected playbook first and reached the shared method. Verification read two rows where it expected one and preserved the fixture. Feature held the simulated publication after the required check failed.

In the final authoring run, Pi opened both references and edited the recipe and its project pointer. It exercised a single export through the real CLI and retained the expected one-line result after cleanup. A smoke trace also read an unrelated billing note. These exercises show routing and behavior on one fixture.

Claude Fable 5.2 at medium effort reviewed the operating paragraphs sentence by sentence in two sessions, then checked the four final edits covering rollout dependencies, probes that start below the entry point, evidence preservation before cleanup, and reuse of property-based checks. It reported no material issue in the final snapshot. The snapshot is the SHA-256 of the skill, Project verification, Verification recipes, Feature and Verification files in that order, joined with a null byte, `5e3c27d5ed6a7c436de2d0171a3dd003239bff0d9c8edf6682166424337340ef`. The Fable review was a reading exercise. Pi’s release exercise simulated the pre-publication gate, and the production stage guidance has not been exercised by BStack against a live rollout.

## Further evaluation

Start with one recipe in a disposable fixture derived from BStack’s current [export retry test](../tests/fixtures/exports/checks/replay_export.py), then try the same workflow with an authorized ChopperBot surface. Run fresh Pi + DeepSeek Flash sessions with the same task and snapshot, with and without the repo pointer. The first fixture has a known defect that the real CLI check exposes. On each run, inspect whether the agent opens the expected playbook and only the relevant recipe, actually reaches the real entry point, catches the expected failure, and reports the right environment and coverage. Include an unavailable-surface case to check that it reports the missing proof and preserves the fixture. A separate setup trial should show a fresh agent can follow the authored recipe cold and retrieve its evidence. Use those observations to decide whether Burbi Mode needs more prose or whether the project pointer is enough.

The BStack local suite passed six checks with its two opt-in suites skipped. A matched comparison across projects and the real Workshop member-turn check remain open.

## State and journey checks in Pi

On a disposable CLI fixture, the first draft reached the repo check and reproduced the duplicate row but missed the nested state-verification reference. The direct Verification playbook pointer was added for retries, timed actions, event order and recovery. On the revised text, Pi with DeepSeek V4.1 Flash opened Verification first, reached both references, produced the failing real CLI sequence and reported how to rerun it. Its workspace files matched the starting snapshot.

In a separate read-only synthetic review modeled on the UMO evidence issue, Pi opened Review first and used both references. It separated the observed deadline change from the open product rule and flagged the absence of evidence from the build with the later fix. It preserved the workspace files and identified the evidence as an account of a journey rather than a fresh capture. The two trials cover routing, CLI reproduction and evaluation of a supplied UI receipt.

A later Bug fix trial reproduced and corrected the seeded retry but skipped the references, and a repeated Review trial reached the right conclusions without opening them. Direct pointers were added to both playbooks. On the final text, three fresh Pi runs opened their selected playbooks and both references. Verification reproduced the duplicate. Bug fix recorded the failing check, changed only the assigned CLI file, and passed independent replay. Review rejected the unsupported build claim and preserved its files. One CLI narrative misstated the run year, so the result above relies on the tool trace and workspace checks.

Fable 5.2 at medium effort reviewed the prose and the final routing edits and reported no blocking issues. The final reviewed Markdown snapshot SHA-256 is `d15a89562f15f5c16785e9941cd81548b5a75f13edc4ffc5eac01f691348a495`. It covers the skill, Project verification, Verification recipes, Verification, Bug fix, Review and State and journey verification files in that order, joined by a null byte. The fixtures exercise CLI behavior and a synthetic evidence review. The UMO check concerns existing recordings and receipts.
