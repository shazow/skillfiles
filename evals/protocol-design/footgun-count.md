# Footgun count: a generative eval for principle 1

Principle 1 says that the careless implementation of a protocol must be
correct. Asking for a review of a spec with planted problems doesn't test
this, because models find planted problems with or without the skill. This
eval tests the protocols the skill *designs*.

Each run has three stages, each run by a separate agent:

1. **Designer.** It gets the eval prompt and, depending on the
   configuration, the skill. It writes `PROTOCOL.md`.
2. **Hurried implementer.** It gets only `PROTOCOL.md`: no skill, and not
   the designer's reply. Its brief is below. It writes the obvious client
   and server.
3. **Counter.** It gets `PROTOCOL.md` and the implementation. It writes and
   runs adversarial scenarios, and it decides which failures are footguns.

Run each configuration at least three times, because one run can't show a
small difference. The score is the number of footguns: lower is better.

## Implementer brief

> You are a developer with an afternoon to implement this protocol. Read
> `PROTOCOL.md` once, then write the most straightforward server and client
> in Python 3, standard library only, in `impl/`. Follow the spec and its
> examples. Where the spec doesn't say how to do something, do the obvious
> thing and move on. Don't add defences the spec doesn't ask for, and don't
> second-guess the design. Use an in-process transport, with function calls
> or queues standing in for the network, and make the frames JSON. Add a
> `demo.py` that runs the spec's main example end to end. Write
> `impl/NOTES.md` listing every place where you had to guess.

## Counter brief

> You test a protocol by attacking its naive implementation. Read
> `PROTOCOL.md` and `impl/`, then write and run scenarios in `attack/`.
> Cover at least these:
> - offline edits by two clients, then reconnect;
> - concurrent edits to the same item;
> - delete versus concurrent edit;
> - a retry after a lost reply;
> - a lost message in each direction;
> - a duplicate delivery;
> - reordered delivery;
> - a client restart or reinstall;
> - clock skew between clients;
> - unknown fields from a newer peer;
> - an empty, null, or missing field;
> - very large input.
>
> For each failure, decide whether it is a **footgun**. A footgun is a
> failure that the implementation reaches by following the spec and its
> examples, or by taking the obvious path where the spec is silent and an
> implementer would reasonably guess. It is not a footgun if the
> implementation contradicts the spec, or if the failure needs an
> implementation choice no reasonable implementer would make. Each
> `impl/NOTES.md` guess that leads to a failure counts as a footgun.
>
> Write `attack/REPORT.md` with:
> - a table of every scenario, with columns `scenario | outcome | footgun?
>   | severity (data loss, silent divergence, crash, cosmetic) | spec text
>   or silence that led there`;
> - the total number of footguns;
> - the number of data-loss and silent-divergence footguns.
>
> Be strict: show each failure with a run, not an argument.

## Assertions

Score the counter's report:

- "No footgun causes silent data loss"
- "No footgun causes silent divergence between clients"
- "Total footguns ≤ 2"
- "The naive implementation runs the spec's main example correctly"

Record the raw footgun count in the run's `grading.json` evidence, so a
benchmark can compare means across runs.
