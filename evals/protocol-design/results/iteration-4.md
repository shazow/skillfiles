# iteration-4: skill v3 vs no skill, generative evals

Three runs per configuration.

| eval | with_skill | without_skill |
|---|---|---|
| eval-11-shopping-list-footgun-count | 1/4, 1/4, 1/4 | 1/4, 3/4, 3/4 |
| eval-12-lint-overspec-pressure | 11/11, 11/11, 11/11 | 10/11, 10/11, 10/11 |

Eval 11 in detail, after a grader normalized the counters' reports to the
12 required scenarios (lower is better):

| run | with_skill: scenarios with a footgun | data loss | silent divergence | without_skill: scenarios with a footgun | data loss | silent divergence |
|---|---|---|---|---|---|---|
| 1 | 5 | 3 | 2 | 5 | 1 | 3 |
| 2 | 5 | 3 | 2 | 2 | 0 | 2 |
| 3 | 5 | 3 | 2 | 2 | 0 | 2 |
| mean | 5.0 | 3.0 | 2.0 | 3.0 | 0.33 | 2.33 |

| metric (designer run) | with_skill | without_skill | delta |
|---|---|---|---|
| time_seconds | 252.4 | 156.6 | +95.8 |
| tokens | 102033 | 61343 | +40690 |

## Notes

- **Principle 2 holds.** On eval 12 every run picks the same three real
  interop gaps. Only the no-skill runs also write rules nobody asked for into
  the spec; the skill's runs propose them in the reply instead.
- **Principle 1 fails.** On eval 11 the skill's designs carry more footguns,
  and far more data loss, than the no-skill designs. The failures the
  with-skill designs share:
  - the server rejects a whole batch on a 400 or 413 while the client
    retries anything that isn't a 200 unchanged, so the outbox jams for good;
  - unknown keys are ignored, the op is acknowledged, and a later full-state
    replace erases a newer peer's data (the skill's extension rule
    backfiring in a sync protocol);
  - minimal constructions: edits with no identity, ordering by device clock
    or by arrival.
- The two best designs came from the no-skill runs: a server-ordered op log,
  op IDs the server deduplicates, per-op rejection naming the op, and new
  features under `/v2/`.
- Hypothesis: the skill's pull toward a minimal core overrides principle 1.
  A smaller spec that a hurried implementer gets wrong is not simpler.
- Pipeline-agent cost (implementer, counter, grader) isn't in the timings
  above.
