# iteration-5: skill v3 + F1 + F5 vs no skill, generative evals

The skill under test adds two changes to v3:

- **F1:** principle 1 beats minimalism.
- **F5:** a hurried-implementer pass before a new design is handed over.

There are three new with-skill runs per eval. The no-skill runs are reused
from iteration 4, and the graders were calibrated to iteration 4's grades.

| eval | with_skill (v3 + F1 + F5) | with_skill v3 (iteration 4) | without_skill |
|---|---|---|---|
| eval-11-shopping-list-footgun-count | 1/4, 1/4, 3/4 | 1/4, 1/4, 1/4 | 1/4, 3/4, 3/4 |
| eval-12-lint-overspec-pressure | 11/11, 11/11, 11/11 | 11/11 ×3 | 10/11 ×3 |

Eval 11, normalized to the 12 required scenarios (lower is better):

| config | scenarios with a footgun, per run | mean | data loss, per run | mean |
|---|---|---|---|---|
| v3 + F1 + F5 | 4, 3, 2 | 3.0 | 1, 1, 0 | 0.67 |
| v3 (iteration 4) | 5, 5, 5 | 5.0 | 3, 3, 3 | 3.0 |
| no skill | 5, 2, 2 | 3.0 | 1, 0, 0 | 0.33 |

| metric (designer run) | eval 11, v3 + F1 + F5 | eval 11, v3 | eval 11, no skill |
|---|---|---|---|
| time_seconds | 544 | 374 | 238 |
| tokens | 141688 | 118191 | 68041 |

## Notes

- **Eval 11 improved.** F1 and F5 took the skill from clearly worse than no
  skill to level with it on footgun scenarios: a mean of 3.0, against 5.0
  before. Data loss fell from 3.0 to 0.67, which is still above no skill's
  0.33. Run 3 is the first with-skill run to meet "≤ 2 footguns".
- **All three designers really ran the pass,** with throwaway naive code
  in `outputs/scratch/`. Op IDs (runs 1 and 3) or a per-field stamp merge
  (run 2) removed the old skill's footguns in retry, lost messages, and
  duplicates. Run 3 also made one-sync-at-a-time and durable storage
  normative.
- **One weakness is left in every run.** Any non-200 response is retried
  unchanged, and the whole outbox (or the whole state) travels in one
  unbounded request. So one malformed op, a null field, or a 413 jams a
  phone for good, and nobody is told. This causes every footgun the runs
  have in categories 11 and 12. None of the designers' passes tested
  malformed requests or a body limit.
- **The remaining failures differ per run.**
  - Run 1 stores the outbox only after a 200, so a restart loses offline
    edits.
  - Run 2 compares 13-digit stamps as strings, which overflow in 2286. This
    is the grader's most debatable call; without it, run 2 has 2
    footguns.
- **Eval 12 is unchanged.** Restraint holds at 11/11 ×3, so F1 and F5 didn't
  make the skill over-specify.
- **Cost.** The pass makes eval-11 design runs about 20% more expensive in
  tokens and 45% slower than v3. They now take more than twice the time
  and tokens of the no-skill runs.
