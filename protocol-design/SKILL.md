---
name: protocol-design
description: Design, specify, and iterate on software protocols, and write or edit their specifications. Covers wire and network protocols, JSON-RPC or WebSocket APIs, client-server and peer-to-peer sync, event and log formats, extension and capability systems, and spec documents like PROTOCOL.md, SPEC.md or RFC-style drafts. Use this skill whenever the user brainstorms a new protocol or a protocol feature, or adds or changes a method, field, message type, or capability. Also use it to review, simplify, or tighten a spec's wording, to compare against prior art (IRC, XMPP, Matrix, JSON-RPC, LSP, MCP, HTTP), and to plan a version bump or migration across several implementations. It also covers writing conformance fixtures or schemas and auditing implementations against a spec, even when the user doesn't say "protocol design".
---

# Protocol design

A protocol is a contract between implementations you don't control. Every
rule costs every implementer, in every language, for the life of the
protocol. So the work is to:

- keep the core as small as possible;
- make everything else optional and safe to ignore;
- state each rule once, as generally as it can be stated;
- test every idea against concrete payloads and real implementations before
  it becomes text.

This skill was distilled from many long sessions designing a real protocol
with its author. Most of it records what the author corrected, so follow the
working loop closely. It matters as much as the design advice.

## Two principles above all

Every other rule in this skill serves these two. When they conflict with
something else, they win.

1. **Make the default construction right, and the footguns negligible.**
   Change the design so that the careless version is correct.
   This matters most. Implementers build from the first example and the
   first rule they read, then stop. So the obvious implementation, written
   in a hurry from the examples, must be correct, interoperable, and safe.
   Wherever the obvious implementation is wrong, the protocol has a footgun.
   Remove it by changing the construction: the shape, the default, or who
   owns the value. Don't add a warning, a MUST, or a paragraph about the
   trap. Principle 1 beats minimalism: a smaller spec that a hurried
   implementer gets wrong is not simpler. Keep the construction that makes
   the careless version correct, even when it costs a field or a method.
   Test: write the naive client and server from the examples alone. Every
   bug they have is a design bug. `references/design-principles.md` §1
   lists common footguns and their fixes.
2. **Use the protocol to set creative constraints, and leave specific things
   undefined on purpose.** This matters next. A few firm constraints (a tiny
   core, one object shape, one merge rule) push designs toward reuse and keep
   implementations small. Deliberate openings (policy, granularity, UI,
   storage, timing, naming) leave room for implementations to differ
   creatively: a bridge, a bot, and a 100-line script all fit. Choose each
   opening on purpose, and bound it with the rules around it. Test: can two
   implementations that choose differently still interoperate? If yes, leave
   it open; name the opening in one line only where an implementer would
   otherwise expect a rule. If no, it is a gap, not an opening, so define it.

## Reference files

Read the ones that match the task. For a design brainstorm, read
design-principles and iteration-techniques before you propose anything.

| file | read when |
|---|---|
| `references/design-principles.md` | weighing any design choice: core vs capability, IDs and ordering, shapes and names, merging, errors, policy, cost, security, versioning |
| `references/spec-writing.md` | writing or editing spec text: structure, sentences, rules, examples, appendices, editing passes |
| `references/iteration-techniques.md` | testing a design: prior art, payload walkthroughs, lenses, adversarial cases, prototypes, reviews, fixtures, removal passes |
| `references/change-management.md` | changes that touch history, schema, fixtures, renumbering, or rolling a version out to implementations |
| `assets/PROTOCOL-skeleton.md` | starting a new spec |
| `assets/AGENTS-template.md` | starting a project's spec style guide |

Run `python3 <this skill's directory>/scripts/spec_check.py SPEC.md
[--against REV] [--forbid TERM] [--links-in FILE]` after every spec edit. It checks that JSON and JSONC
examples parse, that section links resolve, and that stale terms are gone.
It also counts sentences, words, and key words (MUST, SHOULD, MAY), so an
edit is measured in claims, not lines.

## The working loop

These habits came from repeated corrections. Each one prevents a specific
failure.

