### 3.5 Downloading files

This section explains how a client downloads a file. We first describe the
`get` request, then the reply, then what happens in the error cases.

A client that wants the current content of a file sends a `get` request with
the `file_id` of the file. The client may also include `if_rev`, which is the
revision of the copy the client already holds; the client must only send
`if_rev` when it actually holds a copy of the file, since otherwise the
comparison would be meaningless. In v3 this request was called `fetch`; it
was renamed to `get` in v4 to match the HTTP vocabulary that most developers
know.

When the server receives a `get`, it looks up the file. If `if_rev` is
present and equal to the file's current revision, the server replies with
`{"rev": <current revision>, "unchanged": true}` and does not include the
content, which saves bandwidth for clients that already have the latest
version. Since the server always returns the whole content of the file and
never a delta against `if_rev`, clients don't need to keep any partial state
between downloads. The reply carries `rev`, the file's current revision, and
`content`, the file encoded as base64.

A client that receives a field it does not understand in a `get` reply
should simply skip over it and carry on.

Errors: if the `file_id` is unknown, the server replies with
`invalid_params`. If the `file_id` belongs to a file the user is not allowed
to see, the server replies with `invalid_params`. If the file's folder has
been deleted, the server replies with `invalid_params`. In all of these
cases the server MUST reply with `not_found`, so that the client can show a
helpful message. If the file does not exist, the server may also just return
an empty `content`.

Files larger than `max_get` (advertised in the `hello` frame) can't be sent
in one reply. The server MUST reply with `too_large` for those, and the
client then downloads the file in parts with the `chunked` capability
(§4.3). This is important because otherwise very large replies could exhaust
the memory of small clients like phones.

Example:

```jsonc
// -> client already holds revision 7
{"method": "get", "id": "g1", "params": {"file_id": "f_92", "if_rev": 7}}
// <- the file has changed since
{"id": "g1", "result": {"revision": 9, "content": "aGVsbG8gd29ybGQ="}}
```
