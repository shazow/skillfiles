# Change management

This covers keeping a spec, its machine-readable companions, and several
implementations in step across versions. The spec is the source of truth.
Everything else follows it, in a deliberate order.

## Contents

1. Spec first, then propagate
2. The artifacts and what each holds
3. Versions and HISTORY.md
4. Renumbering and links
5. Rolling a version out to implementations
6. After the rollout

---

## 1. Spec first, then propagate

- **Iterate on the spec alone.** When a session is about the spec, edit only
  the spec unless the user approves more. Twice, Claude started editing
  servers and clients right after a spec decision. Both times the user
  stopped it: "WE'RE ONLY EDITING PROTOCOL.md in this session." Decisions
  change several times before they settle. Implementation work done in
  between is wasted, and it hides the size of the spec change.
- **Keep a propagation queue.** As the spec changes, list what will need to
  follow:
  - the schema;
  - fixtures and their README;
  - HISTORY.md;
  - the style guide;
  - other docs that link to moved sections;
  - each implementation.
  Show the queue in your status, and do it in one pass at the end, when the
  user says so.
- **Flag what the scope leaves broken; don't fix it.** For example, a README
  anchor broken by a renumber. Mention it and leave it for the propagation
  pass.
- **In an implementation session, leave the spec to a spec session.** When
  the work runs into the spec, don't edit the spec there. Revert a spec edit
  the user doesn't like, and write a short problem brief instead: what
  happens, the measured numbers, and which flows hit it. When the user links
  the new spec, check the session's work against it.
- **Sort implementation-led suggestions before the user approves them:**
  allowed by the spec today, needs a spec change, or an implementation
  detail that stays off the wire.
- **If CI gates every push** and a spec change makes the schema or fixtures
  fail, ask in the same decision for permission to update them. Don't revert
  the spec example to keep CI green.

## 2. The artifacts and what each holds

| artifact | holds | rule |
|---|---|---|
| Spec (`PROTOCOL.md`) | the protocol, standalone | the source of truth |
| History (`HISTORY.md`) | wire changes per version | brief; only wire changes |
| Schema (`*.schema.json`) | frame shapes | in step with the spec; tighten where the spec is stricter |
| Validator | rules the schema can't express | run after every change to the spec or schema |
| Fixtures | portable behaviour scenarios | written from the spec, never from an implementation |
| Style guide (`AGENTS.md`) | how to write and change the spec | add each rule the user states |
| README | how to use the repo, schema, and fixtures | the spec never refers to these |

- **Keep the schema and the spec in step.** Validate the spec's own examples
  against the schema as well as the fixtures.
- **Run the checks after every change:** the validator, and
  `scripts/spec_check.py` for JSON blocks, links, and claim counts.

## 3. Versions and HISTORY.md

- **Every change to the wire goes in HISTORY.md under the current version.**
  Editorial changes don't, unless they renumber sections. Say "nothing on
  the wire changed, so HISTORY needs no entry" whenever that applies.
- **Head each version with its date** (`## v7 (2026-09-29)`), latest first.
  To write HISTORY.md for a spec that has none, walk `git log --follow` on the
  spec and `git show` each commit that changed the version. Keep only the
  changes with big implications.
- **Keep entries brief.** About ten short bullets per version, in the same
  style as earlier versions. The details live in the spec. A 13-bullet entry
  was sent back to be cut down.
- **Each bullet says what is now true,** naming keys and methods: "`room_list`
  takes `filter` (`joined` / `not_joined` / `all`)". Mention a replacement by
  its old name ("replaces `intro_message`").
- **After a renumber, older entries keep their old section numbers.** Add a
  note with a permalink to the spec at the last version that used them.
- **Version policy** before and after launch is in design-principles §11.
- **Keep the version in sync everywhere:** the opening example, the
  handshake section, fixtures, test frames, implementation version strings
  (`server/6`), and READMEs that claim "speaks protocol N".

## 4. Renumbering and links

- **Renumber with a script.** Use sentinel placeholders, so that §3→§4 and
  §4→§5 don't replace each other twice. A sentinel once turned `@@server`
  into `§server`, so check the result.
- **Verify every link in the repo.** Check `PROTOCOL.md#anchor` links in all
  files, including JSON fixtures' `references` arrays, which no test reads.
  `spec_check.py --links-in FILE` checks a Markdown file. Grep the rest.
- **Diff with cross-references ignored** to confirm that only the intended
  moves happened.
- **Transform fixtures by parsing the JSON, not with regexes.** Afterwards,
  check that every expectation still receives the messages it expects.
- **Keep reflows (line wrapping) in separate commits.**
- **Revert unrelated diffs** that tooling produces, such as a sort that
  reordered fixtures, so the change stays focused.

## 5. Rolling a version out to implementations

- **Run the baseline first.** Run every suite before changing anything, so
  that new failures are attributable.
