### 4.5 `status`

Users have a status that others see next to their name.

**Fields.**

- `user.status` is one of `online`, `away`, `dnd`, `invisible`, or `offline`.
- `user.invisible` is a boolean. When it is `true`, the user appears offline
  to others.
- `user.dnd` is a boolean. When it is `true`, the server sends no push
  notifications to the user.
- `room.muted_by` is a list of `user_id`s on the room record. A user in the
  list gets no push notifications for that room.
- `connection.away` is set per connection, and is `true` after 5 minutes
  without input on that connection.

**Setting status.**

- Clients set `status` with the `status` request:
  `{"method": "status", "id": "s1", "params": {"status": "dnd"}}`.
- A client MAY also set `invisible` and `dnd` with `me`.
- Clients mute a room with the `status` request and `room_id`:
  `{"method": "status", "id": "s2", "params": {"mute": true, "room_id": "ops"}}`.
  The server adds the user to that room's `muted_by` and broadcasts the
  updated room record to the room's members.
- Setting `status` to `invisible` also sets `invisible: true`. Setting
  `invisible: false` with `me` sets `status` to `online`.
- Setting `status` to `dnd` also sets `dnd: true`, but setting `dnd: true`
  with `me` does not change `status`.

**Derived status.**

- The server derives the status that others see, in this order:
  1. `offline` if the user has no connections;
  2. `dnd` if `dnd` is `true`;
  3. `away` if every connection has `away: true`;
  4. otherwise `user.status`.
- The server sends `you` with the derived status to the user's own
  connections, and `user` notifications with the derived status to others.
- If `invisible` is `true`, the server MUST send `offline` to others, except
  that members of a room the user has posted in within the last hour see
  `away`.
- A user who is `dnd` and `invisible` appears `offline` to others, but the
  server still suppresses pushes.
- Muting a room while `dnd` is `true` has no effect until `dnd` is cleared.
- When a user's last connection closes, the server keeps `status`,
  `invisible`, and `dnd`, but clears every `away`.
- Clients SHOULD show `away` users as dimmed, `dnd` users with a red dot, and
  `invisible` users (to themselves only) with a hollow dot.
