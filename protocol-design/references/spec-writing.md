# Writing the spec

A specification is read by experienced engineers who have implemented
protocols before. Increasingly it is also read by an LLM agent that gets the
spec and nothing else, such as "Read PROTOCOL.md, connect to wss://…,
authenticate with this token". Write for both: dense, plain, complete, and
standalone.

Run `scripts/spec_check.py` after every edit. It checks JSON examples and
links, finds stale terms, and counts claims.

## Contents

1. What the document is
2. Structure
3. Sentences
4. Rules
5. Examples
6. Tables, types, and appendices
7. Editing passes
8. The project style guide

---

## 1. What the document is

- **It stands alone.** Readers know other protocol specs. Leave out:
  - a table of contents;
  - a "how to read this document" guide;
  - key-word (BCP 14) boilerplate;
  - a legend for example arrows;
  - references to the schema, fixtures, tests, or implementations.
  Those belong in the README. The user deleted each of these by hand when
  they appeared: "assume people reading this protocol specification are
  intelligent and have read other protocol specifications before".
- **It describes the current protocol, not its history.** "Rooms are not
  announced" only makes sense to someone who knew the previous version. Say
  what is. Changes go in HISTORY.md.
- **It contains what interoperability needs and no more.** Encryption
  walkthroughs, HTTP status-code tables, and client rendering algorithms
  help while designing. They rarely belong in the spec. After exploring,
  ask: "what is the smallest text that lets two implementations
  interoperate?"

## 2. Structure

- **Order sections the way an implementer builds:**
  1. A short introduction: who the protocol is for, the trust model, the goal,
     and one complete happy-path session example.
  2. Transport and framing.
  3. Identifiers.
  4. The core, with a short conformance checklist for a minimal server and
     client.
  5. Optional capabilities.
  6. Informative appendices.
- **Keep implementation order; don't regroup by topic.** A regroup into
  "Data model / Sign-in / Messages / Presence…" was rejected because it
  breaks the build-up.
- **Build the reader's mental model incrementally.** At each point, the
  reader should be able to implement what they've read using only what came
  before. Placement test: "Does a minimal implementer need this here?"
  - Core sections don't list capability methods, records, or examples. A core
    method table lists core methods; the capability intro lists the rest.
  - A rule that belongs to one capability moves into that capability's
    section, even if it touches a core object.
  - One brief forward pointer ("passkey and email sign-in are capabilities,
    §4.10–4.11") is fine. Core examples that use them are not.
- **Order capabilities by how commonly they're implemented, and by teaching
  order.** Don't order them by when they were added. A capability that's
  close to something in the core (a `command` that looks like `message`)
  makes a good first one.
- **Open a section with an optional short paragraph of context and
  motivation, in prose.** The rules follow as bullets.
- **Group a long section under bold labels** (**Delivery.**, **Retention.**)
  rather than adding numbered subsections. Use real subsections only when a
  capability is big enough to have parts.

## 3. Sentences

- **Use Simplified Technical English (ASD-STE100), loosely:**
  - one rule per sentence;
  - active voice;
  - an explicit subject ("the server", "clients");
  - the same word for the same thing.
  Introductions may flow more freely.
- **Write in a developer's voice, not a formal one.**
  - Before: "frames from a JSON-RPC 2.0 sender are accepted as-is; frames
    emitted by this protocol are not JSON-RPC 2.0, since they omit that
    member."
  - After: "Since unknown keys are ignored, a JSON-RPC 2.0 client can talk to
    a server without changes, but it should not expect the `jsonrpc` key in
    what comes back."
  - Say "key", not "member".
- **Refer to actual keys in backticks, not prose names.** Write `log_id`, not
  "Log ID". Write `id`, not "request ID".
- **Prefer possessives where they read clearly** ("the user's connections").
  Avoid "the connections of the user". A style pass that turned possessives
  into "the X of the Y" made the text 10% longer.
- **Write short, whole sentences.**
  - Split a sentence that carries several ideas.
  - Avoid participle chains and tense shifts. "Holding the record at
    `prev_log_id`, a client diffs…; holding an older one, it knows…" was hard
    to parse.
  - Avoid vague endings such as "whatever its `log_id`". Name the actual
    case: "even if `log_id` did not change".
- **Remove qualifiers that don't change the rule.** "*Before
  authentication*, a `~private` notice reaches only its connection" lost its
  qualifier, because the statement is always true.
- **Fix fragmented sentences without turning the bullets into prose.**
  Colon-and-comma chains were "extremely fragmented". Collapsing them into a
  paragraph was also rejected: "No, let's have lists as point form."
- **Standard jargon is fine when defined on first use** ("tombstone").
- **A principle sentence carries no trailing edge cases.** "Servers ignore an
  id on it and send no reply, also when the params are invalid. Extensions
  follow the same rule." The trailing part was cut as confusing. If the edge
  case matters, give it its own plain sentence.
- **Capitalize requirement key words.** A lowercase "must" is not a rule;
  rewrite it or capitalize it. `spec_check.py --verbose` lists them.
- **Don't use "names" as a verb.** A field "refers to" what it points at and
  "defines" what it specifies.
- **Every term needs its counterpart.** "Level 0" without a Level 1 is a
  leftover. Use "core" for the section and "minimal server" for an
  implementation of only the core.
- **Name real standards.** Write "CommonMark", not "Markdown under the rules
  of §3.5", and permit known deviations explicitly.
- **Avoid soft or exploratory wording in normative text.** "We explore using
  WebSocket" became "WebSocket is the reference transport; others are
  possible". Don't claim support the spec doesn't yet have.
- **Advisory numbers are examples.** Prefer "such as a few minutes without
  input" to "about 30 seconds".

## 4. Rules

- **State rules, not their consequences.** Say what an implementation must
  do; implementers work out the effects. Don't add rationale sentences to
  stop a later editor removing something ("so no one optimizes it away").
  Those were declined every time.
- **Generalize rather than enumerate.** Before you add a rule, check whether
  a general one already covers it. Typical general rules:
  - unknown keys, names, and notifications are ignored;
  - unknown or hidden IDs give one error;
  - policy refusals;
  - server normalization of client values;
  - ordering;
  - the merge rule;
  - the extension prefix.
  Don't restate a general rule inside a section.
- **State each rule once.** A replay rule stated four times drifts four
  ways. Put it in one place and point to it. Conventions get one home too.
  All text prefixes (`@user`, `#room`, `~system`) live in one appendix
  section; other sections link to it.
- **Every sentence must earn its place.** "What's the `@` prefix line about?
  Why did we add it?" The line had stayed only to keep a link working, and it
  was deleted. A convention that needs an exception doesn't belong either.
- **Don't leave promises hanging,** such as "a later revision may add
  paging". Either define the escape hatch now (an optional `member_count`
  when a list is truncated) or drop the sentence.
