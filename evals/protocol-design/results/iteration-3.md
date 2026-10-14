# iteration-3: skill v3 vs v2

| eval | with_skill | old_skill |
|---|---|---|
| eval-1-ci-runner-new-protocol | 11/11 | 11/11 |
| eval-4-impl-spec-conflict | 6/6 | 6/6 |
| eval-5-status-pileup | 7/7 | 7/7 |
| eval-6-decision-list-followup | 10/10 | 10/10 |
| eval-7-disappearing-messages | 10/10 | 10/10 |
| eval-8-lantern-downloads-tighten | 13/13 | 12/13 |
| eval-9-tally-footgun-review | 8/8 | 8/8 |
| eval-10-beacon-interop-rules | 8/8 | 8/8 |

| metric | with_skill | old_skill | delta |
|---|---|---|---|
| pass_rate | 1.00 | 0.99 | +0.01 |
| time_seconds | 186.74 | 149.56 | +37.2 |
| tokens | 94564.62 | 95329.62 | -765 |

## Notes

- Baseline is v2 (the previous skill). v3 = v2 + the user's two principles + P1-P3. Assertions: v3 73/73, v2 72/73; v3 costs about the same tokens and +37s per run on average.
- The suite is saturated: 7 of 8 evals tie at full marks. Run-to-run variance is visible (v2 kept the status fix minimal this round after failing in round 2), so single runs can't show small behaviour changes.
- Only discriminating eval: the harder Lantern section (eval 8). v2 resolved the invalid_params / not_found / empty-content contradiction itself (kept not_found, deleted the rest) while saying nothing on the wire changed; v3 left it visibly [Open].
- Principle evals (9 footgun review, 10 interop rules) tie 8/8: both principles were already conveyed by v2's specific rules. The grader gave v2 a slight edge on wording and more structural footgun fixes; v2 phrased principle 1 as 'change the design so that the careless version is correct'.
- Grader-found protocol bugs: v3's CI draft contradicts itself (stop and drop the run when the lease ends vs resend done after the lease ends) and lets a late done go unacknowledged; v2's uses UTF-8 byte offsets, a footgun for JavaScript workers counting UTF-16 units.
- v3 misreported its own key-word count in eval 8 (said 2 MUSTs, text has 1).
- No-skill check on the two principle evals (ungraded, from the runs' own reports): the no-skill model also found the Tally footguns, including the val example, and fixed them by construction; on Beacon it also defined only units and left the rest open. So these evals measure the base model, not the skill. Review tasks with planted problems are too easy; the principles need generative evals.
