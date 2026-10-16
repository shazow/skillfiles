# iteration-6: skill v3 + F1 + F5 + F6, eval 11 only

F6 adds two scenarios to the hurried-implementer pass: a malformed request,
and input sized past both ends of a realistic range that the designer
defines for the protocol. There are three new with-skill runs, and the
grader was calibrated to iterations 4 and 5.

| run | scenarios with a footgun (of 12) | data loss | silent divergence | assertions |
|---|---|---|---|---|
| 1 | 2 (10, 12) | 1 | 1 | 2/4 |
| 2 | 2 (11, 12) | 0 | 2 | 3/4 |
| 3 | 5 (3, 7, 10, 11, 12) | 2 | 3 | 1/4 |

| config | scenarios with a footgun, mean | data loss, mean | designer tokens | designer seconds |
|---|---|---|---|---|
| v3 + F1 + F5 + F6 | 3.0 | 1.0 | 167533 | 814 |
| v3 + F1 + F5 (iteration 5) | 3.0 | 0.67 | 141688 | 544 |
| v3 (iteration 4) | 5.0 | 3.0 | 118191 | 374 |
| no skill (iteration 4) | 3.0 | 0.33 | 68041 | 238 |

## Notes

- **F6 made no measurable difference.** The means match iteration 5, and
  three runs can't separate them. Two of the three runs reach two
  footguns, against one in iteration 5.
- **The passes saw the right inputs but misjudged what happened.**
  - Runs 2 and 3 sent a null field and an oversized body, saw a 400 and a
    413, and scored that as correct handling. They never followed the
    client's retry loop to the point where it stalls for good.
  - Run 1 sent an unknown `qty` field and a 2 MiB name, and scored them as
    fine or "out of range".
  - None of the passes caught a footgun that the counter later found.
- **Every run still stalls on oversized input, and two of the three also
  stall on a null field.** In each case, any non-200 response is retried
  unchanged, and the request holds everything the client has. Run 1 avoids
  the null case because it rejects one op at a time instead of the whole
  request.
- **"Ignore unknown keys" still loses data** (runs 1 and 3). The server
  acknowledges a write, then drops or never relays the field it didn't
  know.
- **Run 3 has extra losses.** Its client forgets an item whenever a reply
  says `deleted: true`, so an edit made during a sync is lost, which
  contradicts the spec's own Appendix A. It also lets syncs overlap.
- **Grader judgment calls:**
  - Run 1's store file truncated by a crash mid-write is not counted: it
    is app storage, and no earlier run was charged for it.
  - "Most edits win" is designed loss in runs 2 and 3.
- **Cost keeps rising.** The skill's design runs now take about 2.5× the
  tokens and 3.4× the time of no-skill runs.
