# Iteration techniques

These are ways to find the weak points in a protocol design before
implementers do. They are grouped by when they pay off. Use the cheap ones
(payloads, lenses, adversarial walkthroughs) on every proposal. Use the
expensive ones (prototypes, fan-out reviews, conformance probes) at
milestones: before a version is cut, and after it is implemented.

## Contents

1. Prior-art research
2. Make it concrete: payloads and scenarios
3. Design lenses
4. Adversarial and edge-case hunting
5. Prototypes and reference implementations
6. Learning from implementations
7. Reviews of the spec itself
8. Conformance: fixtures, validators, probes
9. Removal and minimization passes

---

## 1. Prior-art research

Use this whenever a feature exists elsewhere, which is nearly always.

- **Research failure stories, not feature lists.** Ask "What mistakes did
  they make along the way? What did they later deprecate?" Matrix's
  unauthenticated media, its display-name mention matching, and its removed
  reply fallbacks taught more than its feature set did. So did XMPP's
  multi-user chat (MUC) to Mediated Information eXchange (MIX) migration,
  stalled for years.
- **Present a table:** system | how it does X | what went wrong | borrow or
  reject, and why. Follow it with "What this means for us": map each lesson
  to "we already avoid this", "applies, and here is a one- or two-line spec
  change", or "doesn't apply". Rank the proposals.
- **Borrow the shape of a standard before inventing one.** OpenGraph for
  link metadata, JSON-RPC for errors, CommonMark for text. The comparison
  can also change your mind: oEmbed was tried first and replaced by
  OpenGraph, because OpenGraph has no `html` injection risk, carries alt
  text, and nearly every page publishes it.
- **Check more than one family:** messaging (IRCv3, XMPP, Matrix), RPC
  (JSON-RPC, LSP, MCP), state sync (Kubernetes list+watch, JSON Merge
  Patch), web transport (WebSocket, Web Push, SSE), and auth (WebAuthn).
- **Use naming surveys.** For a contested name, tabulate what many protocols
  call the same thing. To name the handshake's version and software fields,
  one survey covered MCP, LSP, JSON-RPC, SSH, git, libp2p, HTTP, Matrix, XMPP,
  IMAP, BitTorrent, Redis, Postgres, and more. Breadth matters: the user's
  answer to a thin first survey was "look at some more protocols".
- **Say when you are working from memory** ("details may have drifted").
  Search when the details matter.
- **When documentation is blocked,** use library sources that quote the API
  text verbatim, and say that you did.
- **Prior art confirms as often as it changes things.** Saying "IRCv3 and
  XMPP both regretted negotiation, so we keep 'degrade, don't negotiate'" is
  a valid finding.

## 2. Make it concrete: payloads and scenarios

The most common request in every design session was "show me the payloads".

- **Start from the experience.** Restate the user-visible behaviour the user
  wants in a sentence or two. Then show how the current spec already
  delivers it, or exactly where it falls short.
- **Recover history before changing it.** "How did this work before?" Use
  `git log -S <term>`, `git show <rev>:SPEC.md`, and commit messages to
  rebuild the earlier design. Show its wire examples next to today's. State
  the premise that justified the change, and test whether it still holds.
  If it doesn't, revert rather than patch the symptom. A room summary had
  become a message "because we thought we wanted edit history on the
  summary, but I don't think we do", so it went back to a `description`
  field. History also found a removed field (`member_count`) that was the
  right fix again.
- **Use-case tables decide whether a field earns its place.** Columns are
  use | who needs it | does it need this field? Step tables show where an ID
  must exist: step | needs the ID? | why.
- **One fixed scenario, every variant.** Pick a short story that touches the
  feature. For example: Alice posts A, Bob replies B, B moves to a thread,
  Carol reacts, Alice edits. Render it as before/after JSON. When there are
  alternatives, render it three ways with the same story, then compare them on
  wire size, ordering, client dispatch, degradation, extension, and
  compaction. A log table (`log_id | transition`) at the top helps.
