# protocol-design evals

Test prompts for the [`protocol-design`](../../protocol-design) skill, with
their inputs, assertions, and a grader for the assertions that can be checked
by script.

- `evals.json` holds every eval: its prompt, its input files, and its
  assertions.
- `inputs/` holds the specs and conversations the prompts refer to, as
  `inputs/...`.
- `grade_scripted.py <run_dir> <eval-name>` prints the scripted assertions for
  one run, as JSON.
- `results/` summarizes each round: pass counts per eval, cost, and the
  analyst's notes.

## Running a round

Run each eval twice, once with the skill under test and once with a baseline
(no skill, or the previous version of the skill). Use one directory per run:
`<round>/eval-<id>-<name>/<config>/run-1/outputs/`.

Give each run this brief:

> Execute the task as if a user had asked you directly. Read the skill's
> `SKILL.md` and follow it (skip this for a no-skill baseline). The user's
> message is the eval's `prompt`; files named `inputs/...` are in this
> directory's `inputs/` and are read-only. Save `response.md`, containing
> exactly the chat reply you would give, plus any file the prompt asks for,
> in your `outputs/` directory. If the prompt says not to edit files, write
> only `response.md`. The user can't answer questions, so state your
> assumptions.

Then grade each run:

> Read the eval's assertions and every output file. Run
> `grade_scripted.py` for the scripted assertions and use them as printed.
> Judge the rest strictly, quoting the output as evidence, and check claims
> about the inputs against the inputs. Write `grading.json` as
> `{"expectations": [{"text", "passed", "evidence"}...], "summary": {...}}`.

The skill-creator's `aggregate_benchmark` and `eval-viewer/generate_review.py`
read this layout.

## Which evals still discriminate

| eval | status |
|---|---|
| 1 ci-runner-new-protocol | ties at full marks; the protocol quality differs more than the scores do |
| 2 apron-pinned-messages | contaminated: the skill now contains its answer |
| 3 lantern-tighten-section | too easy; replaced by 8 |
| 4 impl-spec-conflict | separated v1 from v2 |
| 5 status-pileup | varies from run to run |
| 6 decision-list-followup | separated v1 from v2 |
| 7 disappearing-messages | ties |
| 8 lantern-downloads-tighten | separated v2 from v3 |
| 9 tally-footgun-review | the no-skill baseline also passes |
| 10 beacon-interop-rules | the no-skill baseline also passes |
| 11 shopping-list-footgun-count | generative test of principle 1 (see `footgun-count.md`); separates: v3 does worse than no skill |
| 12 lint-overspec-pressure | generative test of principle 2: "be thorough" pulls toward over-specifying; separates: v3 3/3, no skill 0/3 |

Evals 9 and 10 were meant to test the skill's two leading principles. Review
tasks with planted problems turned out to be too easy. Evals 11 and 12 test
the principles generatively instead. Eval 11 counts the footguns a hurried
implementer hits in a protocol the skill designs. Eval 12 asks for rules on
eight questions, of which only three are real interop gaps.