- **Write a shared contract file** for implementation agents. It contains:
  - "The spec is the source of truth. Where this contract and the spec
    disagree, the spec wins; report the conflict."
  - The wire changes, as a diff summary (`git diff <old>..<new> --
    PROTOCOL.md`).
  - Fixed decisions: choices already made for things the spec leaves open.
  - In scope: renames, removals, changed semantics. Out of scope: new
    features not yet requested.
  - "No backward compatibility: delete old-version code and tests; don't
    keep shims." (when there are no outside consumers)
  - "Change only what the spec change forces." Otherwise one agent rewrites
    reconnect logic that the new version didn't touch.
  - "End with: choices you made where the spec is silent; comments whose
    described behaviour no longer matches the spec (list, don't rewrite)."
- **Brief details that paid off:**
  - Each agent keeps a notes file with **Decisions / Concerns / Spec
    feedback**, appended as it goes. Spec feedback quotes §x.y and proposes
    wording.
  - Agents read the full spec sections, not just the diff. One retrospective
    traced misreadings to agents that read the 1,000-line diff once and never
    opened the spec.
  - When the spec changes mid-migration, append an "Update N" section to the
    brief with the new diff and a delta list. *Resume* the same agents so
    they keep their context; don't respawn them.
  - When the user says "pause", stop every agent and check nothing is
    half-written. Then list the spec issues you noticed, so the user can
    settle them in the same change.
- **Fan out one agent per component.** Each one works only in its own
  directory and doesn't commit. The coordinator commits per component after
  that component's tests pass, and never commits half-finished agent work.
  Relay one agent's resolved ambiguities to the others while they run.
- **Fixtures first, then implementations.** An agent writes fixtures from the
  spec alone, so they are a fixed target for everyone else.
- **Use a clean-context reviewer per repo before each PR.**
  - Priority order: security, then conformance (MUST/SHOULD, error codes,
    who receives what), then correctness and stored-data migration, then
    leftovers from the old version, then test gaps.
  - "Actually run the checks."
  - "Verify each finding; don't report speculative issues as confirmed."
  - Don't flag the deliberate choices listed in the brief.
  - Output a numbered list (severity / file:line / problem / failure
    scenario / fix) plus a **spec ambiguities** section.
  - Then **re-review**: "for each numbered finding, verify it is actually
    fixed. Read the code; don't trust commit messages."
  - Then a narrow **convergence pass**: "only verified blockers and should-fix
    issues; skip style nits." A broad review once, then narrow ones,
    converges.
  - Match the review to the change. A mechanical rename gets a diff check,
    not a reviewer agent.
- **The coordinator verifies independently before opening PRs.** Re-run the
  checks yourself rather than trusting an agent's report. Say what wasn't
  independently reviewed, and report your own slips (for example a `| tail`
  that hid a failing exit code).
- **Final summary to the user:**
  - a PR table with state and review rounds;
  - merge order, with reasons;
  - concerns: blockers found, one-way upgrades, deliberate deviations from
    the spec;
  - spec feedback in priority order;
  - one process lesson.
- **Use stacked PRs in dependency order:** spec → reference server and client
  → constrained server → extras. When cross-implementation CI fails exactly
  at the step a later PR fixes, document it on the PR.
- **Pin test peers.** Implementations include the spec repo and each other
  as submodules for wire and interop tests, so CI tests against chosen
  versions rather than whatever `main` is.
- **Order deploys to avoid data loss.** If the client stops sending something
  the server used to rely on, the server must handle the new behaviour first.
  Write the order down.
- **Stored data is part of a protocol change.** Stateful servers need to
  upgrade stored data when the protocol changes, such as converting old
  descriptions or renaming reserved IDs. Test the upgrade two ways: inject a
  failure partway through and check that it rolls back; and build a real
  old-version store with the old code, then upgrade it. Call out upgrades
  that are one-way ("roll forward only").
- **Renames before release:** servers send only the new names. Clients may
  keep a tiny, commented fallback for the previous version, gated on its
  version number.
- **Implementations ship risky new paths behind a flag that is off by
  default.** New sign-in schemes are an example.
- **Data migrations:** while there are no real users, reset stored data when
  the version changes instead of migrating it. One migration replaced this
  way cut about 250 lines. When you ask the user about one, spell out what
  would be lost, such as demo accounts or counters. A bare multiple-choice
  question got an answer the user reversed once they saw the stakes.

## 6. After the rollout

- **Deep clean:** delete code, tests, docs, aliases, and "tests that removed
  features stay removed" from earlier versions. Keep only data migrations a
  pending deploy still needs, and list each one with the condition for
  removing it.
- **Cross-validation:** two independent agents.
  - One runs pins, tests, and interop. It fixes only pins and outdated
    expectations, and reports real bugs instead of patching them.
  - One is a read-only consistency reviewer. It checks each new rule against
    every implementation with file:line evidence, and re-checks the riskiest
    deletions.
- **Compliance or leftovers audit:** run one read-only agent per component.
  Each sorts its findings into:
  - already correct;
  - fix;
  - optional;
  - a decision for the user.
  Don't assume "everything is updated". In one audit, two minimal servers
  turned out to be two versions behind.
- **Describe the current state in docs,** not the change from the last
  version.
- **Do a size review:** where did the code grow, and why?
- **Feed spec notes back.** Collect the implementers' "spec is silent here"
  lists. Fix the small ones in the spec. Queue the design questions for the
  next spec session.
- **PR descriptions summarize every protocol change,** grouped by area,
  with a "not done yet" list. Update the title and description as the scope
  grows.
- **File follow-ups in other repos as issues** with file:line references.
- **Parallel agents never share scratch files.** Give each agent its own
  output path. Only the coordinator writes shared files such as the spec.
  Once, two style-pass agents shared `out.json`, and one applied the other's
  edits.
