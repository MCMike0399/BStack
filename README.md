# Burbi-mode, first review draft

Prepared from pinned pstack v0.15.43 for phrase-by-phrase review. Prepared for a GitHub review PR. No installation, CLAUDE.md edits, plugin registration, agent changes, or automation activation.

Start with `skills/burbi-mode/SKILL.md`. It copies the mode through Autonomy and stops before Subagents. Delegation references before that boundary are visibly deferred. Autonomy is a source quotation pending review.

`skills/` contains the mode and its non-deferred candidate dependencies. Nothing in this folder is installed. `upstream-reference/` contains exact source `.txt` snapshots, including deferred skills, for comparison only. `diffs/` records every staged skill change. `source-manifest.json` records paths, status, pinned commit, and source hashes. MIT notices are preserved in `licenses/`.

External references deslop, control-ui, and control-cli come from cursor-team-kit at the same commit. TypeScript companion examples are included. Deferred workflows are not claimed to have a complete runnable dependency closure. See `DEFERRED.md`.

No invocation is registered yet. After a separately approved installation, the slash command name will be burbi-mode, with a plugin prefix if packaged as a Claude Code plugin.

## Review order

1. [Burbi-mode draft](skills/burbi-mode/SKILL.md): start at Non-negotiables and review phrase by phrase.
2. [Mode changes from upstream](diffs/burbi-mode.diff): inspect renaming, cutoff, and deferred clauses.
3. [Deferred material](DEFERRED.md): subagents and dependent workflows remain paused.
4. [Pinned original mode](upstream-reference/pstack/skills/poteto-mode/SKILL.md.txt): comparison only, not adopted policy.
5. [Source provenance](source-manifest.json) and [MIT notices](licenses/).

Supporting skills are candidates for later review, not approved defaults. Autonomy remains an upstream quotation pending review.

## Verification

Run `python3 verify.py` from this repository. Static checks cover source hashes, relative links, skill counts, the pre-Subagents cutoff, and draft boundaries. Claude Code loading, installation, and runtime behavior have not been tested.
