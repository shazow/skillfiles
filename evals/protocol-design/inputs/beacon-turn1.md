# Conversation so far

**User:** Can you review beacon-spec.md and propose cleanups? Labelled items
please, I'll answer by label.

**Assistant:** I read the whole spec. Five proposals:

1. **Merge the repeated unknown-keys rules.** §1 already says unknown keys in
   a frame are ignored. §2 and §3 repeat it for `set_name` and `report` as
   MUSTs. I'd delete both repeats and keep only the §1 rule.
2. **Add `battery_pct` to `report`.** Most devices are battery powered, and
   operators will want to see charge levels next to readings.
3. **State that `name` is settable.** I'd add a sentence to §2 saying that
   devices can change their `name` at any time with `set_name`.
4. **Add `device_count` to the `devices` result,** so tools can show a total
   without counting the array.
5. **Make `report` a request instead of a notification,** so a device learns
   when the collector rejects a reading (for example, a value out of range).

**User:** 1. Ok 2. Skip 3. If it's already clear that names are settable,
drop it 4. Skip for now, revisit when we add pagination 5. Pitch me
