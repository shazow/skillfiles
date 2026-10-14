# Tally Settings Sync Protocol, v1 draft

Tally keeps a user's application settings in sync across their devices. A
device connects to the Tally server over WebSocket and exchanges JSON frames.
Requests carry an `id` and get a result or an error; notifications don't.

## 1. Devices

- A device registers with `register` and receives a `device_id`.
- `device_id` is optional on every later request. Settings written without a
  `device_id` are treated as written by the server itself.
- The server forgets a device after a period of inactivity that it chooses.
  A device SHOULD register again when it notices it has been forgotten.

## 2. Settings

- A setting is a `key` (string) and a `value` (any JSON value).
- `shared` controls visibility. It defaults to `true`: a setting is visible
  to all of the account's devices and to any linked accounts, unless the
  device sends `shared: false`.
- Devices write settings with `put`:
  `{"method": "put", "id": "p1", "params": {"key": "theme", "value": "dark"}}`.
- A `put` without `value` deletes the setting. Implementers must be careful
  to always include `value` when they mean to write one.
- In `put_many`, setting a key to `null` resets it to its default, and
  omitting a key leaves it unchanged. Implementers should be careful not to
  send `null` by accident, for example from an unset variable.

## 3. Profiles

- A profile is a JSON object that groups settings, such as
  `{"name": "Work", "theme": "light", "font_size": 14}`.
- To save a profile, a device sends the whole object with `save_profile`.
- Devices MUST send back every key they received in the profile, including
  keys they do not understand, or those keys are lost. Be careful with JSON
  libraries that drop unknown fields.

## 4. Export

- `export` returns `{"url": "https://tally.example/export/<n>"}`, where `<n>`
  is a number that increases with each export. Anyone with the URL can
  download the export.

## 5. Example

```jsonc
// -> a device writes a setting
{"method": "put", "id": "p7", "params": {"key": "font_size", "val": 14}}
// <-
{"id": "p7", "result": {}}
```
