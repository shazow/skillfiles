# Design principles

These heuristics came out of many rounds of design review on a real protocol.
Most were learned by getting it wrong first. Each one says what to prefer and
why. Examples come from a chat protocol (rooms, messages, reactions), but the
reasoning applies to any protocol where independent implementations have to
interoperate.

Every rule in a protocol is paid for by every implementer, in every language,
for as long as the protocol lives. Most of what follows is a way of keeping
that bill small.

## Contents

1. Start from scope and trust
2. A minimal core plus optional capabilities
3. Fewer guarantees, fewer mechanisms
4. Identity, ordering, and logs
5. Shapes and names
6. State, merging, and extension data
7. Requests, results, and errors
8. Protocol versus policy
9. Cost and scale
10. Security and privacy
11. Versioning

---

## 1. Start from scope and trust

- **Write down who the protocol is for and how much the parties trust each
  other.** The trust model sets the size of the protocol. "Groups whose
  members mostly trust each other" removed federation, spam defense, and
  sybil resistance in one sentence. Later it settled arguments such as "should
  the server reject mentions of users not named in the text?" The answer was
  no, because semi-trusted groups may want invisible mentions.
- **Name the topologies you might want later.** One example is "someday this
  may run peer-to-peer". When two options are otherwise equal, choose the one
  that also works in that future topology. It usually means authored events
  rather than server-computed aggregates.
- **Name the implementations you expect.** For example: a full server, a bridge
  to another protocol, a 100-line script, a cheap serverless deployment, a bot
  that connects to send one message. Designs that are easy for the smallest of
  these and cheap for the most constrained tend to be good designs.
- **The protocol makes use cases possible; it doesn't list them.** "We just
  want to be able to implement all of these things on top of the defined
  protocol, but it doesn't have to strictly define every use case yet."
  Before adding a field, ask what breaks without it. "Why do we need
  `label`?" "It's not strictly needed." So it went.
- **Specify what clients need to interoperate; servers do the rest.** "We
  just want enough so that clients implement correct behaviour. The servers
  can do whatever they want." Some consequences:
  - The client doesn't need to know in advance what it may do. A UI may offer
    an action that will fail, because `denied` with a readable message is the
    contract. Per-user permission lists in the handshake were rejected.
  - Invitation state, consent flows, and pending queues can stay inside the
    server. Only what crosses the wire is specified.
  - Client behaviour that needs no agreement between implementations stays
    out of the spec, such as a client announcing a new thread with a
    message.
  - A feature that could work out of band gets only what discovery needs. For
    example, email sign-in got a scheme name so clients know a server
    supports it, and little more.
- **Start from the experience the user wants, then check what the spec
  already does.** "High level, the experience I want: … I think this is
  already covered in the protocol as is?" It was. The proposed new array was
  for something nobody needed.

- **Hunt footguns in the default construction.** Each of these made an
  obvious implementation wrong, and each was fixed by changing the
  construction rather than by adding a warning:

  | footgun | construction that removes it |
  |---|---|
  | meaning taken from an absent field ("no body means delete") | an explicit marker (`deleted: true`) |
  | `null` clears a value, absent keeps it | an empty value clears; `null` is not special (§6) |
  | clients must re-send keys they don't know | the server merges and keeps them (§6) |
  | an identity field that is optional for special cases | a placeholder value; the shape stays uniform (§5) |
  | a new field that is unsafe to ignore | a new method, which fails loudly (§2) |
  | a request whose meaning depends on connection state | fix the effect when the request is made (§10) |
  | a timeout only one side knows | send it on the wire (§3) |
  | sequential IDs inside URLs | unguessable URLs (§10) |
  | an unsafe default (public unless flagged) | the safe value is the default, and an unknown flag fails closed (§6) |
  | an example that contradicts a rule | examples validated against the rules (spec-writing §5) |

  A warning in the spec ("implementers must be careful to…") is a sign that a
  footgun is still there.

## 2. A minimal core plus optional capabilities

