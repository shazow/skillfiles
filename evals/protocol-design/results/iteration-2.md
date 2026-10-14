# iteration-2: skill v2 vs v1

| eval | with_skill | old_skill |
|---|---|---|
| eval-1-ci-runner-new-protocol | 9/11 | 9/11 |
| eval-2-apron-pinned-messages | 9/9 | 9/9 |
| eval-3-lantern-tighten-section | 12/12 | 12/12 |
| eval-4-impl-spec-conflict | 6/6 | 5/6 |
| eval-5-status-pileup | 5/7 | 4/7 |
| eval-6-decision-list-followup | 10/10 | 9/10 |

| metric | with_skill | old_skill | delta |
|---|---|---|---|
| pass_rate | 0.92 | 0.85 | +0.07 |
| time_seconds | 227.07 | 214.65 | +12.4 |
| tokens | 114045.67 | 111201.00 | +2845 |

## Notes

- Baseline here is the previous skill version (v1), not no-skill; iteration 1 has the no-skill comparison. Assertions passed: new skill 51/55, v1 48/55 (mean pass rate 92% vs 85%), at about +3k tokens and +12s per run.
- Eval 4 (spec conflict found while implementing) separates the versions on exactly R2: the new skill wrote a separate brief for a spec session; v1 planned to edit PROTOCOL.md, schema and fixtures itself.
- Eval 6 (decision list) separates on R6: v1 handed a conditional approval back to the user ('tell me and I'll add it') although the user's condition was already settled by the text.
- Eval 5 (status pile-up) shows a gap in BOTH versions: each applied a full redesign of the section for a single bug report instead of applying the minimal fix and proposing the rewrite. Neither built the owner/audience/lifetime table (R3 lives in a reference file a bug-fix run may not read). Only the new skill offered real whole-section variants with deletion lists (R4).
- Eval 1 (new CI protocol) ties 9/11, with different misses. The new skill's draft kept the core small with one capability and fallback, but its reconnect grace is SHOULD-only and a job lost in transit holds a slot forever. v1's draft has a sound lease but no capability/fallback split. Candidate principle: every piece of state one side holds for the other needs an end both sides can observe.
- Evals 2 and 3 are non-discriminating: eval 2 is contaminated (v1 already contains the pin example added after iteration 1); eval 3 needs harder planted flaws.
- Tooling: spec_check.py accepted trailing commas, so it missed the invalid JSON planted in the Lantern example; fixed in this iteration (apron's spec still passes 46/46).