- **All payload shapes side by side.** For a method under suspicion, list
  every shape it can take (A–F) with a comment for each. Overloading becomes
  obvious when the same key means different things across the list.
- **A full exchange for each shape question:** request, result, broadcast,
  final state. Do this for any create or edit flow, uploads and streams,
  sign-in, and listing and updates.
- **Explain coined terms with a wire exchange.** "Auth is a barrier" became
  clear from a two-round-trip example, not from a definition.
- **Write pseudo-code for the minimal server** to answer "what keeps the
  server simplest?" For example: `slice = log[room].between(after,
  before).take(limit)` plus one ternary. This proves dumb replay is enough.
- **State tables for merge and replay rules:** "client holds X, receives Y,
  keeps Z", one row per case.
- **Size tables for options:** bytes for 1,000 rooms with 20 and with 100
  members, to put a number on "megabytes per response".

## 3. Design lenses

Ask each question of a proposal. Each lens has caught real design bugs.

- **Append-only log:** "Would this work if all state were an append-only
  log?" This found reactions lost on move, unlogged room state, and deletion
  that couldn't erase anything.
- **Future topology:** "Would this work peer-to-peer?" Use it as the
  tie-breaker between otherwise equal options.
- **Dumb server:** "Is a naive server that replays the log conformant?" If
  conformance needs the optimization, the optimization is in the wrong place.
- **Minimal implementer, reading in order:** read the spec section by section
  as someone building a minimal client and server. At each point ask "can I
  implement this with only what came before?" The output is a list of things
  "referenced too early".
- **Statically typed decoder:** "How does a Go struct or Rust serde type
  decode this?" This catches unknown-key round-tripping, `null` versus
  missing, and big integers.
- **Cheapest deployment:** "What does this cost a stateless or metered
  server per frame?"
- **Trust model:** "Does enforcing this fit who the users are?"
- **Next feature:** take an open issue or roadmap item and check whether the
  design handles it. "Let's look at another addition scenario to see if
  it'll help us reach a conclusive decision" turned an argument about array
  shapes into a count of record kinds.

## 4. Adversarial and edge-case hunting

Walk each through as a timeline with concrete IDs, not as prose.

- **Retries and deduplication:** a retried request whose broadcast is
  suppressed; a timed-out request that was applied anyway; a reply lost
  because the connection was replaced.
- **Reordering:** a result before its broadcast; typing start and stop
  reversed; two saves of the same object; a listing in flight while another
  device leaves the room, so the room comes back.
- **Concurrency:** two writers on one object under whole-object replace (a
  phone sets `tz` while a laptop sets `bio`); quick toggles; editing, then
  moving before the edit is confirmed; saving a deleted object.
- **Moves across scopes:** what stays behind in the source; what leaks about
  the destination.
- **Identity changes:** sign-in, a guest upgrading to an account, a repeat
  sign-in as the same user, notifications filed under the old identity.
- **Mixed versions:** an older client edits a newer object and strips fields
  it doesn't know.
- **Retention and truncation:** objects created before a discarded prefix;
  checkpoints below the new lower bound.
- **Reconnect windows:** a "keep for 60 s" rule that leaves a user online
  forever; a reconnect storm hitting rate limits.
- **Misuse and malformed input:** scalar frames (`"x"`, `1`, `null`); empty
  references (`{}`, `{"id": null}`); `limit: 0` or negative; a 1 MiB frame; a
  wrong protocol version string; unknown methods before auth; a notification
  sent with an `id`.
- **Scale and abuse:** one frame per user sharing a big room; status flips
  flooding rooms; unbounded extension growth; mention spam; caps with no
  limit.
- **Operational:** clock skew wiping registrations; per-message signing cost.
- **Privacy:** for each promise to hide something, list every
  server-originated frame that could reveal it.
- **Attacks as real exchanges.** "Walk me through the actual protocol
  payloads of the attack." Write the attacker's request, what the victim
  receives, what the victim's client does on its own, and what the attacker
  ends up with, as frames and links. Then build a matrix of design options
  against attacks (add-CSRF, login-CSRF, cross-device link, brute force,
  table exhaustion). Run a threat-model pass on every auth-related change
  *before* implementation starts. One tightening written mid-flight
  reopened an account takeover and cost a client three regressions.
- **Personas:**
  - a send-only bot that connects, posts, and disconnects (this removed
    auto-announcing rooms on sign-in);
  - a years-old public room with thousands of departed members;
  - a mobile app moving through foreground, background, suspended,
    woken by push, and resumed. Write that lifecycle as requirements R1–Rn
    with a "supported today?" column before choosing mechanisms.
- **Failure-mode column:** in every options table, add a column for "a peer
  that doesn't support it". This one column decided `command` as its own
  method rather than a flag.
- **Invariant check:** before writing a proposed one-liner, test it against
  the protocol's invariants: monotonic positions, inclusive bounds, the
  only-redaction-rewrites rule, and whether live delivery can reach state
  clients already hold. Also check it against the spec's general rules,
  especially any you cite as a safety argument. One pin design argued "pins
  are safe because server fields are read-only" while adding a request that
  changes that server field. Copy the encoding that existing fields use for
  the same thing: units, durations, "forever", clearing. Include "change
  nothing" as an option.
- **Two clocks:** for every timeout, ask which side decides it and whether
  the other side can know. A grace period only one side knows lets them
  disagree about whether a job is still alive. For each thing one side
  holds, ask what ends it if the message that would end it is lost. Once
  several timeouts are set, walk one user's scenario end to end with the
  real numbers ("at what point does an idle user become offline?"). Take
  the values from products users know, not from guesses.

## 5. Prototypes and reference implementations

- **Write the client code before specifying.** "What does a reasonable web
  client that renders a streaming terminal look like?" Writing it showed
  several problems:
  - `Content-Range` can't describe a growing file;
  - a simple CORS GET avoids preflight;
  - UTF-8 sequences split across reconnects;
  - an idle watchdog is needed.
  All of this led to a smaller protocol: reconnect means replace, with no
  offsets.
- **Build a comprehensive reference server, then a client against it.**
  Implementing everything exposed a stream-end deadlock, Host-header
  injection in URLs the server mints, and identity loss on disconnect.
- **Build a constrained deployment too,** such as a free-tier serverless
  worker with read and write budgets. It shows the cost of each rule and
  tests whether the MAY paths really work. One implementation should
  actually take every MAY.
- **Keep two tiny example servers.** About 150 lines each, checked by the
  same scratch client. They keep "the core fits in about a hundred lines"
  true.
- **Check that a specific implementation can comply with the text.** For
  example, "would the worker's auto-response mechanism still be compliant?"
  Answer with a table of spec requirement | mechanism | edge cases.
- **Verify by experiment rather than assert.** Write a fixture, a repro test,
  or an interop run instead of arguing. Check claims against the text and
  the code first. Overstated claims ("typing is nearly free", "tenfold
  savings", "nothing links back to the thread", "this field is unused") were
  each wrong and corrected later.

## 6. Learning from implementations

- **Mine implementation friction.** This is the strongest technique. After a
  version is implemented in several codebases, collect:
  - every rule an implementer had to invent ("decisions beyond the
    contract", "ambiguities I resolved", "choices where the spec is
    silent");
  - every point where two implementations diverged;
  - every workaround, such as polling, throttle exemptions, or cross-scope
    fallbacks.
  Each one is a spec gap or a design flaw. Report them as:
  - real design gaps;
  - places where the spec left choices and implementations split;
  - what worked well (keep it);
  - costs to note.
- **Ask implementers for spec notes.** Every implementation agent's brief
  ends with "list the choices you made where the spec is silent". Fold small
  ones into the spec. Bring design ones to the user, with the divergent
  behaviours side by side. Leave alone the ones with no wire-visible
  difference.
- **Use implementation features as probes.** Build a policy feature, such as
  read-only guests or bot invite tokens, under the constraint "no protocol
  change", and "raise any flags where the spec fights it". The flags become
  spec fixes, and the feature branch is rebased onto them.
- **Do differential testing.** Feed the same inputs to two implementations
  and tabulate where they disagree. Five Markdown inputs on which a renderer
  and a regex disagreed about mentions changed the design to an explicit
  list.
- **Run a retrospective over implementation traces.** After a migration,
  give a read-only agent these inputs:
  - the spec and its diff;
  - the coordinator's brief (which shows the defaults the spec failed to
    decide);
  - the agents' notes files;
  - the reviewers' "spec ambiguities" sections;
  - the raw agent transcripts.

  Tell it to find "feedback that would have SIMPLIFIED implementation or
  prevented bugs, grounded in evidence from the traces, not speculation".
  Friction signals to look for:
  - one section re-read many times;
  - back-and-forth over one sentence;
  - reversals and rework;
  - disagreements between implementations;
  - time spent on something one sentence could settle.

  Quantify the findings. In one migration, 48% of review findings and both
  security blockers traced back to the spec.
- **Filter implementer feedback before it reaches the spec.** Friction is
  evidence of where the spec is unclear. It is not proof that the spec needs
  more rules. Agents' retrospectives push toward defining everything: server
  internals, rate-limit floors, invariants across all fields. The user
  rejected most of those. Keep what clients need to interoperate. Prefer a
  default over an invariant. Bring each item with a verdict (valid / already
  covered / skip, and why) and paste-ready wording.
- **Process outside reviews item by item.** For a review the user pastes in
  ("we don't have to accept these, just consider"), give a verdict per item,
  a minimal diff for the accepted ones, and the open questions. Push back on
  reviewer items with reasons.
- **Account for size after a rollout.** "We simplified the protocol, I was
  hoping it would shrink." Account line growth per area (spec, fixtures,
  server, client) and explain it. A simpler spec should give smaller code. If
  it doesn't, find out why. In one case the cause was pretty-printed
  fixtures.

## 7. Reviews of the spec itself

Run these as parallel read-only subagents with sharp briefs. Merge their
findings into one table with a "raised by" column. Findings that several
reviewers raised independently come first.

- **Implementer read.** Brief: "Read the whole spec as if you had to
  implement it from scratch, twice: (a) a minimal client that only does the
  core, and (b) a full server with every capability. Existing implementations
  follow the previous revision, so don't treat them as ground truth. Report
  where an implementer would be stuck, or where two reasonable implementers
  would build incompatible things. Look at what a result contains, ordering,
  error codes, defaults, contradictions, and edge cases." One run found ten
  interop bugs.
- **Consistency and leftovers.** Give the reviewer the intended design as a
  list, and have it flag anything that contradicts it:
  - a MUST in one place and a MAY in another;
  - one policy stated three ways;
  - an example that breaks a rule;
  - "two steps" that lists three;
  - every JSON block that fails to parse.
- **Per-consumer reviews.** Use one reviewer per implementation (web client,
  constrained server, reference server and load tester) and one for the
  conformance suite ("which rules have no tests; the smallest set of fixtures
  worth adding"). Each reports:
  - required changes;
  - optional changes;
  - unclear spec points, with suggested wording;
  - interop risks;
  - cost impact.
- **Domain-expert persona review.** For example: "an expert in WebRTC, very
  familiar with LiveKit". Give it the focus areas. Tell it the authors want
  the protocol MINIMAL, to flag only what is needed for interoperability or
  correctness, and to label nice-to-haves. Output: Critical / Should fix /
  Nice-to-have / Looks good. Answer each item with a "my take" column.
- **Independent review of your own patch.** Before a security-relevant spec
  change lands, have a fresh agent check it against a scenario list: does it
  close the hole; is it consistent with the related sections; what about an
  unauthenticated request presented later, two tabs, two accounts, or a
  guest connection; are key words used consistently; is there a HISTORY
  line?
- **Reference remap verifier,** after renumbering: check every changed link
  against the content of its new target.
- **Final cleanup check:** stale names, links that resolve, every example's
  order, and duplicated rules.

## 8. Conformance: fixtures, validators, probes

- **Write fixtures from the spec alone,** never generated from an
  implementation. Portable JSON scenarios (replay: frames in, expected state
  out; session: scripted exchanges) pin behaviour across languages.
  - Version the fixture format.
  - Delete variants that the spec now forbids.
  - Don't write tests asserting that a removed feature stays removed.
- **Mutation-test the fixtures.** Write deliberately broken copies and
  confirm the checker catches each one. "All 15 broken copies were caught."
- **Writing a schema exposes design smells.** Writing a JSON Schema for one
  protocol surfaced these:
  - results that don't carry their method;
  - one method with three shapes by direction;
  - message kinds told apart by missing fields;
  - an open `format` in one place and a closed one in another;
  - stutters;
  - a singular name among plurals;
  - examples that can't be validated because of `...`.
  Write the schema early.
- **Test the validator with known-bad frames.** The first schema accepted all
  of them, because unknown methods matched the catch-all for the other
  direction. A lenient schema that allows unknown keys hides renames
  (`membership` versus `memberships`), so use a strict variant for fixtures.
- **Validate recorded live traffic.** Capture every frame from each
  implementation's test suite and check it against the schema. One run
  checked about 17,000 frames. Server leniencies found this way become spec
  questions.
- **Write a validator for rules the schema can't express.** For example:
  - every frame speaks the current version;
  - undefined names carry the extension prefix;
  - no frame arrives between a barrier request and its result;
  - no fixture repeats a variant;
  - stated size limits hold.
- **Run fixtures over every envelope variant,** such as with and without an
  optional `jsonrpc` key.
- **Run a black-box conformance probe** written from the spec without reading
  the server code first. Use policy profiles per server, so documented local
  policy isn't counted as a failure. Report a table of severity | section |
  observed | root cause file:line | suggested fix. Run the process-killing
  tests last, on throwaway connections.
- **When fixtures fail against a real client,** confirm the fixtures are
  right with a throwaway patch, then schedule the real fix.
- **Load and violation testing:** many concurrent clients through scenarios
  (churn, flood, threads, edits, history). Report errors, protocol
  violations (for example `log_id` order), and leaks. Add the tricky patterns
  the spec allows, such as pipelining behind `auth`.
- **Interop in CI:** client × each server. Pin the test peers (submodules) to
  chosen versions, not `main`.
- **After each rule change, add a fixture that tells old from new behaviour.**
  For example, a cleared avatar against a stale recorded copy. Port every
  attack a reviewer found into a regression test.
- **Write regression tests that fail on the old code.** Verify by restoring
  the old line temporarily.

## 9. Removal and minimization passes

Do this pass without being asked. "Nothing left to consolidate or simplify?"
found two more real cuts in a document Claude had called finished. Sort the
findings into Remove / Fix / Add / Checked and fine. Test each removal
candidate:

- Is any implementation actually using it? Grep for producers and consumers.
  One flag had one producer and zero consumers. One field was always sent
  with the same value.
- Does the spec contain admissions that it is redundant ("clients MUST
  accept the result as confirmation") or special cases that exist only
  because of it?
- Could it be added back later without breaking anything? If yes, removing
  it now is cheap.
- What real use would be lost? Before removing `prev_log_id`, ask: "What if
  we wanted edit history in a client, is it equally easy without it?" It
  stayed, and its wording now states that use.
- Does it contradict another rule?
- When minimizing, list what the shorter text no longer says. One example:
  "Four things the shorter text no longer says". Let the user accept the
  gaps knowingly.
