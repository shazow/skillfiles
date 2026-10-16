# iteration-1: skill v1 vs no skill

| eval | with_skill | without_skill |
|---|---|---|
| eval-1-ci-runner-new-protocol | 11/11 | 5/11 |
| eval-2-apron-pinned-messages | 9/9 | 7/9 |
| eval-3-lantern-tighten-section | 12/12 | 12/12 |

| metric | with_skill | without_skill | delta |
|---|---|---|---|
| pass_rate | 1.00 | 0.74 | +0.26 |
| time_seconds | 254.50 | 162.97 | +91.5 |
| tokens | 116458.67 | 79503.33 | +36955 |

## Notes

- Eval 3 (tighten a bloated section) is non-discriminating: both configs pass 12/12. The skill's version is tighter (-60% vs -49% words) and drops the remaining rationale sentence and an un-keyworded pseudo-rule, but the assertions don't capture that. Needs harder planted flaws (restated general rules in disguise, unagreed additions, a removal that silently drops a requirement).
- Eval 1 (new CI protocol) shows the largest gap (11/11 vs 5/11): without the skill the draft used BCP 14 boilerplate, no up-front session example, a mandatory core with no capability/fallback split, both-sides-must-list extension negotiation, and no request/notification distinction.
- Eval 1 with-skill run built a throwaway simulation that found and fixed two spec bugs, but the grader found a real one it missed: the coordinator's reconnect grace period is not on the wire, so a resumed job can briefly run twice. The baseline sent 'grace' in its welcome. Candidate skill addition: any timeout both sides act on must be communicated, not chosen privately.
- Eval 2 (pinning brainstorm): with-skill adds prior art, costs of its own pick, and a single fixed scenario across options. The baseline caught a real spec conflict the skill run missed (a pin request changes a server field, contradicting 'server fields are read-only'). Candidate skill addition: re-check every new rule against the general rules you cite as safety arguments.
- Cost: the skill adds ~37k tokens and ~90s per run on average, mostly reading references (and in eval 1, building and running a prototype).