- **The core is what every implementation must do, and nothing else.** It
  should be enough for a working minimal implementation in about a hundred
  lines. Test every core rule with one question: "Could a core-only,
  single-scope implementation ignore this and still be correct?" If yes, it
  doesn't belong in the core.
- **Push everything optional out of the core, including concepts the core
  seemed to need.** In the chat protocol, rooms left the core. `room_id`
  became optional with a default room, and a minimal server ignores rooms
  entirely.
- **Each capability adds one coherent feature and states its fallback.**
  Example: "`history`: page and recover a room's log; fallback: session-only
  scrollback." A capability table with columns *adds / fallback / section* is
  the map of the protocol.
- **A capability shows support, not permission.** Servers still refuse
  individual requests by policy.
- **Degrade gracefully; don't negotiate.** Only one side, usually the server,
  advertises capabilities. Clients ignore capabilities they don't know.
  Unknown keys are ignored. Unknown notifications are ignored. Unknown
  requests get a well-defined error. Avoid client capability lists and
  handshakes. Every negotiated feature doubles the states that both sides must
  handle.
- **When silently ignoring a new feature would be unsafe, use a new method,
  not a new field.** An unknown field is dropped without a sound. An unknown
  method fails loudly. Example: slash commands sent as `message` with a
  `command` flag would be posted publicly by a server that doesn't know the
  flag. A separate `command` method makes that server refuse it instead, which
  is the safe failure.
- **Optional server behaviour degrades by being ignored.** It doesn't need a
  capability flag or a MUST-reject rule. Prefer "a server MAY ignore
  `latest_log_id`" to "a server that doesn't support X MUST reject Y" or to a
  new capability. If the client must know which path the server took, add the
  smallest in-band signal. Example: the server includes `left` only when it
  applied the delta filter, so a result without `left` is a full listing.
- **Let deployments choose capabilities.** A constrained deployment (a free
  tier, an embedded device) turns off whole capabilities rather than asking
  for finer-grained protocol switches.

## 3. Fewer guarantees, fewer mechanisms

- **Removing a mechanism beats replacing it with a guarantee.** When a field
  turns out to be unused, the instinct is to "make removal safe" with a new
  MUST, such as an ordering rule. First ask whether an identifier that already
  exists makes the guarantee unnecessary. Example: an `echo` flag was dropped,
  and clients matched the result to the broadcast by `message_id` in either
  order. That needed no ordering rule. Every guarantee binds every transport
  and every implementation.
- **Everything one side holds for the other needs an end both can observe.**
  An assigned job, a pending request, a reserved slot, and a reconnect grace
  period each need a lease, an acknowledgement, or a bound that both sides
  know. If a coordinator privately decides how long it keeps a disconnected
  worker's job, the worker keeps running it while the coordinator hands it
  to someone else, and the job runs twice. If an assignment is lost in
  transit and nothing ends it, it holds a slot forever. Send the value
  (`grace` in the handshake result), say what ends each held thing when a
  message is lost, and make it a MUST when ignoring it breaks the other
  side.
- **Request IDs are opaque and imply no order.** Servers MAY process requests
  concurrently and reply in any order. A client that needs one request applied
  before another waits for the first reply.