- **Start at the weakest strength that still interoperates.** The rungs are
  a permission ("`log_id` is usable as a timestamp"), a one-line suggested
  convention, MAY, SHOULD, and MUST. Use MUST only when a peer that ignores
  the rule breaks another. Use SHOULD when a conformant implementation may
  legitimately decline: "Servers SHOULD use the requested `name` for the
  passkey label", because servers may refuse names in general. When you
  propose a MUST, offer the weaker rung too.
- **Narrow a rule's subject instead of adding exceptions.** "Deliveries go
  only to joined rooms" plus an exception for system notices became "regular
  messages go only to joined rooms". System notices then fall under their own
  section.
- **Reword a hard-to-check requirement to the intent; don't weaken it.** "In
  the same room" can't be checked by a client. It became "MUST show the ID
  when the client knows another `user_id` with the same name", which a client
  can check locally, and it stayed a MUST.
- **Don't restate what the transport or base protocol already allows.**
  "On WebSocket, servers MAY also use protocol ping frames" was cut.
- **Specify a variant by how it differs.** "`command` takes the same params
  as `message`; it differs in…" Don't restate everything.
- **Mark conventions as conventions.** Put a one-line "Suggested convention:
  …" bullet next to the rule it relates to. Longer conventions go in an
  informative appendix that says it "needs no protocol support".
- **Keep "server policy" notes brief, and only where they point somewhere
  useful.**
- **Don't add cross-references for every interaction between rules.** One
  proposed cross-reference was rejected with "Excessive, skip."