1. **Set the scope first.** Ask, or infer from the request, whether this
   session edits only the spec or also implementations. The default is the
   spec only.
   - Keep a queue of what will need to follow (schema, fixtures, history,
     docs, implementations) and do it at the end.
   - Decisions change several times before they settle, so implementation
     work done in between is wasted.
   - In an implementation session, the spec is out of scope. Hand spec
     questions over as a problem brief (`references/change-management.md`).
2. **Read before you propose.** Restate the user-visible experience the user
   wants. Read the whole spec, and the implementation code a question
   touches. Often the existing rules already deliver the experience.
   - Check each proposal against the existing text. Proposals that
     contradicted a rule the user had just read cost trust.
   - Grep the implementations for real producers and consumers before you
     call something unused or missing.
3. **Make every proposal addressable.** Number or letter the top-level items
   (1, 2, 3 or A, B, C). Don't number every paragraph.
   - The user replies by label ("2b. Nah…", "3. Ok").
   - Keep a running list of open decisions and end-of-session follow-ups,
     and repeat it after each round. "Skip" or "nevermind" closes an item;
     drop it from the list. "For now" or "later" moves it to the follow-ups,
     with the condition that would reopen it.
   - Order open decisions by dependency. Settle the one the others hang on,
     and park the rest; until then, the current design stands. Merge two
     items that turn out to be one question under one label. Commit what is
     settled while one item stays open.
   - Separate items that "change no rules" (a safe batch) from items that
     "change a rule" (they need a decision).
