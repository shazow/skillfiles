# <Name> Protocol

<!--
Skeleton for a new protocol spec. Replace every <placeholder> and delete
these comments. Keep the section order: each part should be implementable
with only what came before it.
-->

<Name> is for <who: the parties and how much they trust each other>. That
<trust model / scope> keeps the protocol small: <what it deliberately leaves
out, such as federation or spam defense>.

The goal is <many independent implementations that interoperate / ...>. A
<smallest implementation> needs only the core ([§3](#3-core)). Everything
else is an optional capability ([§4](#4-capabilities)) with a fallback.

Example of a valid session:

```jsonc
// <- <first frame from the side that speaks first>
{"method": "<hello>", "params": {"<name>": 1, "capabilities": [], "auth": ["<scheme>"]}}

// -> <client authenticates>
{"method": "auth", "id": "c1", "params": {"scheme": "<scheme>"}}

// <- <server assigns identity>
{"id": "c1", "result": {"you": {"user_id": "<id>"}}}

// -> <the core action>
{"method": "<action>", "id": "c2", "params": {"...": "..."}}

// <- <what everyone sees>, then the confirmation
{"method": "<action>", "params": {"...": "..."}}
{"id": "c2", "result": {"<object>_id": "<id>"}}
```

---

## 1. Transport & framing

- <Reference transport; others are possible.>
- <One frame per transport message / line.>
- <Envelope: requests carry `id`, notifications don't; results and errors.>
- Unknown keys are ignored and MAY be dropped. Unknown notifications are
  ignored. An unknown request gets `unsupported`.
- <Ordering: what is and isn't guaranteed. Prefer correlation by ID over
  ordering rules.>

### 1.1 Envelope and replies

<Core methods: which are requests (the sender needs the reply) and which are
notifications. General errors: unknown or hidden IDs and rejected values are
`invalid_params`, sizes `too_large`, policy and count limits `denied`.>

### 1.2 Retries and deduplication

<A retry repeats the same `id` and `params`. The server deduplicates on
(identity, `id`) and returns the original result.>

## 2. Identifiers

- <Each ID: who assigns it, its format, its scope, and how IDs compare.>
- <Position (log) IDs vs object IDs, if the protocol keeps a log.>
- <The one replay rule, if any: the greatest position per key wins.>

## 3. Core

<What every implementation does. Nothing here depends on a capability.>

### 3.1 <Handshake frame>

### 3.2 Authentication

### 3.3 <Primary object>

### 3.N Core conformance checklist

Every server:

1. <...>

A minimal client (informative):

1. <...>

---

## 4. Capabilities

Everything beyond the core is optional. Each capability adds one coherent
feature and says what a peer does without it. A capability shows support,
not permission.

| capability | adds | fallback | spec |
|------------|------|----------|------|
| `<cap>`    | <...> | <...>   | [§4.1](#41-cap) |

**Extension names.** A name that this document does not define starts with
`ext:`. This document never defines a name with that prefix.

<Order capabilities by how commonly they're implemented, and by teaching
order: one close to the core first.>

### 4.1 `<cap>`

---

## Appendix A — Conventions (informative)

## Appendix B — Valid scenarios (informative)

Exchanges that are valid under this spec but easy to get wrong, collected so
implementations accept them. Each follows from the sections it cites.

## Appendix C — Under consideration

Designs that are not yet part of the protocol, kept here so implementations
can experiment and converge on them.
