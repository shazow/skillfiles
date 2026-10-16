### 3.4 Uploading changes

This section describes how a client uploads changes to the server. It is
organized as follows: first we describe the `put` request, then the server's
reply, then error handling, and finally some examples. The key words "MUST",
"MUST NOT", "SHOULD", and "MAY" in this section are to be interpreted as
described in BCP 14.

A client that has modified a file locally and wishes to propagate that
modification to the server (and thereby to the other devices that are
subscribed to the same folder) sends a `put` request. The `put` request
contains the `fileId` of the file, the `base_rev` which is the revision that
the client's modification was based on, and the new `content` of the file,
encoded as base64. It is important that the `base_rev` is the revision the
client last saw, because otherwise the server would not be able to detect
conflicts, and conflicts would be silently overwritten, which would lead to
data loss for users.

The server must check that `base_rev` matches the current revision of the
file. If it matches, the server stores the content, increments the revision,
and replies with the new revision in `rev`. If it does not match, the server
MUST reply with a `conflict` error. In the case of a conflict, the client
will then need to download the current version, merge it with its local
changes, and send a new `put` with the new `base_rev`. This means that a
client that is offline for a long time may experience many conflicts. Note
that the server MUST NOT store the content when there is a conflict, since
this would overwrite the other device's changes.

Unknown members in the `put` request MUST be ignored by the server. Unknown
members in the `put` reply MUST be ignored by the client. (This is the same
as the general rule in §1, but we repeat it here for clarity.)

When the server has stored the content, it sends a `changed` notification to
every other device that is subscribed to the folder. The `changed`
notification is sent before the reply to the `put` request is sent, so that
clients can rely on the ordering. (Previously the reply contained an `echo`
field that clients used to suppress their own `changed` notification; this
was removed in v4.) The `changed` notification contains the `file_id`, the
new `rev`, and a `pending` flag which is `true` while other devices are
still downloading the content and `false` once all devices have it.

Large files are a special case. If the content is larger than the server's
`max_put` limit (advertised in the `hello` frame), the server MUST reply with
a `too_large` error. Clients should split large files using the `chunked`
capability (see §4.3) if the server supports it. If the server does not
support `chunked`, clients cannot upload the file. Level 0 servers do not
support `chunked`.

Retries: if the connection drops before the reply arrives, the client may
retry the `put` with the same `id`. The server should deduplicate retries by
`id`, and should return the original reply. If the original `put` caused a
conflict, the retry also gets a conflict. If the original succeeded, the
retry gets the original `rev`, even if the file has changed since, and even
if the retry's `base_rev` no longer matches, and also when the content is
different.

Example:

```json
// -> client uploads
{"method": "put", "id": "p1", "params": {"fileId": "f_92", "base_rev": 7, "content": "aGVsbG8=",}}
// <- other devices are told
{"method": "changed", "params": {"file_id": "f_92", "rev": 8, "pending": true}}
// <- reply
{"id": "p1", "result": {"rev": 8}}
```