- **State an ordering guarantee where data has no sequence number.** Records
  with a log position can arrive in any order. State without a position, such
  as user profiles or memberships, races. One server-side rule ("a result
  reflects every notification sent before it on that connection") is cheaper
  than buffering logic in every client.
- **Optional optimizations must not complicate the mandatory path.** A naive
  server that replays its log must be fully conformant. Compaction,
  aggregation, and caching are MAY. If an optimization creates the spec's most
  intricate rules and nobody implements it yet, drop it.
- **Reuse a primitive before adding one.** Each of these became a use of an
  existing primitive:
  - Magic-link email sign-in became the existing `token` scheme with a
    short-lived token that the server upgrades.
  - Invites became the same token idea.
  - Calls became private rooms.
  - DMs became private rooms.
  - Interactive prompts became an embed whose buttons send existing
    commands.
  - A separate membership notification became a key in the existing room
    update.
- **When fixes pile up for one feature, look for the primitive it
  reimplements.** A WebRTC design gathered review fixes for membership,
  privacy, and consent until the user saw "this is basically all the rooms
  mechanic".
  - Settle the general primitive first (private rooms).
  - Then remove the special mechanisms one by one.
  - Then prove nothing was lost, with a table of every old feature, its new
    form, and what changes in meaning.
  - Don't abandon a unifying direction at the first objection; push the
    reuse further before falling back to a new primitive.
- **If no primitive explains the pile-up, rewrite the section.** The warning
  sign is often small payload questions ("why does this field exist?", "show
  me how X is set") that keep exposing duplication. Offer two or three
  complete variants, each built from fewer rules. Judge them against one
  stated objective, such as "minimum coordination between independent
  implementations". List what each variant deletes. Apply none until the
  user picks one. Work already built on the old design is not a reason to
  keep it.
- **Make the most general case the baseline.** Threads that stand alone are
  the baseline; a link to an origin message can be added later as an
  optional field. Designs that assume the special case ("every thread has an
  origin message") break on the general one.
- **Before adding a mechanism, look for a general rule that is wrong.**
  Example: sign-in instructions sent before `auth` seemed to need a new
  `auth_notes` field, a `deny` list, or hints in errors. The real bug was that
  delivery was defined only for signed-in users. "Signing in gates sending,
  not receiving" fixed it in one sentence.
- **Question the constraints behind "what you lose".** When an option looks
  costly, list the constraints that make it costly and ask whether each one
  can be dropped. One case: threads-as-rooms looked expensive until per-room
  message IDs became global and replies could embed their target. The
  constraints were choices, not facts.
- **Don't spend rules on harmless edge cases.** An edit that empties a message
  can just render as an empty message. "Clients render it" is an acceptable
  answer.
- **Don't extend a mechanism to cases that have no use for it.** A
  previous-version pointer on messages enables edit history. Adding it to
  reactions "for symmetry" adds work and serves no one.
- **Don't add fields for features that aren't designed yet.** Adding an
  optional field later doesn't break anything. Removing one after
  implementations exist does. Example: `room_count` was added and removed
  within a minute, "until we add pagination".
- **When a generic mechanism arrives, re-audit the specific features it
  covers.** Once `command` existed, a typed `mute` request became a server
  command and was removed.

## 4. Identity, ordering, and logs

- **Keep position and identity as separate IDs.** A log position (`log_id`)
  says where a change happened. An object ID (`message_id`) says which object
  it describes. One object has many transitions, so one field can't serve
  both. Generating the object ID from its creation position is fine. It gives
  creation order and uniqueness for free while keeping the concepts separate.
- **Prefer one monotonic sequence across the whole server.** It makes object
  IDs globally unique, lets objects move between scopes, and gives one clock.
  If the position is the commit time in milliseconds, or the previous value
  plus one, it doubles as a timestamp. Then no separate time field is needed.
- **The server assigns identity.** Clients may hint, for example a requested
  display name or user ID, but deduplication, sender trust, and "stable" all
  rest on server-assigned IDs.
- **Use one replay rule for every source: the greatest position per key
  wins.** Live notifications, history pages, and copies embedded in other
  objects all go through the same rule. Then:
  - embedded snapshots are safe;
  - compacted history equals raw replay;
  - duplicates and reordering are harmless.
  State the rule once.
- **Treat the append-only log as a design lens.** Ask: "Is there anything
  left in the protocol that wouldn't work as an append-only log?" In one audit
  this found:
  - a real bug, reactions lost when a message moved;
  - unlogged state;
  - deletion that couldn't erase anything, fixed by allowing exactly one
    rewrite, redaction to a tombstone;
  - retention that dropped live objects, fixed by compacting at rest instead
    of truncating.
- **Log invariants are sacred.** Positions only increase and are unique.
  Lower bounds never decrease. The only rewrite is redaction. Check every new
  idea against these before writing it, such as a placeholder where history
  was purged. Precedent: before discarding part of the log, *append* a summary
  record; don't rewrite an old one.
- **Put state in the log if its deltas must be correct.** Memberships were
  unlogged, so "what changed since position X" missed joins made from other
  devices. Logging them fixed deltas, member lists in history, cross-device
  consistency, and a separate join notification, all at once. When one
  mechanism fixes several problems, accept its cost.
- **Prefer local pointers to global indexes.** A `prev_room_id` on a moved
  message lets servers store each room's log separately. A "look up any record
  by position" request would force a global index. Weigh the storage and
  indexing burden that every rule puts on servers.

## 5. Shapes and names

- **Use one object shape at different completeness levels.** The client's
  request is a partial object. The broadcast is the complete object. A history
  entry is the object. A reference is the object with only its ID. Presence of
  the position field marks a complete snapshot.
- **Make objects self-describing, and flatten wrappers.** If a wrapper exists
  only to hold one or two IDs next to the object, move those IDs into the
  object. `{"root": {"message_id", "log_id", "message": {"message_id", ...}}}`
  repeats a key across levels. Make it `"message": {...}`. One flattening like
  this removed the wrapper from requests, broadcasts, and history at once.
- **Use separate methods for snapshots and deltas.** A listing request returns
  a complete answer for its filter. A separate notification carries only
  changes. Never let a key mean "complete set" in one place and "what changed"
  in another, and never use an echoed flag to tell them apart.
- **Give each method one meaning.** List every payload shape a method can
  take, side by side. If the same key means different things depending on what
  else is present, split the method.
- **Use typed arrays per record kind in batch results.** For example
  `messages`, `reactions`, `memberships`. They beat an interleaved list with a
  discriminator, and they beat full RPC frames nested inside a result. Old
  clients ignore new arrays. If replay is per-key newest-wins, order across
  arrays doesn't matter. Any empty array may be omitted, and a missing array
  means empty. Apply that to all arrays, not some.
- **One field, one job.** Never give an existing field a second meaning by
  convention. Using `reply_to` to also mark a thread's origin "breaks how
  `reply_to` may be used otherwise". A room description stored as a message
  failed for four reasons:
  - edits reached the wrong audience;
  - the wrong people controlled it;
  - retention deleted it;
  - the record stopped being complete at its position.
  When a field's reason has gone, remove it rather than rename it, then
  examine what is lost.
- **Keep shapes uniform.** Prefer placeholder values to optional identity
  fields. Every message has `from.user_id`; system senders are placeholder
  users. Making `user_id` optional "introduces bugs by branching this logic".
- **Prefer explicit markers to inference from absence.** Keep `deleted: true`
  even though tombstones lack a `body`. Bare references and push payloads lack
  a `body` too, and "no body means delete" would delete by accident. Don't
  infer structure from "the first X" either. "The first message in a thread
  replies to the origin" breaks on moves, deletes, and other replies.
- **Separate record types by key and by who writes them.** Reactions are keyed
  `(message_id, user_id)`; messages are keyed by `message_id`. Folding
  reactions into messages would make every 👍 a new message snapshot.
- **Prefer an ordering rule to a mutable pointer.** Write "`peers` lists seats
  oldest first, and the oldest seat hosts", not a `host_peer_id` field that
  must be kept up to date. The ordering rule also covers handover.
- **Key state per device on a composite key** `(user_id, peer_id)`, or one
  device overwrites another.
- **Keep symmetry with existing pairs.** Keep `rtc_leave` if there is
  `rtc_join`, as with `room_join` and `room_leave`, even if one method could
  be dropped. A familiar pair of methods costs readers nothing. This doesn't
  contradict §3: copying a *mechanism* onto records that have no use for it
  does have a cost.
- **Extend with keyed groups, not type tags.** `actions: {commands: [...],
  links: [...]}` grows for free, because unknown keys are ignored. A
  per-item `type` needs extra rules for unknown types.
- **Name a field for its relationship, not its type.** Use `reply_to`, not
  `message`, since one frame can hold two messages. Use `member_ids`, not
  `user_ids`, because it says what the IDs are.
- **Keep names in step with each other:**
  - Filter values match result array names: `filter: joined` gives
    `joined: [...]`.
  - Every log position ends in `_log_id`; a bare `_id` is an entity.
  - Methods of one capability share a prefix: `room_list`, `room_join`,
    `room_set`.
  - Spell names out (`width`, not `w`).
  - Avoid generic words that clash with other meanings ("events").
  - Don't let one name mean several things (cap, method, array, field).
  - Don't use vocabulary foreign to the protocol (`nick` in a protocol that
    says "name").
  - Avoid stutter such as `room_update.members[].members[]`. A small one
    (`reactions.reactions`) can be cheaper than churn.
  - Use one term per concept across the whole spec, prose included. Rejecting
    "features" for "capabilities" came down to "two terms for one idea would
    be the one real mistake". Before renaming, list every sentence that would
    change.
  - Settle names with a prior-art survey across many protocols. For the
    handshake, the version field is named after the protocol (`apron: 7`, as
    JSON-RPC has `"jsonrpc": "2.0"`). The software string is `agent` (as in
    git, libp2p, and HTTP `User-Agent`). A bare `version` reads as the
    software's version.
  - When a name feels wrong, ask whether the method should exist at all.
    Several rounds of renaming a membership notification ended with folding
    it into the existing room update.
- **Don't encode structure in free text.** A title is a `title` field, not
  "the first line of the body". Servers shouldn't parse rich text to find
  meaning. Mentions became an explicit `mentions` list after two
  implementations disagreed about which `@` signs inside Markdown code were
  mentions.
- **Derive state from present fields, not status flags.** An upload without a
  `url` is still uploading. A stream with final `text` has finished. Drop
  `pending`, `removed: true`, and `joined: true` booleans when the client can
  derive them.
- **Tie lifecycle to an owning record.** Uploads live as embeds inside a
  message, so deleting, expiring, or compacting the message cleans them up. A
  side table of upload IDs needs its own cleanup rules and its own state.
- **The client sends only what it knows. The server derives and owns the
  rest.** Size, dimensions, final URLs, and previews are server-owned. Servers
  *ignore* server-owned fields on input; they don't reject them. That lets
  clients send back whole objects.
- **Model special cases as values of existing fields.** System notices come
  from reserved sender IDs (`~server`, `~room`, `~private`) that state a
  scope. They aren't new entity kinds, and they aren't absent senders. A
  reserved prefix degrades better than absence. A missing `from` breaks every
  renderer, can't tell actors apart, and turns a bug that drops the field into
  a change of meaning.
- **Text that a server may vary belongs in data.** If servers may call
  something different names, send the name ("System message to you") and let
  clients render generically (`Name (@id)`). Don't put a vocabulary in
  clients.
- **Don't use booleans for open categories.** `bot: true` bakes in a
  dichotomy. Use conventions on IDs or names, or extension data.

## 6. State, merging, and extension data

- **Prefer state that users author over state the server aggregates.** Each
  user replaces their own complete reaction set on a message. Concurrent
  reactors never overwrite each other. Nothing reads, modifies, and writes,
  nothing toggles, and the server never computes totals. Clients aggregate.
  This also suits peer-to-peer.
- **Replace complete state rather than send deltas** for per-user sets and
  snapshots. Retries and replays become idempotent.
- **Separate current state from recorded state.** Current objects (the
  signed-in user, member lists, user listings) merge into the client's copy.
  Recorded copies (the `from` on an old message) are display fallbacks and
  never overwrite current state.
- **Use one merge rule, one level deep, everywhere.** A present field replaces
  the kept value. An empty value (`""`, `[]`, `{}`) clears it. An absent field
  stays. Values below the first level are replaced whole. `null` is an
  ordinary value. Reuse the same rule for extension data, one level into its
  keys. JSON Merge Patch (RFC 7396) was rejected: `null`-clears can't be told
  from missing in typed decoders (Go `*string`), and it would add a second
  clearing rule.
- **Cleared means an explicit empty value.** Keep `""`, `[]`, or `{}` so
  "cleared" differs from "never known". Then a fallback to recorded copies
  applies only to fields the kept object lacks; otherwise a cleared avatar
  comes back from old messages. Servers must send explicit empty values in
  complete objects (`roles: []`). Otherwise a client that missed the change
  keeps stale state forever.
- **Server fields are read-only: a request never changes them.** Replace a
  list of exceptions ("ignore `log_id` on input, except `message_id`
  addresses the message, except…") with a rule about what a request does to
  a field. Similarly, write "fields ending in `_id` are fixed at creation"
  rather than naming each one.
- **Place state by its owner, audience, and lifetime.** Before choosing where
  a value lives, sort it: per connection, per user, per scope, or derived for
  others to see. Then question every scoped variant ("do we need per-room
  idle?"). Shared ephemeral state, such as who is in a call right now, rides
  on its record as an unlogged delivery field, so joins and leaves don't
  churn the log. A private per-user setting, such as a mute, travels on the
  method that sets it and is echoed to all of that user's connections.
  Others see only the derived result.
- **Design for statically typed decoders.** Never require implementations to
  keep and re-send unknown keys; Go struct decoding drops them. Put extension
  data in one opaque container (`ext`, decoded as a raw-JSON map). Clear with
  empty values, not `null`. Keep large integers exact.
- **The server preserves extension data, not the client.** "Clients MUST send
  `ext` back unchanged" fails in three cases:
  - a client that never read the object;
  - two devices writing different keys at once;
  - a third party saving the object.
  Server-side merge fixes all three.
- **Reserve one prefix for every name an extension adds.** Methods,
  capabilities, schemes, and kinds all use it, such as `ext:irc`. The spec
  never defines a name with that prefix. An extension `ext:foo` keeps its data
  under `ext.foo`. Display values, such as status labels and roles, take no
  prefix. Extension names say what the data is, not who made it. A vendor name
  makes no sense in a generic protocol.
- **Keep capabilities orthogonal.** For each pair, ask: "Does having one but
  not the other mean something?" If not, merge or split them.
- **"Unknown keys are ignored" is also a hazard.** An older server ignored
  `user_id` on `room_leave` and removed *the caller* instead of the target.
  Another older server ignored `private: true` and created a public room. For
  any field where being ignored is destructive or unsafe:
  - Prefer a new method (§2).
  - If it must be a field, a server that knows it but doesn't support it MUST
    reject it (fail closed).
  - The server echoes only flags it enforces, and clients check the echo.
  - A MUST binds only implementations that know the field exists. Older
    peers need a client-side check, such as gating on the protocol version.
- **Don't overclaim compatibility with a base protocol.** "Modeled on JSON-RPC
  2.0, without the `jsonrpc` key, and with string `id`s only" is accurate. "A
  JSON-RPC client can talk to it unchanged" was dropped.
- **Decide extension design from concrete uses.** List real candidates (a
  bio, bridge IDs, bot metadata, room settings, server hints) with who writes
  each and whether others edit it. The table shows where round-tripping
  matters and where whole-object replacement overwrites a concurrent writer.

## 7. Requests, results, and errors

- **A method is a request when its sender needs the reply.** That means data,
  a confirmation, or an error. Otherwise it is a notification. State the
  principle, then list which methods require an `id` and which must omit it.
  Don't let senders choose per call. Allow tolerance: "A server MAY ignore a
  request method sent without an `id`, and a notification method sent with
  one." Typical case: a load tester sent a notification with an `id` and
  waited forever for a reply.
- **A result must stand alone.** A deduplicated retry produces a result and no
  broadcast, so the result carries the created ID. Keep the confirmation even
  when a broadcast echoes the change. Only the result can do these jobs:
  - match the request to a pending local placeholder;
  - confirm to a sender that isn't subscribed;
  - answer a deduplicated retry;
  - carry credentials that must not be broadcast;
  - close every request, as RPC clients expect.
- **Deduplicate on (authenticated identity, request id).** Clients use random
  request IDs, so retries work across reconnects and devices. A deduplicated
  retry skips the side effect, never freshness: its result reflects the
  current state. Otherwise a cached result can overwrite a newer
  notification. How long IDs are remembered is up to the implementation.
- **Notifications never get error replies.** An undeliverable signalling
  notification is dropped. Answering it with `invalid_params` breaks the
  request/notification split.
- **Notifications a request causes precede its result** on that connection.
  That gives clients one code path.
- **Make authentication a barrier.** The server finishes `auth` before it
  processes later frames. Later requests run with the identity `auth` left
  in place. An `auth` that authenticates nothing, such as the start of a
  passkey ceremony, leaves the identity unchanged. A blanket "frames behind a
  failed `auth` are refused" broke signed-in connections that were adding a
  passkey.
  Clients can then pipeline `auth` with their first reads in one round trip,
  which matters on every reconnect. Every notification caused by a change of
  identity follows the `auth` result. Otherwise the client files it under the
  old identity. Make clients robust ("drop kept state at sign-in, apply what
  arrives") rather than adding end-of-batch markers.
- **Reuse the base protocol's error mechanism.** If the framing is JSON-RPC,
  connection-level errors are JSON-RPC errors without an `id`. Don't invent a
  `close` method.
- **Use a few general error codes.** Clients tell errors apart by `code`.
  Human detail goes in `message`, not in a sub-reason enum. Typical set:
  - an unknown *or hidden* ID is `invalid_params`, so the error never reveals
    that something exists;
  - a rejected value is `invalid_params`, and an oversized one is
    `too_large`;
  - policy and count limits are `denied` (the code follows who controls the
    limit);
  - a defined but unoffered feature is `unsupported`.
  Put these in one section. Don't repeat them per method.

## 8. Protocol versus policy

- **The protocol defines the interop surface, not the implementation.** For
  push: the protocol defines the kinds a server offers, how a registration is
  identified, and the payload the client reads. Encryption, retries, and
  collapsing belong to implementations. For streams: one capability, one
  embed kind, one result field, and two endpoints described by behaviour only.
- **Leave policy to servers.** Guest treatment, read-only modes, limits,
  rate limits, expiry, and identity hiding are policy. "Better to
  underdefine." One general rule ("servers MAY refuse any request or field by
  local policy") covers all of them, so no section needs its own.
- **But the spec must settle conflicts between its own rules.** When one rule
  says "announce the identity change" and another says "invisible users look
  offline", implementers follow the more specific rule. The spec has to
  decide.
- **Change the protocol only when it can't express the feature.** For each
  feature request, ask three questions. Does the protocol already allow this?
  If not, what is the smallest wire change? Is the pain real yet? Staged
  multi-file uploads turned out to be client-only. Pre-send background
  uploads were deferred until the delay is shown to matter.
- **An implementation feature should not need a protocol change.** Build such
  features as probes (see iteration techniques). Where the spec fights one,
  judge the conflict by what users see, not by the letter of the text. A
  feature that complies only on a technicality still conflicts. Offer the
  smallest loosening of the spec. If none is cheap, drop the feature and meet
  the need from what the wire already carries. A server-injected "older
  messages expired" notice was dropped this way: "I feel like this is
  malicious compliance with the protocol."
- **A request that changes state is a write for permission purposes**, even
  if nothing is logged.
- **Weigh what a rule costs implementers.** Prefer a default that makes the
  common case right to an invariant that every field must be checked
  against. "New sub-rooms inherit the parent's `private` setting" replaced "a
  frame never refers to a room its receiver can't see", which would have made
  servers audit every field they send.
- **For an optional field, recommend one place for it.** Make it SHOULD in
  the obvious place. Don't require it everywhere. Allow it elsewhere only
  where a client needs it and has no other source; each extra carrier is
  another merge path in every client. `users` comes with `room_list` and
  may come with a newly joined room, but it was dropped from `history`.

## 9. Cost and scale

- **Design for the cheapest deployment you care about.** Count the reads,
  writes, and frames that each rule costs a stateless or metered server. Don't
  force servers to track deltas. Minimal objects in notifications and complete
  objects in listings work for both kinds of server.
- **Keep responses bounded.** Send counts, not lists. Send profiles only for
  the senders on this page. Return complete data now and add pagination
  later. When pagination comes, use an opaque cursor. Avoid live membership
  lists: the expensive part is keeping a list current, not listing it.
- **Offer fast paths without making them the rule.** A keepalive can be a
  fixed byte string, so infrastructure can answer it without parsing. Servers
  must still answer any well-formed form, because RPC libraries add spaces and
  keys.
- **Measure, don't estimate.** "Typing is nearly free" turned out to be 24
  writes per frame on the metered deployment.

## 10. Security and privacy

- **Secure by construction: fix a request's effect when it is made, not when
  its token is presented.** Email sign-in first said "a code presented on a
  signed-in connection adds the address". That allowed account takeover:
  1. Mallory requests a link for Mallory's own address and sends it to
     Alice.
  2. Alice's signed-in client opens it, which adds Mallory's address to
     Alice's account.
  3. Mallory signs in as Alice.

  Patches that depended on connection state made clients worse; one client
  had to reconnect before requesting a code. The fix was **propose/approve**.
  The request proposes the effect, and the token only approves it. A
  guessable code works only on the connection that proposed it. Constrain the
  property ("guessable implies bound to the proposer"), not the mechanism.
  When implementations keep adding defensive machinery around a rule, such
  as a fourth rate-limiter design, revisit the protocol model.
- **Threat-model every "click a link" flow:**
  - login and account-linking CSRF;
  - links built from server configuration, never from request fields;
  - tokens in the URL fragment, not the query string;
  - link scanners that consume single-use tokens, so the page asks for a
    click to confirm.
- **Don't reveal whether an account exists.** Return the same result either
  way. Count unsent proposals against limits too, so timing doesn't leak it.
- **Display data that implies trust is set by the server and rendered
  distinctly.** Roles render as badges, not name text, and users can't set
  them.
- **Privacy flags fail closed.** See "unknown keys are ignored is also a
  hazard" in §6.
- **Peer-to-peer leaks addresses.** Don't answer connection offers before the
  user consents. Allow relay-only connections.
- **Unguessable URLs act as capabilities.** Counter-based paths (`/f/1234`)
  can be enumerated. Write URLs are credentials and go only in the result to
  the writer, never in a broadcast. Header auth breaks `<img src>`, tokens in
  query strings leak into logs, and per-viewer signed URLs can't sit inside
  stored snapshots.
- **Example IDs in the spec suggest implementations.** `embed_1234` invited
  counters, which contradicted the unguessable-URL rule. Pick examples that
  obey every rule.
- **Privacy promises must hold on every path.** For each thing the protocol
  promises to hide, ask which server-originated frame could reveal it. One
  example is an "old identity → new identity" announcement for a user who is
  invisible.
- **Standard passes:**
  - SSRF on any URL a server fetches;
  - injection in anything rendered (HTML in previews, terminal escape
    sequences);
  - sanitize whole texts, never fragments;
  - IP leaks from third-party media;
  - different readers seeing different content for the same object.

## 11. Versioning

- **Before launch, while you are the only consumer:**
  - bump an integer version on every revision;
  - make breaking changes freely;
  - write no compatibility notes;
  - fold late changes into the unreleased version rather than starting a
    new one;
  - remove old code paths, aliases, and tests that a removed feature stays
    removed.
  Agents default to compatibility shims. Remove them.
- **Classify each change as breaking or not** in reviews and PR descriptions,
  even pre-launch. It shows reviewers what an upgrade costs.
- **After launch,** breaking changes need the version, and extensions that
  become standard keep their old prefixed name for a transition. XMPP's
  multi-user chat (MUC) to Mediated Information eXchange (MIX) migration,
  stalled for years, shows why to break things while you still can.
- **Version strings in software should read against the protocol number.**
  For example `myserver/6` speaks protocol 6.