- **Keep compatibility caveats that are true and useful** ("a strict JSON-RPC
  2.0 client may reject replies"). Write no compatibility notes for consumers
  that don't exist.

## 5. Examples

- **The opening example is a complete, happy-path session.** It shows no
  errors. It assumes the most common capability set and says so. Show the
  minimal case elsewhere.
- **Examples show the recommended practice, not the bare minimum.** Include
  optional fields you recommend, such as a display `name` in `from`. Leave
  out default values, such as `format: "plain"`.
- **Every example is a complete, correct frame that obeys every rule.**
  - A bare fragment shown as "the broadcast" was wrong; it belonged inside
    `method=message`.
  - When an ordering rule changes, reorder every example.
  - When a field becomes required, add it everywhere.
  - Requests and the notifications they cause must match. Joining room X
    can't produce an update for room `general`.
- **Write examples in causal order with explicit actors.**
  - Show a request, then its result, then the next request.
  - Comments say who acts ("server assigns the identity").
  - Put latitude in parentheses ("the server may choose something else").
  - Keep commentary out: "Server confirms message ID" implied a dependency
    that wasn't there.
- **Use core features in core examples.** Avoid frames with special
  constraints. A keepalive that must be byte-identical for an infrastructure
  fast path is a bad generic notification example.
- **Format JSON for reading:**
  - Short frames go on one line.
  - Complex frames go on grouped lines: envelope and `params` first, then
    IDs, then `from`, then `body`.
  - Use `...` for parts the example doesn't need.
  - Shorten long examples by showing only what's new and pointing to the full
    sequence.
- **Example values must not suggest a bad implementation.** Counter IDs
  invite counter URLs.
- **Developers implement from the examples first,** so a missing record in
  an example becomes a missing record in an implementation. Where a
  validator checks the examples, use `...` sparingly, because it can't check
  what's left out.

## 6. Tables, types, and appendices

- **Type blocks:**
  - Open the section that introduces an object with a TypeScript-like
    `class` block. Readability matters more than compiling.
  - Use one flat class per object, with nested shapes inlined.
  - Write defaults inline (`text?: string = ""`).
  - Type opaque blobs as `object`.
  - Leave a blank line between required core fields and optional ones.
  - Keep types complete. Group capability fields at the end under separator
    comments (`// "edit" capability`), as "a taste of what's to come". Don't
    add per-line `@since` tags, don't strip capability fields, and leave out
    only experimental ones.
- **A table may repeat information in a different form; a list may not.** A
  table that shows the same facts from another angle stays. A prose list
  that repeats a type block goes.
- **Table labels must be unambiguous.**
  - An "editable" column misled readers. It became "set by: `server` /
    `client` / `delivery`", with a one-line legend.
  - Drop a legend if the table is clear without it.
  - Don't repeat the key column in the description column.
- **Checklists are numbered lists** that cite their sections. Diagrams and
  arrow chains don't separate packed rules.
- **Appendices are informative and hold no MUST rules.** If a rule drifted
  into an appendix, move it back into the body. Useful appendices:
  - **Conventions:** reserved IDs, field naming, text prefixes.
  - **Valid scenarios:** exchanges that are valid under the spec but easy to
    get wrong, collected so implementations accept them. Each is a short
    point-form entry with a small example and links to the rules it follows
    from. Examples: a notice before sign-in; a bot that connects, posts once,
    and leaves; an invite token that signs up several people. Scenarios add
    no rules. If writing one exposes a rule that forbids it, fix the
    normative text in the same change.
  - **Under consideration:** designs that aren't part of the protocol yet,
    kept so implementations can experiment and converge.

## 7. Editing passes

- **A change replaces wording rather than adding to it.** It leaves out what
  another rule implies and what is up to the implementation. Prefer less
  text, but not at the cost of clarity.
- **Measure edits by claims, not lines.** Use `spec_check.py --against <rev>`
  to compare sentences, words, and each key word. Name every MUST or MAY that
  an edit added, removed, strengthened, or weakened, and ask the user to
  confirm. A lowercase "may" that became a formal MAY is a change in meaning.
- **After a style pass, run a consolidation pass.** Splitting sentences
  inflates text. Then look for many per-section rules that one higher-level
  rule could replace, and delete the repeats.
- **Draft a new or rewritten section in chat first.** "Show me what the
  section looks like, then once we're happy with it we can update everything
  else." Then list the ripple edits it needs before making them.
- **Run the final review in categories:**
  - contradictions (rule against rule, example against rule);
  - gaps;
  - excessive or out of date;
  - mechanical (broken sentences, stale names, table alignment).
  Apply the clear-cut fixes. Bring the rest as numbered decisions, each with
  a default.
- **Sweep for stale names and stale concepts after each redesign.**
  - grep for old field names and anchors with `spec_check.py --forbid`;
  - "either kind" phrasing left over from when there were two kinds;
  - sentinel values that no longer occur ("`"0"` is reserved for the empty
    log": when does that happen?);
  - lists that must name their members once a new member arrives.
- **Ask the reader's questions yourself.** "What does 'editable' mean
  here?" "When does this case happen?" "We never mention Level 1." The user
  found each of these by hand. Find them first.
- **Review the user's direct edits** for lost normative text and for
  contradictions with other sections. Report them. Don't restore normative
  text without asking; the removal may have been deliberate.

- **Run a whole-document style pass with parallel agents and hard
  constraints.**
  - Split the spec into ranges.
  - Each agent returns a list of `{old, new, why}` edits, with each `old`
    byte-exact and unique, and writes only to its own output file.
  - The coordinator reviews the edits and applies them.
  - Constraints: no meaning change; MUST, SHOULD, and MAY keep their force; no
    field, section, or link changes; code blocks and headings untouched; be
    selective (10–25 edits per range).
  - Afterwards, verify that every key word count is unchanged or explained,
    that every link resolves, and that every code block is byte-identical.
  - Reject edits that undo deliberate wording.

## 8. The project style guide

Keep a short style guide for the spec in the repo, such as `AGENTS.md` or
`CLAUDE.md`, so every session writes the same way. Start from
`assets/AGENTS-template.md`.

When the user corrects style more than once, summarize the pattern ("what
writing style changes am I asking for?"). Offer to add it to the guide. Then
run a style pass over the whole spec. Apron's guide came about this way, in
one afternoon, from a run of corrections. Keep the guide's own rules in point
form, and generalize them too.