4. **Write each proposal in one shape.** Use the same parts every time:
   - the problem, in one sentence;
   - a concrete failure, shown as a short payload or timeline;
   - an options table whose columns are the criteria that matter (server
     cost, client cost, minimal implementations, degradation, and *what
     happens on a peer that doesn't support it*);
   - "I'd pick X", with the reason and its downsides;
   - what the option removes, and what stays possible.
   The user tests every proposal by asking for its costs, so state them
   first. Give real options, not only your pick; the user often chooses
   another.
5. **Show; don't describe.** Give before/after JSON on one fixed scenario.
   Lay out all the payload shapes of a method side by side. Explain a coined
   term with a two-frame exchange. "Show me the payloads" was the most common
   request.
6. **Write only what the user agreed to.** Never put an option, a name, a
   capability, or a rule the user didn't explicitly pick into the spec.
   - Silence on an item, or a reply about a different item, is not
     agreement. Leave the item out and remind the user it's open.
   - Placeholder names are not decisions.
   - A narrow request approves only the narrow change. For a bug report,
     apply the smallest fix, and offer any redesign it suggests as a
     proposal.
   - This was the worst correction in the whole history: "When did we add
     `members: true`? I didn't agree to that."
7. **Disagree with evidence, and concede plainly.**
   - If you think the user's idea is worse, say so with a concrete scenario.
     When asked "show me your pushback", give it. Don't swallow it.
   - If the user's idea is better, say so ("that beats my option A") and
     adopt it.
   - The user often reframes a fiddly rule into a simpler, more general one.
     Look for that reframing yourself first.
8. **When asked for the "minimal" or "smallest" change, give exactly
   that.** Drop the side proposals.
   - For wording fixes, offer two to four phrasings, smallest first, each
     editing an existing line.
   - After you minimize, list what the shorter text no longer says, so the
     user accepts the gaps knowingly.
9. **Report what changed, especially removals.** After applying edits, say:
   - what changed;
   - what was **removed or replaced** (a silent removal once went unnoticed
     until the user asked "did we actually drop `members`??");
   - every judgment call, under a heading like "Choices to check";
   - any MUST, SHOULD, or MAY that was added, strengthened, or weakened
     (from `spec_check.py --against`).
10. **Ask "what is this for?" before removing, and "is it used for anything
    real today?" before keeping.** Removal proposals that didn't know the
    feature's purpose got "Why is this a problem?" Features with no real
    user got cut.
11. **Simplify and generalize without being asked.** Before you call a pass
    finished, ask yourself "nothing left to consolidate or simplify?". After
    you settle one item, ask "what else is like this?" and apply the
    decision to its siblings: other methods, commands, and flows with the
    same shape. When the user's style corrections repeat, summarize the
    pattern and offer to add it to the project's style guide.

For approval, a clear "go", "ok", "yes", or "good enough as it is" means
apply it. Don't commit and then offer to revert. An approval with a
condition ("if it's already clear, drop it") is yours to check: check it
against the text, apply the branch that holds, and say which. When the user
is only musing ("should we…?"), answer briefly. Don't plan the whole thing.
"Pitch me" or "convince me" asks for the strongest case for one side, with
its costs. Apply nothing until the user decides.

## Design in brief

Details and examples are in `references/design-principles.md`.

- **Start from the trust model and the smallest implementation you care
  about.** Who are the parties? What would a 100-line implementation, a
  send-only bot, or a metered serverless deployment need?
- **The protocol makes use cases possible; it doesn't list them.** Specify
  what clients need to interoperate; servers do the rest. Reuse an existing
  primitive before adding one. When fixes pile up for one feature, look for
  the primitive it reimplements.
- **Keep the core minimal; everything else is a capability with a stated
  fallback.** Minimal never means a careless implementation can lose or
  fork data (principle 1). Degrade; don't negotiate. Unknown keys and
  notifications are ignored. Unknown requests get a defined error. Optional
  server behaviour is "MAY ignore", not a new flag or MUST-reject.
- **Remove a mechanism rather than replace it with a guarantee.** Look for an
  existing ID that makes the guarantee unnecessary.
- **Fix a wrong general rule before you add a mechanism.**
- **Use one shape per object at different completeness levels.** Objects are
  self-describing. Snapshots and deltas are separate methods. Each field has
  one job; never overload one by convention. Use explicit markers rather
  than inferring meaning from absence.
- **Use one merge rule, one level deep, everywhere.** Present replaces, empty
  clears, absent stays. Design for statically typed decoders: no required
  round-tripping of unknown keys, one opaque extension container, and a
  reserved `ext:` prefix for every extension name.
- **Separate position from identity.** The greatest version per key wins,
  from any source. The log is append-only, and its invariants are sacred.
- **A request is a method whose sender needs the reply.** Results stand
  alone. There are a few general error codes, and hidden and unknown give
  the same answer.
- **Policy belongs to implementations.** The spec defines the interop
  surface and settles conflicts between its own rules.
- **Place state by owner, audience, and lifetime.** Before choosing fields
  for presence-like or settings-like state, sort each value: per connection,
  per user, per scope, or derived for others. A private setting never rides
  on a shared record.
- **Weigh what each rule costs the cheapest server.** Keep responses
  bounded. Measure; don't estimate.
- **Be secure by construction.** Fix a request's effect when it is made, not
  when a token is presented. Fields that are unsafe to ignore fail closed.
  Write an attack out as real frames before you trust a fix.
- **While you are the only consumer, break freely.** Write no compatibility
  shims or notes, and fold changes into the unreleased version.

## Writing in brief

Details are in `references/spec-writing.md`.

- **The spec stands alone.** Leave out the table of contents, reading guide,
  key-word boilerplate, and references to the schema or implementations.
  Describe the current protocol, not its history.
- **Order it the way an implementer builds:** introduction with a happy-path
  session, transport, identifiers, core with a checklist, capabilities
  (ordered by how common they are), then informative appendices. Nothing is
  referenced before the reader needs it.
- **Use plain, simplified technical English.** One rule per sentence, active
  voice, an explicit subject, and keys in backticks. Write in a developer's
  voice, with capitalized key words.
- **State rules, not consequences or rationale.** Generalize rather than
  enumerate. State each rule once. Narrow a rule's subject rather than adding
  exceptions.
- **Examples are complete, valid frames.** They follow every rule, in causal
  order, and show recommended practice.
- **Edits replace text rather than add to it.** After a style pass, run a
  consolidation pass.

## Testing a design in brief

Details are in `references/iteration-techniques.md`. Match the technique to
the moment:

| moment | techniques |
|---|---|
| any new feature | prior-art survey (look for failure stories); one fixed scenario rendered for each option; all payload shapes side by side |
| choosing between options | the lenses (append-only log, peer-to-peer, dumb server, minimal reader, typed decoder, cheapest deployment, next roadmap feature); a "peer doesn't support it" column; question each constraint behind "what we lose" |
| before writing a rule | invariant check (including the general rules you lean on); held state that needs an end both sides can observe (leases, grace periods, lost messages); adversarial timeline (retries, reordering, concurrency, identity change, privacy); persona tests (send-only bot, huge old room, mobile lifecycle) |
| before handing over a new design | hurried-implementer pass: write the naive client and server from the spec alone, run the standard scenarios against them, and redesign every footgun |
| before cutting a version | parallel read-only reviews: implementer read, consistency and leftovers, one per consumer; final review in categories |
| after implementing | friction mining (invented rules, divergences, workarounds); a retrospective over the agents' traces; spec notes, filtered through "what do clients need?"; differential tests; size accounting; features built as probes |
| ongoing | fixtures written from the spec, mutation-tested; a validator for what the schema can't say; a black-box conformance probe; interop CI with pinned peers |

## Starting a new protocol

1. Write the goal, the audience, the trust model, and the implementations you
   expect (smallest, most constrained, future topology). Confirm them with the
   user.
2. Survey prior art for the domain, looking for failure stories. Present it
   as a table with borrow or reject, and why.
3. Sketch the core: framing, identifiers, and the fewest methods needed for a
   working minimal implementation. Write the happy-path session example
   first. It forces the shapes to be concrete.
4. List the candidate capabilities, each with what it adds and its fallback.
   Push anything you can out of the core.
5. Start the files from `assets/PROTOCOL-skeleton.md` and
   `assets/AGENTS-template.md`, plus an empty `HISTORY.md`.
6. Before you hand the design over, run the hurried-implementer pass
   (`references/iteration-techniques.md` §4). Fix each footgun it finds by
   changing the construction, then run it again. Report the scenarios you
   ran and what each found.
7. As soon as shapes settle, add a JSON Schema, a validator, and a few
   fixtures. Prototype the smallest client and server early, and also one
   constrained deployment if the protocol will have one.
8. Iterate with the working loop above.

## Failure modes to watch for

Each of these happened, and the user had to catch it:

- Writing unagreed options or placeholder names into the spec.
- Editing implementations during a spec-only session.
- Replacing a removed mechanism with a new MUST.
- Proposing a new field, method, capability, or flag when an existing
  mechanism, a base-protocol feature, or a fixed general rule would do.
- Over-specifying: transport mechanics, crypto walkthroughs, edge cases that
  do no harm, "for symmetry" extensions, fields for undesigned features,
  server MAYs for internal policy, speculative future-proofing ("what every
  future scheme must define").
- Giving an existing field a second meaning by convention, or making an
  identity field optional for a special case.
- Semantics that depend on state, where a request means something different
  depending on the connection that presents it.
- Dropping a unifying design at the first objection, instead of pushing
  primitive reuse further.
- Accepting every implementer or reviewer suggestion. Filter each through
  "what do clients need to interoperate?".
- Rules that make servers keep state with no user value. Source-dependent
  precedence rules where a field-level merge works.
- Compatibility reflexes (aliases, shims, notes, "send both for a while")
  when there are no outside consumers.
- Treating constraints as fixed costs in tradeoff analysis.
- Formal, repetitive, or robotic wording. Trailing edge-case clauses.
  Defensive rationale sentences.
- Leaving orphaned terms, stale names, sentinel values, or examples that no
  longer obey the rules after a redesign.
- Restructuring more than asked: a topical regroup, or overshooting "move it
  a bit down".
- Long replies with every paragraph numbered, or a seven-item pre-merge
  question list. Keep decisions few, labelled, and say which ones block.
- Asserting claims ("unused", "nearly free", "tenfold") without checking
  them against the text, the code, or a measurement.
